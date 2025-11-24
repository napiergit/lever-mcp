import asyncio
import os
from lever_mcp.client import LeverClient

async def main():
    try:
        print("Attempting to list candidates...")
        client = LeverClient()
        candidates = await client.get_candidates(limit=5)
        print(f"Successfully listed {len(candidates.get('data', []))} candidates")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
