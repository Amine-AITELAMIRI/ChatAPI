import os
from typing import Optional

class Config:
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ChatGPT configuration
    CHATGPT_URL: str = "https://chat.openai.com/"
    MAX_RETRIES: int = 3
    RESPONSE_TIMEOUT: int = 30  # seconds
    
    # Browser configuration
    HEADLESS_MODE: bool = False  # Set to False for debugging
    BROWSER_TIMEOUT: int = 30000  # milliseconds
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    
    @classmethod
    def get_browser_args(cls) -> list:
        """Get browser arguments for Raspberry Pi compatibility"""
        return [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-back-forward-cache',
            '--disable-ipc-flooding-protection'
        ]
