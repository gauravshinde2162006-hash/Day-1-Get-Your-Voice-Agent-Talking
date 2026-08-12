import asyncio
from livekit import api

async def main():
    lk = api.LiveKitAPI('http://localhost', 'key', 'secret')
    print([a for a in dir(lk) if not a.startswith('_')])
    if hasattr(lk, 'agent_dispatch'):
        print([a for a in dir(lk.agent_dispatch) if not a.startswith('_')])
    await lk.aclose()

asyncio.run(main())
