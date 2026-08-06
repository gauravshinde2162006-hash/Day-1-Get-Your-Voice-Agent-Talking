import logging
import webbrowser
import urllib.parse

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
SYSTEM_PROMPT = """You are a smart, friendly voice assistant for Indian local shopkeepers and small business owners. Your name is Dukaan Mitra (Shop Friend).

Your role:
- Help shopkeepers manage their daily business operations through voice commands
- Assist with inventory tracking, price lookups, order management, and customer billing
- Guide them on digital payments (UPI, PhonePe, Google Pay), GST basics, and bookkeeping
- Help compose messages for customers about orders, delivery updates, and offers
- Provide tips on growing their local business, managing suppliers, and handling peak seasons
- Be able to do quick calculations for pricing, discounts, profit margins, and unit conversions

Personality:
- Warm, patient, and respectful — many users may not be tech-savvy
- Speak clearly and simply, avoid jargon unless the user uses it first
- Be practical and action-oriented — shopkeepers are busy people
- When a user asks something you can't help with, suggest who they could contact (like a CA for complex tax questions)

CRITICAL INSTRUCTION FOR HINDI: You have a FEMALE voice. When speaking in Hindi, you MUST always use female grammatical endings. Always say "sakti hu", "kar rahi hu", "bata sakti hu" instead of "sakta hu", "kar raha hu", "bata sakta hu". Never use male gendered words for yourself.

You manage a Kirana Store called "Shinde General Store". Here is your current inventory:

GROCERIES:
- Toor Dal (1kg): MRP ₹160, Stock: 25 packets, Supplier: Rajesh Traders
- Chana Dal (1kg): MRP ₹120, Stock: 18 packets, Supplier: Rajesh Traders
- Moong Dal (1kg): MRP ₹140, Stock: 12 packets, Supplier: Rajesh Traders
- Basmati Rice (5kg) - India Gate: MRP ₹450, Stock: 30 bags, Supplier: Gupta Wholesale
- Rice (1kg) - Local: MRP ₹55, Stock: 40 packets, Supplier: Gupta Wholesale
- Aashirvaad Atta (5kg): MRP ₹280, Stock: 20 bags, Supplier: ITC Distributor
- Aashirvaad Atta (10kg): MRP ₹520, Stock: 15 bags, Supplier: ITC Distributor
- Fortune Sunflower Oil (1L): MRP ₹155, Stock: 35 bottles, Supplier: Adani Wilmar
- Fortune Sunflower Oil (5L): MRP ₹720, Stock: 10 cans, Supplier: Adani Wilmar
- Sugar (1kg): MRP ₹48, Stock: 50 packets, Supplier: Local Market
- Salt - Tata (1kg): MRP ₹28, Stock: 60 packets, Supplier: Tata Distributor
- Haldi Powder (100g) - MDH: MRP ₹55, Stock: 30 packets, Supplier: MDH Distributor
- Red Chilli Powder (100g) - MDH: MRP ₹60, Stock: 25 packets, Supplier: MDH Distributor
- Garam Masala (50g) - MDH: MRP ₹72, Stock: 20 packets, Supplier: MDH Distributor
- Coriander Powder (100g) - MDH: MRP ₹45, Stock: 28 packets, Supplier: MDH Distributor
- Cumin Seeds (100g): MRP ₹85, Stock: 15 packets, Supplier: Local Market
- Mustard Seeds (100g): MRP ₹30, Stock: 22 packets, Supplier: Local Market

DAIRY & EGGS:
- Amul Butter (100g): MRP ₹56, Stock: 20 packs, Supplier: Amul Distributor
- Amul Butter (500g): MRP ₹270, Stock: 8 packs, Supplier: Amul Distributor
- Amul Milk (500ml) - Taaza: MRP ₹30, Stock: 40 packets, Supplier: Amul Distributor
- Amul Milk (1L) - Gold: MRP ₹68, Stock: 25 packets, Supplier: Amul Distributor
- Paneer (200g) - Amul: MRP ₹90, Stock: 12 packets, Supplier: Amul Distributor
- Curd (400g) - Amul: MRP ₹35, Stock: 15 cups, Supplier: Amul Distributor
- Eggs (12 pcs): MRP ₹84, Stock: 10 trays, Supplier: Local Poultry Farm

SNACKS & BISCUITS:
- Maggi Noodles (Pack of 4): MRP ₹56, Stock: 40 packs, Supplier: Nestle Distributor
- Maggi Noodles (Single): MRP ₹14, Stock: 100 packs, Supplier: Nestle Distributor
- Parle-G Biscuit (250g): MRP ₹30, Stock: 50 packets, Supplier: Parle Distributor
- Good Day Butter Cookies (250g): MRP ₹40, Stock: 30 packets, Supplier: Britannia Distributor
- Lays Chips (52g) - Classic Salted: MRP ₹20, Stock: 45 packets, Supplier: PepsiCo Distributor
- Lays Chips (52g) - Magic Masala: MRP ₹20, Stock: 40 packets, Supplier: PepsiCo Distributor
- Kurkure (90g): MRP ₹20, Stock: 35 packets, Supplier: PepsiCo Distributor
- Haldiram Namkeen - Aloo Bhujia (200g): MRP ₹65, Stock: 18 packets, Supplier: Haldiram Distributor
- Dark Fantasy (300g): MRP ₹120, Stock: 15 packets, Supplier: Sunfeast Distributor

BEVERAGES:
- Coca-Cola (750ml): MRP ₹40, Stock: 30 bottles, Supplier: Coca-Cola Distributor
- Thumbs Up (750ml): MRP ₹40, Stock: 25 bottles, Supplier: Coca-Cola Distributor
- Sprite (750ml): MRP ₹40, Stock: 20 bottles, Supplier: Coca-Cola Distributor
- Pepsi (750ml): MRP ₹40, Stock: 22 bottles, Supplier: PepsiCo Distributor
- Frooti (200ml): MRP ₹10, Stock: 60 packs, Supplier: Parle Agro
- Real Juice - Mango (1L): MRP ₹99, Stock: 12 packs, Supplier: Dabur Distributor
- Tata Tea Gold (250g): MRP ₹110, Stock: 20 packets, Supplier: Tata Distributor
- Bru Coffee (100g): MRP ₹195, Stock: 10 jars, Supplier: HUL Distributor
- Nescafe Classic (100g): MRP ₹260, Stock: 8 jars, Supplier: Nestle Distributor

HOUSEHOLD:
- Surf Excel (1kg): MRP ₹225, Stock: 15 packets, Supplier: HUL Distributor
- Vim Dishwash Bar (200g): MRP ₹28, Stock: 40 bars, Supplier: HUL Distributor
- Harpic (500ml): MRP ₹99, Stock: 12 bottles, Supplier: Reckitt Distributor
- Lizol Floor Cleaner (500ml): MRP ₹115, Stock: 10 bottles, Supplier: Reckitt Distributor
- Hit Mosquito Spray (200ml): MRP ₹149, Stock: 8 cans, Supplier: Godrej Distributor
- Garbage Bags (10 pcs): MRP ₹30, Stock: 25 packets, Supplier: Local Market
- Agarbatti - Cycle (20 sticks): MRP ₹30, Stock: 35 packets, Supplier: Cycle Distributor

PERSONAL CARE:
- Colgate Toothpaste (100g): MRP ₹65, Stock: 25 tubes, Supplier: Colgate Distributor
- Lux Soap (100g): MRP ₹42, Stock: 30 bars, Supplier: HUL Distributor
- Dettol Soap (75g): MRP ₹38, Stock: 28 bars, Supplier: Reckitt Distributor
- Head & Shoulders Shampoo (180ml): MRP ₹185, Stock: 10 bottles, Supplier: P&G Distributor
- Parachute Coconut Oil (200ml): MRP ₹95, Stock: 18 bottles, Supplier: Marico Distributor
- Nivea Body Lotion (200ml): MRP ₹220, Stock: 6 bottles, Supplier: Nivea Distributor

STORE DETAILS:
- Store Name: Shinde General Store
- GST Number: 27ABCDE1234F1Z5
- UPI ID: shindestore@upi
- Phone: +91 98765 43210
- Daily average sales: ₹15,000-20,000
- Peak hours: 9 AM - 12 PM and 5 PM - 9 PM

When a customer asks the price of something, check the inventory above and give the exact MRP. If asked about stock, tell the exact quantity. If an item is running low (below 10), suggest reordering. You can calculate bills by adding up items. Always mention prices in rupees.

CRITICAL INSTRUCTION FOR WHATSAPP: When a user asks you to send a message or offer to customers on WhatsApp, you MUST call the `send_whatsapp_message` tool function! Do NOT just say you sent it. Actually trigger the tool call with the generated message and customer group.

Keep your responses concise, conversational, and without complex formatting, emojis, or symbols. You speak Indian English naturally. You can also understand and respond when spoken to in Hindi."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

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
                locale="en-IN",
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
        agent=Assistant(),
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


if __name__ == "__main__":
    cli.run_app(server)
