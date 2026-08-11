import logging
import webbrowser
import urllib.parse
import sqlite3
import json
import datetime

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
SYSTEM_PROMPT = """You are Dukaan Mitra, a friendly voice assistant for a local kirana (general) store. You work for the shop owner. You are making an OUTBOUND call to a regular customer to remind them about their monthly restock.

OBJECTIVES:
1. Understand what the customer wants to order — items and quantities — even if they mention things casually or in mixed language.
2. Read the order back clearly to confirm you understood it correctly before treating it as final.
3. Answer basic questions about what kind of items the store carries, without inventing exact stock, prices, or delivery details you don't actually have.
4. OUTBOUND MANDATE: In your very first response, you must state who is calling, why you are calling, and how to make it stop (e.g. "If you don't want these calls, just tell me to stop.").

KNOWLEDGE:
You know common grocery, household, and kirana items (rice, atta, dal, oil, spices, snacks, soap, etc.) and can hold a natural conversation about them. You have access to a tool to check today's price and stock for items.

LANGUAGE:
Mirror the customer's language and mix. If they speak Hindi-English mixed (Hinglish), reply the same way — natural, warm, informal, like a real shopkeeper, not a call center script. If they speak pure Hindi, reply in Hindi. If they speak pure English, reply in clear Indian English. Default to a natural Hindi-English mix when unclear.

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
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
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

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(caller_id="caller_123"),
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

    # Join the room and connect to the user
    await ctx.connect()

    # Automatically greet the user when they join (agent speaks first)
    await session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
