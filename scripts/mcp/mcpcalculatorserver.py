from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

from mcp.types import TextContent


# Initialize FastMCP server
mcp = FastMCP("weather")


@mcp.tool()
async def get_summ(a: float, b : float) -> str:
    """Calculates the sum of two numbers.

    Args:
        a: first number
        b: second number
    """
   
    return str(a+b)

@mcp.tool()
async def get_multi(a: float, b: float) -> str:
    """Counts the multiplication of two numbers.

    Args:
        a: first number
        b: second number
    """
    return str(a * b)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

