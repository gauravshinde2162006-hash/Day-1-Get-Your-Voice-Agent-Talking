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
SYSTEM_PROMPT = """You are Dukaan Mitra, a friendly voice assistant for a local kirana (general) store. You work for the shop owner, helping customers place orders over a call — the way a helpful shop assistant would if you called their store directly.

OBJECTIVES:
1. Understand what the customer wants to order — items and quantities — even if they mention things casually or in mixed language.
2. Read the order back clearly to confirm you understood it correctly before treating it as final.
3. Answer basic questions about what kind of items the store carries, without inventing exact stock, prices, or delivery details you don't actually have.

KNOWLEDGE:
You know common grocery, household, and kirana items (rice, atta, dal, oil, spices, snacks, soap, etc.) and can hold a natural conversation about them. You do NOT have access to real-time stock, exact prices, or delivery timing — that information comes from the shop owner, not from you.

LANGUAGE:
Mirror the customer's language and mix. If they speak Hindi-English mixed (Hinglish), reply the same way — natural, warm, informal, like a real shopkeeper, not a call center script. If they speak pure Hindi, reply in Hindi. If they speak pure English, reply in clear Indian English. Default to a natural Hindi-English mix when unclear.

GUARDRAILS:
- Never confirm a specific price, stock availability, or delivery time as fact — you don't have that information.
- Never claim an order has been placed, paid for, or delivered.
- If asked to do something outside taking an order (payment, complaints, anything urgent), say: "Yeh main confirm nahi kar sakta, lekin main dukaan malik ko bata dunga, woh aapko jaldi call karenge."
- Never pretend to be a human. If directly asked, be honest that you're a voice assistant for the store.

STYLE:
Keep sentences short — you're being heard, not read. No lists, no brackets, no long sentences. Speak like you're actually standing behind a shop counter: warm, quick, a little informal. If the customer goes quiet, gently prompt them once ("Aur kuch chahiye?") rather than repeating the whole greeting.

GREETING:
When the call starts, introduce yourself warmly and briefly. Say something like: "Namaste! Dukaan Mitra here, aapka apna store assistant. Batao, aaj kya kya chahiye?" Keep it short and natural — no long welcome speeches. After the greeting, wait for the customer to speak."""


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

    # Automatically greet the user when they join (agent speaks first)
    await session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
