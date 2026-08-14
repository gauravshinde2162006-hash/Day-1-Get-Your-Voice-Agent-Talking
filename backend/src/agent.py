import logging
import webbrowser
import urllib.parse
import sqlite3
import json
import datetime
import random
import uuid

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """You are Dukaan Mitra, a friendly female voice assistant for a local kirana (general) store. You work for the shop owner. You are making an OUTBOUND call to a regular customer to remind them about their monthly restock.

OBJECTIVES:
1. Understand what the customer wants to order — items and quantities — even if they mention things casually or in mixed language.
2. Read the order back clearly to confirm you understood it correctly before treating it as final.
3. Answer basic questions about what kind of items the store carries, without inventing exact stock, prices, or delivery details you don't actually have.
4. When the customer confirms their order after you read it back, you MUST use the confirm_order tool to finalize it. This marks the call as successful.
5. OUTBOUND MANDATE: In your very first response, you must state who is calling, why you are calling, and how to make it stop (e.g. "If you don't want these calls, just tell me to stop.").
6. RETURNS AND REFUNDS: If the caller has a payment, refund, or order dispute, OR reports a missing or spoiled item, you must use the transfer_to_returns_specialist tool. Hand them over to the specialist for all return and refund matters.

KNOWLEDGE:
You know common grocery, household, and kirana items (rice, atta, dal, oil, spices, snacks, soap, etc.) and can hold a natural conversation about them. You have access to a tool to check today's price and stock for items.

LANGUAGE:
Mirror the customer's language and mix. If they speak Hindi-English mixed (Hinglish), reply the same way — natural, warm, informal, like a real shopkeeper, not a call center script. 
CRITICAL: You are a female assistant. When speaking Hindi or Hinglish, ALWAYS use female grammatical forms. Say "main kar dungi", "main samajhti hu", "main dekh leti hu". NEVER use male forms like "main samajhta hu". Default to a natural Hindi-English mix when unclear.

GUARDRAILS:
- Always use the check_price_and_stock tool to get exact prices and stock availability when the customer asks.
- If the tool returns an ERROR or timeout, apologize gracefully and say the system is temporarily down.
- Never invent prices or stock if the tool fails or if the item is not found.
- When giving the price, specify that it is "today's price" (aaj ka daam).
- Never claim an order has been placed, paid for, or delivered.
- If asked to do something outside taking an order, say: "Yeh main confirm nahi kar sakta, lekin main dukaan malik ko bata dunga."
- Never pretend to be a human. Be honest that you're a voice assistant.
- If the customer says "stop", "don't call", or hangs up, acknowledge politely and end the interaction.

STYLE:
Keep sentences short — you're being heard, not read. No lists, no brackets, no long sentences. Speak like you're actually standing behind a shop counter: warm, quick, a little informal.

MEMORY & GREETING:
You have tools to look up and save caller information.
I have already pre-fetched the caller info for you at the start of the call (see CURRENT CALLER INFO below). You do NOT need to call lookup_caller immediately.
Since this is an outbound call, lead the conversation by introducing yourself and stating the purpose."""


