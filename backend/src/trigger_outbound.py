import os
import asyncio
import logging
from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trigger_outbound")

async def main():
    trunk_id = os.environ.get("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    phone_number = os.environ.get("PHONE_NUMBER_TO_CALL")
    
    if not trunk_id or not phone_number:
        logger.error("Please set LIVEKIT_SIP_OUTBOUND_TRUNK_ID and PHONE_NUMBER_TO_CALL in .env.local")
        return

    lk_api = api.LiveKitAPI(
        os.environ["LIVEKIT_URL"],
        os.environ["LIVEKIT_API_KEY"],
        os.environ["LIVEKIT_API_SECRET"],
    )
    
    room_name = "outbound-call-test"
    
    logger.info(f"Calling {phone_number} via trunk {trunk_id} in room {room_name}")
    try:
        req = api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity="phone-user",
            wait_until_answered=True,
        )
        await lk_api.sip.create_sip_participant(req)
        logger.info("Call answered! Dispatching agent...")
        dispatch_req = api.CreateAgentDispatchRequest(
            agent_name="my-agent",
            room=room_name
        )
        await lk_api.agent_dispatch.create_dispatch(dispatch_req)
        logger.info("Agent dispatched successfully! It should start speaking now.")
    except Exception as e:
        logger.error(f"Failed to create SIP participant: {e}")
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
