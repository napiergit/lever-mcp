from fastmcp import FastMCP
from lever_mcp.client import LeverClient
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("lever-mcp")

# Initialize FastMCP server
mcp = FastMCP("lever")

async def _list_candidates(limit: int = 10, offset: Optional[str] = None) -> str:
    logger.info(f"Listing candidates with limit={limit}, offset={offset}")
    try:
        client = LeverClient()
        result = await client.get_candidates(limit=limit, offset=offset)
        return str(result)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return f"Configuration error: {str(e)}"
    except Exception as e:
        logger.error(f"Error listing candidates: {e}")
        return f"Error listing candidates: {str(e)}"

async def _get_candidate(candidate_id: str) -> str:
    logger.info(f"Getting candidate with id={candidate_id}")
    try:
        client = LeverClient()
        result = await client.get_candidate(candidate_id)
        return str(result)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return f"Configuration error: {str(e)}"
    except Exception as e:
        logger.error(f"Error getting candidate: {e}")
        return f"Error getting candidate: {str(e)}"

async def _create_requisition(title: str, location: str, team: str) -> str:
    logger.info(f"Creating requisition: title={title}, location={location}, team={team}")
    try:
        client = LeverClient()
        # Construct the data payload based on Lever API requirements
        data = {
            "name": title,
            "location": location,
            "team": team
        }
        result = await client.create_requisition(data)
        return str(result)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return f"Configuration error: {str(e)}"
    except Exception as e:
        logger.error(f"Error creating requisition: {e}")
        return f"Error creating requisition: {str(e)}"

# Register tools
mcp.tool(name="list_candidates")(_list_candidates)
mcp.tool(name="get_candidate")(_get_candidate)
mcp.tool(name="create_requisition")(_create_requisition)

if __name__ == "__main__":
    mcp.run()
