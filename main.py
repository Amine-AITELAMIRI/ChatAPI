from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging
from chatgpt_automation import chatgpt_automation
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Custom ChatGPT API", version="1.0.0")

# Use the same automation instance as start_server.py

class ChatRequest(BaseModel):
    prompt: str
    max_retries: int = 3

class ChatResponse(BaseModel):
    response: str
    success: bool
    error_message: str = None

@app.get("/")
async def root():
    automation_ready = chatgpt_automation.is_initialized and chatgpt_automation.is_logged_in
    return {
        "message": "Custom ChatGPT API is running!", 
        "status": "healthy" if automation_ready else "initializing",
        "automation_ready": automation_ready
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a prompt to ChatGPT and return the response
    """
    try:
        # Check if automation is ready
        if not chatgpt_automation.is_initialized or not chatgpt_automation.is_logged_in:
            logger.error("Chat request received but automation not ready")
            return ChatResponse(
                response="", 
                success=False, 
                error_message="ChatGPT automation not ready. Please ensure server started successfully and login completed."
            )
        
        logger.info(f"Received chat request: {request.prompt[:50]}...")
        
        # Get response from ChatGPT
        response = await chatgpt_automation.get_chat_response(
            prompt=request.prompt,
            max_retries=request.max_retries
        )
        
        if response:
            logger.info("Successfully got response from ChatGPT")
            return ChatResponse(response=response, success=True)
        else:
            logger.error("Failed to get response from ChatGPT")
            return ChatResponse(
                response="", 
                success=False, 
                error_message="Failed to get response from ChatGPT"
            )
            
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check if automation is initialized and logged in
        if not chatgpt_automation.is_initialized or not chatgpt_automation.is_logged_in:
            return {
                "status": "unhealthy",
                "chatgpt_accessible": False,
                "error": "ChatGPT automation not ready - please ensure server started successfully"
            }
        
        # Test if ChatGPT automation is working
        test_response = await chatgpt_automation.get_chat_response("Hello", max_retries=1)
        return {
            "status": "healthy",
            "chatgpt_accessible": test_response is not None,
            "automation_ready": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "chatgpt_accessible": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