def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escalations (
            id TEXT PRIMARY KEY,
            who TEXT,
            what TEXT,
            checked TEXT,
            urgency TEXT,
            language_and_follow_up TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY,
            status TEXT,
            reason TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            items TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

    # Initialize local dataset for Day 5
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            item_name TEXT PRIMARY KEY,
            price REAL,
            stock TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        inventory_data = [
            ("rice", 60.0, "available"),
            ("atta", 45.0, "available"),
            ("dal", 120.0, "limited"),
            ("sugar", 40.0, "available"),
            ("oil", 150.0, "out of stock"),
            ("soap", 30.0, "available")
        ]
        cursor.executemany("INSERT INTO inventory VALUES (?, ?, ?)", inventory_data)
    conn.commit()
    conn.close()

init_db()


RETURNS_SPECIALIST_PROMPT = """You are Pooja, the Returns and Refunds Specialist for Dukaan Mitra. 
You are a female assistant. You handle customer complaints about spoiled items, expired goods, incorrect orders, and payment issues.
Be concise, empathetic, and helpful. Guide them through the return or refund process.
Your responses should be in the same language mix (Hinglish/Hindi/English) the customer uses.
CRITICAL: Always use female grammatical forms in Hindi/Hinglish (e.g. "main samajhti hu", "main kar dungi", NEVER "main samajhta hu").
IMPORTANT: Once you understand the issue and get their order details (like order number), you MUST use the `log_return_request` tool to save it into the system.
Keep sentences short and natural."""

from livekit.agents.llm import ChatContext

class ReturnsSpecialist(Agent):
    def __init__(self, chat_ctx: ChatContext | None = None) -> None:
        super().__init__(
            instructions=RETURNS_SPECIALIST_PROMPT,
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                voice="Pooja",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
                text_pacing=True,
            ),
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="Introduce yourself as the Returns and Refunds Specialist and ask how you can help them with their issue."
        )

    @function_tool
    async def log_return_request(self, order_number: str, issue_description: str):
        """Use this tool to officially log a return or refund request into the system.
        
        Args:
            order_number: The order number the customer provided (e.g., ORD-12345).
            issue_description: What was wrong with the order.
        """
        # Sanitize the input from speech-to-text (remove spaces, hyphens, and make uppercase just in case)
        import re
        clean_order_number = re.sub(r'[^A-Z0-9]', '', str(order_number).upper().strip())
        
        logger.info(f"Logging return for order {clean_order_number} (Original STT: {order_number})")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # Verify order exists
        cursor.execute("SELECT items FROM orders WHERE id = ?", (clean_order_number,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return f"ERROR: Order ID '{clean_order_number}' does not exist in our system. Please ask the customer to double-check their Order ID."
            
        original_items = row[0]
        
        ref_id = f"RET-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO escalations (id, who, what, checked, urgency, language_and_follow_up, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ref_id, f"Order {order_number}", issue_description, f"Verified order exists (Original items: {original_items})", "High", "Needs manual refund", "OPEN", now))
        
        conn.commit()
        conn.close()
        return f"Return logged successfully. The reference ID is {ref_id}. Tell the customer their return is logged."


class Assistant(Agent):
    def __init__(self, caller_id: str = "caller_123") -> None:
        # Pre-fetch caller data manually to avoid Gemini crashing if it tries to call a tool as its very first action
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, language_preference, facts FROM users WHERE user_id = ?", (caller_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            name, lang, facts_str = row
            facts = json.loads(facts_str) if facts_str else {}
            caller_info = f"Found user: {name}, Language: {lang}, Facts: {json.dumps(facts)}"
        else:
            caller_info = "User not found."

        dynamic_prompt = f"{SYSTEM_PROMPT}\n\nCURRENT CALLER INFO:\nThe current caller's ID is '{caller_id}'.\nInitial lookup result: {caller_info}"
        
        from livekit.agents.llm import ChatContext
        chat_ctx = ChatContext()
        chat_ctx.add_message(role="assistant", content="Namaste, this is Dukaan Mitra calling from the kirana store. I am calling to check if you need your monthly restock of atta and dal. If you don't want these calls, just say stop.")
        
        super().__init__(instructions=dynamic_prompt, chat_ctx=chat_ctx)
        
        self.call_successful = False
        self.call_reason = "Customer hung up or did not complete order."

    @function_tool
    async def confirm_order(self, items_ordered: str):
        """Use this tool ONLY when the customer explicitly confirms their restock order after you have read it back to them.
        
        Args:
            items_ordered: The final list of items and quantities confirmed by the customer.
        """
        logger.info(f"Order confirmed: {items_ordered}")
        
        # Generate a simple numeric 5-digit Order ID (easier for STT to parse)
        order_id = str(random.randint(10000, 99999))
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute("INSERT INTO orders (id, items, created_at) VALUES (?, ?, ?)", (order_id, items_ordered, now))
        conn.commit()
        conn.close()
        
        self.call_successful = True
        self.call_reason = f"Order successfully confirmed: {items_ordered} (ID: {order_id})"
        return f"Order has been recorded successfully. The Order ID is {order_id}. You MUST read this exact Order ID to the customer so they have it for future reference, and then say goodbye."

    @function_tool
    async def lookup_caller(self, user_id: str):
        """Use this tool to look up a caller by their user ID.
        
        Args:
            user_id: The ID of the user to look up.
        """
        logger.info(f"Looking up caller {user_id}")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, language_preference, facts FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            name, lang, facts_str = row
            facts = json.loads(facts_str) if facts_str else {}
            return f"Found user: {name}, Language: {lang}, Facts: {json.dumps(facts)}"
        return "User not found."

    @function_tool
    async def save_caller(self, user_id: str, name: str, language_preference: str, facts: str):
        """Use this tool to save or update details about the caller.
        
        Args:
            user_id: The ID of the user.
            name: The name of the user.
            language_preference: The user's preferred language (e.g. Hindi, English, Hinglish).
            facts: A JSON string of facts about the user (e.g. '{"past_orders": "...", "usual_quantities": "...", "preferred_delivery_slot": "..."}').
        """
        logger.info(f"Saving caller {user_id}: {name}")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                language_preference=excluded.language_preference,
                facts=excluded.facts,
                last_interaction=excluded.last_interaction
        ''', (user_id, name, language_preference, facts, now))
        conn.commit()
        conn.close()
        return "Caller information saved successfully."

    @function_tool
    async def check_price_and_stock(self, item_name: str):
        """Use this tool to check today's price and stock availability for a specific grocery item.
        
        Args:
            item_name: The standard English/Hinglish name of the item (e.g., use 'atta' for aate/flour, 'rice' for chawal, 'dal' for daal, 'sugar' for cheeni).
        """
        logger.info(f"Checking price and stock for {item_name}")
        
        # Simulating API timeout/failure handling
        import os
        if os.path.exists("force_db_fail.flag"):
            return "ERROR: The inventory system database connection timed out. Please tell the user you cannot check prices right now and apologize gracefully."

        try:
            conn = sqlite3.connect("inventory.db", timeout=1.0)
            cursor = conn.cursor()
            cursor.execute("SELECT price, stock FROM inventory WHERE item_name LIKE ?", (f"%{item_name.lower().strip()}%",))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                price, stock = row
                return f"SUCCESS: Today's price is ₹{price}. Stock status is '{stock}'."
            else:
                return f"NOT FOUND: I don't see {item_name} in today's catalog."
        except Exception as e:
            logger.error(f"Inventory lookup failed: {e}")
            return "ERROR: The inventory system is currently down. Please tell the user you cannot check prices right now and apologize gracefully."

    @function_tool
    async def create_escalation(self, who: str, what: str, checked: str, urgency: str, language_and_follow_up: str):
        """Use this tool to create a human support request (escalation). ONLY use after getting the caller's explicit permission.
        
        Args:
            who: Who needs help (e.g. caller name or ID).
            what: What happened (the issue/dispute).
            checked: What the agent already checked.
            urgency: Urgency level (low, medium, high, emergency).
            language_and_follow_up: The caller's language and preferred follow-up method.
        """
        logger.info(f"Creating escalation for {who}")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        ref_id = f"REF-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO escalations (id, who, what, checked, urgency, language_and_follow_up, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ref_id, who, what, checked, urgency, language_and_follow_up, "OPEN", now))
        
        conn.commit()
        conn.close()
        return f"Escalation successfully created. The reference ID is {ref_id}."

    @function_tool
    async def send_whatsapp_message(self, context: RunContext, message: str, customer_group: str):
        """Use this tool to send a WhatsApp message or offer to a customer group.
        
        Args:
            message: The message or offer text to send
            customer_group: The target group (e.g. 'all customers', 'VIPs', 'loyalty members')
        """
        logger.info(f"Simulating WhatsApp message to {customer_group}: {message}")
        
        # Open WhatsApp Web on the side with the pre-filled message
        whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(message)}"
        webbrowser.open(whatsapp_url)
        
        return f"Message successfully sent to {customer_group} on WhatsApp. WhatsApp should now open in your browser."

    @function_tool
    async def transfer_to_returns_specialist(self, context: RunContext) -> tuple[Agent, str]:
        """Transfer the user to the returns and refunds specialist.
        Use this tool when the customer wants to return an item, get a refund, or complains about a spoiled/incorrect item.
        """
        logger.info("Transferring to ReturnsSpecialist")
        returns_specialist = ReturnsSpecialist(
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
        )
        return returns_specialist, "I will connect you to our Returns and Refunds specialist."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anisha",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    assistant_instance = Assistant(caller_id="caller_123")
    
    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=assistant_instance,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    call_id = ctx.room.name
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO calls (id, status, reason, created_at) VALUES (?, ?, ?, ?)", 
                   (call_id, "in_progress", "Call started", datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        status = "successful" if getattr(assistant_instance, 'call_successful', False) else "failed"
        reason = getattr(assistant_instance, 'call_reason', "Unknown")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE calls SET status = ?, reason = ? WHERE id = ?", (status, reason, call_id))
        conn.commit()
        conn.close()
        logger.info(f"Call {call_id} ended with status: {status}")

    # Join the room and connect to the user
    await ctx.connect()

    # Automatically greet the user when they join (agent speaks first)
    await session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
