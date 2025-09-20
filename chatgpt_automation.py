import asyncio
import logging
from playwright.async_api import async_playwright
import time
import random
from config import Config

logger = logging.getLogger(__name__)

class ChatGPTAutomation:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.is_logged_in = False
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the browser and navigate to ChatGPT"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with configuration settings
            self.browser = await self.playwright.chromium.launch(
                headless=Config.HEADLESS_MODE,
                args=Config.get_browser_args()
            )
            
            # Create new page
            self.page = await self.browser.new_page()
            
            # Set user agent to avoid detection
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Navigate to ChatGPT
            await self.page.goto('https://chat.openai.com/', wait_until='networkidle')
            
            logger.info("Browser initialized and navigated to ChatGPT")
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            return False
    
    async def login_if_needed(self):
        """Check if we need to login and handle the login process"""
        try:
            # Check if we're already logged in by looking for the chat input
            chat_input = await self.page.query_selector('textarea[placeholder*="Message"]')
            
            if chat_input:
                self.is_logged_in = True
                logger.info("Already logged in to ChatGPT")
                return True
            
            # If not logged in, we need manual intervention
            logger.warning("=" * 60)
            logger.warning("LOGIN REQUIRED")
            logger.warning("=" * 60)
            logger.warning("Please log in to ChatGPT in the browser window that opened.")
            logger.warning("IMPORTANT: Do NOT close the browser window during login!")
            logger.warning("The automation will wait for you to complete the login process...")
            logger.warning("=" * 60)
            
            # Wait for user to log in manually
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    # Check if page is still accessible
                    await self.page.evaluate('() => document.title')
                    
                    # Check for login completion
                    chat_input = await self.page.query_selector('textarea[placeholder*="Message"]')
                    
                    if chat_input:
                        self.is_logged_in = True
                        logger.info("✅ Login detected! Ready to process requests.")
                        return True
                    
                    # Check if we're on a different page (might indicate login redirect)
                    current_url = self.page.url
                    if 'chat.openai.com' in current_url and 'auth' not in current_url:
                        # We're on the main chat page, check again for input
                        chat_input = await self.page.query_selector('textarea[placeholder*="Message"]')
                        if chat_input:
                            self.is_logged_in = True
                            logger.info("✅ Login detected! Ready to process requests.")
                            return True
                    
                    await asyncio.sleep(2)
                    
                except Exception as page_error:
                    logger.error(f"Browser page error during login wait: {str(page_error)}")
                    logger.error("Browser window may have been closed. Please restart the server.")
                    return False
            
            logger.error("Login timeout. Please try again.")
            return False
            
        except Exception as e:
            logger.error(f"Error during login check: {str(e)}")
            return False
    
    async def startup_initialization(self, max_retries: int = 3):
        """Initialize browser and handle login during server startup"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting ChatGPT automation initialization (attempt {attempt + 1}/{max_retries})...")
                
                # Initialize browser
                if not await self.initialize():
                    logger.error(f"Failed to initialize browser during startup (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        logger.info("Retrying browser initialization...")
                        await asyncio.sleep(5)
                        continue
                    return False
                
                # Handle login
                login_success = await self.login_if_needed()
                if not login_success:
                    logger.error(f"Failed to complete login during startup (attempt {attempt + 1})")
                    
                    # Check if browser was closed
                    try:
                        await self.page.evaluate('() => document.title')
                        logger.info("Browser still open, retrying login process...")
                    except:
                        logger.error("Browser window was closed during login!")
                        logger.error("Please keep the browser window open during the login process.")
                        logger.error("Restarting browser for retry...")
                        await self.close()  # Clean up before retry
                        await asyncio.sleep(5)
                        continue
                    
                    if attempt < max_retries - 1:
                        logger.info("Retrying login process...")
                        await self.close()  # Clean up before retry
                        await asyncio.sleep(5)
                        continue
                    return False
                
                logger.info("ChatGPT automation ready! Server can now accept requests.")
                return True
                
            except Exception as e:
                logger.error(f"Error during startup initialization (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info("Retrying initialization...")
                    await self.close()  # Clean up before retry
                    await asyncio.sleep(5)
                    continue
                return False
        
        logger.error("Failed to initialize ChatGPT automation after all retries")
        return False
    
    async def get_chat_response(self, prompt: str, max_retries: int = 3):
        """Get response from ChatGPT for the given prompt"""
        try:
            # Check if automation is ready
            if not self.is_initialized or not self.is_logged_in:
                logger.error("ChatGPT automation not ready. Please ensure server started successfully.")
                return None
            
            # Find the chat input
            chat_input = await self.page.query_selector('textarea[placeholder*="Message"]')
            if not chat_input:
                logger.error("Could not find chat input field")
                return None
            
            # Clear any existing text and type the prompt
            await chat_input.click()
            await chat_input.fill('')
            await chat_input.type(prompt, delay=50)  # Type with small delay
            
            # Find and click the send button
            send_button = await self.page.query_selector('button[data-testid="send-button"]')
            if not send_button:
                # Try alternative selector
                send_button = await self.page.query_selector('button:has-text("Send")')
            
            if not send_button:
                logger.error("Could not find send button")
                return None
            
            await send_button.click()
            logger.info("Prompt sent to ChatGPT")
            
            # Wait for response
            response = await self.wait_for_response(max_retries)
            return response
            
        except Exception as e:
            logger.error(f"Error getting chat response: {str(e)}")
            return None
    
    async def wait_for_response(self, max_retries: int = 3):
        """Wait for ChatGPT to generate a response"""
        try:
            # Wait for the response to start appearing
            await asyncio.sleep(2)
            
            # Look for the response in the chat
            for attempt in range(max_retries):
                try:
                    # Wait for response to appear
                    await self.page.wait_for_selector('[data-message-author-role="assistant"]', timeout=30000)
                    
                    # Get all assistant messages
                    assistant_messages = await self.page.query_selector_all('[data-message-author-role="assistant"]')
                    
                    if assistant_messages:
                        # Get the last (most recent) message
                        last_message = assistant_messages[-1]
                        
                        # Extract text content
                        response_text = await last_message.inner_text()
                        
                        if response_text and len(response_text.strip()) > 0:
                            logger.info("Successfully received response from ChatGPT")
                            return response_text.strip()
                    
                    # If no response yet, wait a bit more
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
            
            logger.error("Failed to get response after all retries")
            return None
            
        except Exception as e:
            logger.error(f"Error waiting for response: {str(e)}")
            return None
    
    async def is_browser_connected(self):
        """Check if browser is still connected and accessible"""
        try:
            if not self.page:
                return False
            await self.page.evaluate('() => document.title')
            return True
        except:
            return False
    
    async def close(self):
        """Close the browser and cleanup"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

# Global instance
chatgpt_automation = ChatGPTAutomation()
