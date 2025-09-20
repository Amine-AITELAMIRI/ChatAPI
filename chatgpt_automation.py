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
        """Skip login detection for testing - just mark as logged in"""
        try:
            logger.info("Skipping login detection for testing purposes")
            logger.info("Browser opened and navigated to ChatGPT")
            logger.info("You can manually log in if needed, but automation will proceed")
            
            # Mark as logged in without checking
            self.is_logged_in = True
            logger.info("✅ Automation ready for testing (login detection disabled)")
            return True
            
        except Exception as e:
            logger.error(f"Error during login setup: {str(e)}")
            return False
    
    async def startup_initialization(self, max_retries: int = 3):
        """Initialize browser during server startup (login detection disabled)"""
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
                
                # Skip login detection - just mark as ready
                login_success = await self.login_if_needed()
                if not login_success:
                    logger.error(f"Failed to setup automation (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        logger.info("Retrying automation setup...")
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
            
            # Debug: Check page title and URL
            page_title = await self.page.title()
            page_url = self.page.url
            logger.info(f"Current page: {page_title} at {page_url}")
            
            # Try multiple selectors for the chat input
            chat_input = None
            selectors_to_try = [
                'textarea[placeholder*="Message"]',
                'textarea[placeholder="Message ChatGPT…"]',
                'textarea[data-id="root"]',
                'textarea[role="textbox"]',
                'textarea[aria-label*="Message"]',
                'textarea'
            ]
            
            for selector in selectors_to_try:
                logger.info(f"Trying selector: {selector}")
                chat_input = await self.page.query_selector(selector)
                if chat_input:
                    logger.info(f"Found chat input with selector: {selector}")
                    break
            
            if not chat_input:
                # Debug: List all textareas on the page
                all_textareas = await self.page.query_selector_all('textarea')
                logger.error(f"Could not find chat input field. Found {len(all_textareas)} textareas on page:")
                for i, textarea in enumerate(all_textareas):
                    try:
                        placeholder = await textarea.get_attribute('placeholder')
                        role = await textarea.get_attribute('role')
                        data_id = await textarea.get_attribute('data-id')
                        logger.error(f"  Textarea {i+1}: placeholder='{placeholder}', role='{role}', data-id='{data_id}'")
                    except:
                        logger.error(f"  Textarea {i+1}: Could not get attributes")
                return None
            
            # Clear any existing text and type the prompt
            await chat_input.click()
            await chat_input.fill('')
            await chat_input.type(prompt, delay=50)  # Type with small delay
            
            # Find and click the send button
            send_button = None
            send_selectors = [
                'button[data-testid="send-button"]',
                'button:has-text("Send")',
                'button[aria-label*="Send"]',
                'button[title*="Send"]',
                'button:has(svg)',
                'button[type="submit"]'
            ]
            
            for selector in send_selectors:
                logger.info(f"Trying send button selector: {selector}")
                send_button = await self.page.query_selector(selector)
                if send_button:
                    logger.info(f"Found send button with selector: {selector}")
                    break
            
            if not send_button:
                # Debug: List all buttons on the page
                all_buttons = await self.page.query_selector_all('button')
                logger.error(f"Could not find send button. Found {len(all_buttons)} buttons on page:")
                for i, button in enumerate(all_buttons):
                    try:
                        text = await button.inner_text()
                        aria_label = await button.get_attribute('aria-label')
                        title = await button.get_attribute('title')
                        data_testid = await button.get_attribute('data-testid')
                        logger.error(f"  Button {i+1}: text='{text}', aria-label='{aria_label}', title='{title}', data-testid='{data_testid}'")
                    except:
                        logger.error(f"  Button {i+1}: Could not get attributes")
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
