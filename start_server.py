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
from chatgpt_automation import chatgpt_automation

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
        # Initialize ChatGPT automation and handle login
        logger.info("Initializing ChatGPT automation...")
        logger.info("Browser will open - please log in to ChatGPT when prompted")
        
        initialization_success = await chatgpt_automation.startup_initialization()
        
        if not initialization_success:
            logger.error("Failed to initialize ChatGPT automation. Server cannot start.")
            logger.error("Please check your internet connection and try again.")
            sys.exit(1)
        
        logger.info("ChatGPT automation ready! Starting API server...")
        
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
        # Clean up browser
        await chatgpt_automation.close()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        # Clean up browser
        await chatgpt_automation.close()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
