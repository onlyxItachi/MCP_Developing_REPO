"""app — FastMCP instance + entry point. Tools are registered in Phase 4."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("perfdigest")


def main() -> None:
    """Run the perfdigest MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
