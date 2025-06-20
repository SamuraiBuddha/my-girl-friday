#!/usr/bin/env python3
"""
My Girl Friday MCP Server entry point
Run with: python -m my_girl_friday
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from .server import main as server_main

# Load environment variables from .env file if it exists
env_path = Path.cwd() / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try parent directory
    parent_env = Path.cwd().parent / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG', '').lower() == 'true' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting My Girl Friday MCP Server...")
        asyncio.run(server_main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
