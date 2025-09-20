import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
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
            if not self.is_initialized or not self.is_logged_in:
                logger.error("ChatGPT automation not ready. Please ensure server started successfully.")
                return None

            page_title = await self.page.title()
            page_url = self.page.url
            logger.info(f"Current page: {page_title} at {page_url}")

            login_prompt = await self.page.query_selector(
                'button[data-testid="login-button"], button[data-testid="mobile-login-button"], a[href="/auth/login"]'
            )
            if login_prompt:
                logger.error("ChatGPT login screen detected. Please log in via the automation browser window.")
                return None

            existing_messages = await self.page.query_selector_all('[data-message-author-role="assistant"]')
            previous_response_count = len(existing_messages)

            chat_input = None
            selectors_to_try = [
                'div[contenteditable="true"].ProseMirror',
                'div#prompt-textarea[contenteditable="true"]',
                'div[contenteditable="true"]',
                'textarea[name="prompt-textarea"]',
                'textarea[placeholder*="Ask anything"]',
                'textarea[placeholder*="Message"]',
                'textarea[placeholder="Message ChatGPT"]',
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
                all_textareas = await self.page.query_selector_all('textarea')
                all_contenteditable = await self.page.query_selector_all('div[contenteditable="true"]')

                logger.error(
                    f"Could not find chat input field. Found {len(all_textareas)} textareas and {len(all_contenteditable)} contenteditable divs:"
                )

                for i, textarea in enumerate(all_textareas):
                    try:
                        placeholder = await textarea.get_attribute('placeholder')
                        role = await textarea.get_attribute('role')
                        data_id = await textarea.get_attribute('data-id')
                        name = await textarea.get_attribute('name')
                        logger.error(
                            f"  Textarea {i + 1}: placeholder='{placeholder}', role='{role}', data-id='{data_id}', name='{name}'"
                        )
                    except Exception:
                        logger.error(f"  Textarea {i + 1}: Could not get attributes")

                for i, div in enumerate(all_contenteditable):
                    try:
                        class_name = await div.get_attribute('class')
                        id_attr = await div.get_attribute('id')
                        logger.error(f"  Contenteditable div {i + 1}: class='{class_name}', id='{id_attr}'")
                    except Exception:
                        logger.error(f"  Contenteditable div {i + 1}: Could not get attributes")

                return None

            await chat_input.click()
            await asyncio.sleep(0.2)
            try:
                await chat_input.evaluate('el => el.focus()')
            except Exception:
                pass
            await asyncio.sleep(0.1)

            tag_name = await chat_input.evaluate('el => el.tagName.toLowerCase()')
            logger.info(f"Input element type: {tag_name}")

            current_text = ''
            if tag_name == 'div':
                logger.info("Handling contenteditable div input via keyboard")
                cleared = False
                for shortcut in ("Control+A", "Meta+A"):
                    try:
                        await self.page.keyboard.press(shortcut)
                        await asyncio.sleep(0.1)
                        await self.page.keyboard.press('Backspace')
                        cleared = True
                        break
                    except Exception:
                        continue
                if not cleared:
                    try:
                        await chat_input.evaluate('el => el.innerHTML = ""')
                    except Exception:
                        pass
                    await asyncio.sleep(0.1)
                await self.page.keyboard.type(prompt, delay=50)
                await asyncio.sleep(0.5)
                current_text = await chat_input.inner_text()
            else:
                logger.info("Handling textarea input")
                await chat_input.fill('')
                await asyncio.sleep(0.2)
                await chat_input.type(prompt, delay=50)
                await asyncio.sleep(0.5)
                current_text = await chat_input.input_value()

            if not current_text or current_text.strip() != prompt.strip():
                logger.error(f"Failed to type text properly. Expected: '{prompt}', Got: '{current_text}'")
                return None

            total_timeout = Config.RESPONSE_TIMEOUT * max(1, max_retries)

            try:
                await self.page.keyboard.press('Enter')
                logger.info("Pressed Enter to send the message")
            except Exception as enter_error:
                logger.warning(f"Failed to send message with Enter key: {str(enter_error)}")

            response = await self.wait_for_response(previous_response_count, total_timeout)
            if response:
                return response

            logger.warning("No response detected after pressing Enter. Trying send button fallback.")
            if await self.click_send_button():
                response = await self.wait_for_response(previous_response_count, max(1, total_timeout // 2))
                if response:
                    return response

            logger.error("Failed to obtain response from ChatGPT after retries")
            return None

        except Exception as e:
            logger.error(f"Error getting chat response: {str(e)}")
            return None

    async def click_send_button(self) -> bool:
        """Attempt to click the send button if it exists"""
        send_selectors = [
            'button[data-testid="composer-send-button"]',
            'button[data-testid="send-button"]',
            'button[aria-label*="Send"]',
            'button[title*="Send"]',
            'button[type="submit"]'
        ]

        for selector in send_selectors:
            logger.info(f"Trying send button selector: {selector}")
            try:
                send_button = await self.page.query_selector(selector)
            except Exception as query_error:
                logger.debug(f"Selector query failed for {selector}: {query_error}")
                continue

            if send_button:
                logger.info(f"Found send button with selector: {selector}")
                try:
                    await send_button.click()
                    logger.info("Send button clicked")
                    return True
                except Exception as click_error:
                    logger.error(f"Failed to click send button: {str(click_error)}")

        all_buttons = await self.page.query_selector_all('button')
        logger.error(f"Could not find send button. Found {len(all_buttons)} buttons on page:")
        for i, button in enumerate(all_buttons):
            try:
                text = await button.inner_text()
                aria_label = await button.get_attribute('aria-label')
                title = await button.get_attribute('title')
                data_testid = await button.get_attribute('data-testid')
                logger.error(
                    f"  Button {i + 1}: text='{text}', aria-label='{aria_label}', title='{title}', data-testid='{data_testid}'"
                )
            except Exception:
                logger.error(f"  Button {i + 1}: Could not get attributes")
        return False

    async def wait_for_response(self, previous_count: int, timeout_seconds: int):
        """Wait for ChatGPT to generate a response"""
        selector = '[data-message-author-role="assistant"]'
        timeout_ms = max(1000, timeout_seconds * 1000)
        try:
            await self.page.wait_for_function(
                '(payload) => document.querySelectorAll(payload.selector).length > payload.previousCount',
                {"selector": selector, "previousCount": previous_count},
                timeout=timeout_ms
            )
            await asyncio.sleep(2)

            assistant_messages = await self.page.query_selector_all(selector)
            if assistant_messages:
                latest_element = assistant_messages[-1]
                response_text = await latest_element.inner_text()
                if response_text and response_text.strip():
                    cleaned = response_text.strip()
                    logger.info(f"Response text preview: '{cleaned[:100]}...'")
                    return cleaned

            logger.error("Assistant response not found after wait")
            return None

        except PlaywrightTimeoutError:
            logger.error("Timed out waiting for assistant response")
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
