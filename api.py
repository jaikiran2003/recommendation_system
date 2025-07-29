from fastapi import FastAPI
from pydantic import BaseModel
from llm_handler import chat_with_phi, reset_conversation

app = FastAPI(
    title="Maruti Suzuki Car Salesman API",
    description="API backend for your Maruti Suzuki chatbot",
    version="1.0"
)

# Request and Response models
class ChatRequest(BaseModel):
    user_message: str

class ChatResponse(BaseModel):
    bot_response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    bot_reply = chat_with_phi(request.user_message)
    return ChatResponse(bot_response=bot_reply)


@app.post("/reset")
async def reset_endpoint():
    reset_conversation()
    return {"message": "Conversation reset successfully!"}
