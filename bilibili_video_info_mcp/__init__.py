"""
Bilibili Video Info MCP Server
"""
import argparse
import signal
import sys
from .server import mcp


def _handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutting down gracefully...")
    sys.exit(0)


def main():
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    parser = argparse.ArgumentParser(description="Bilibili Video Info MCP Server")
    parser.add_argument('transport', nargs='?', default='stdio', choices=['stdio', 'sse', 'streamable-http'],
                        help='Transport type (stdio, sse, or streamable-http)')
    args = parser.parse_args()

    try:
        mcp.run(transport=args.transport)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
