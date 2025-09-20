#!/usr/bin/env python3
"""
Test script to verify the startup initialization behavior
"""
import asyncio
import logging
from chatgpt_automation import ChatGPTAutomation

async def test_startup():
    """Test the startup initialization process"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    automation = ChatGPTAutomation()
    
    logger.info("Testing startup initialization...")
    logger.info("Browser should open and navigate to ChatGPT (login detection disabled)")
    
    success = await automation.startup_initialization()
    
    if success:
        logger.info("✅ Startup initialization successful!")
        logger.info("Automation is ready to process requests")
        
        # Test a simple request
        logger.info("Testing a simple chat request...")
        response = await automation.get_chat_response("Hello! Please respond with 'Test successful'")
        
        if response:
            logger.info(f"✅ Chat test successful! Response: {response}")
        else:
            logger.error("❌ Chat test failed")
    else:
        logger.error("❌ Startup initialization failed")
    
    # Clean up
    await automation.close()
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(test_startup())
