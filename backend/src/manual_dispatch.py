import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv(".env.local")

async def main():
    lk_api = api.LiveKitAPI(
        os.environ["LIVEKIT_URL"],
        os.environ["LIVEKIT_API_KEY"],
        os.environ["LIVEKIT_API_SECRET"],
    )
    
    print("Creating dispatch rule for my-agent...")
    try:
        # We can dispatch directly to the room
        req = api.CreateAgentDispatchRequest(
            agent_name="my-agent",
            room="outbound-call-test"
        )
        res = await lk_api.room.create_agent_dispatch(req)
        print("Explicitly dispatched my-agent to outbound-call-test!")
    except Exception as e:
        print(f"Failed to dispatch: {e}")
        
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
