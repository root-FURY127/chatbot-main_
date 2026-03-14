from fastapi import APIRouter, HTTPException, Depends
from services.chatbot_processor import ChatbotProcessor
from app.database import get_db

router = APIRouter()

def get_chatbot_processor(db=Depends(get_db)):
    return ChatbotProcessor(db)

@router.post("/chatbot")
async def chatbot(
    request: dict,
    processor: ChatbotProcessor = Depends(get_chatbot_processor)
):
    """Process natural language commands from chatbot"""
    user_id = request.get("user_id")
    message = request.get("message")
    if not user_id or not message:
        raise HTTPException(status_code=400, detail="user_id and message are required")
    action = await processor.parse_and_execute(user_id, message)
    return action