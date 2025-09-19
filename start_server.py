#!/usr/bin/env python3
"""
Startup script for the Custom ChatGPT API
"""
import asyncio
import logging
import sys
from main import app
import uvicorn
from config import Config

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chatgpt_api.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def main():
    """Main startup function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Custom ChatGPT API Server...")
    logger.info(f"Server will be available at: http://{Config.HOST}:{Config.PORT}")
    logger.info("API Documentation: http://localhost:8000/docs")
    
    try:
        # Start the server
        config = uvicorn.Config(
            app,
            host=Config.HOST,
            port=Config.PORT,
            log_level=Config.LOG_LEVEL.lower(),
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
