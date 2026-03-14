# app.py – PrivacyGuardian Chatbot with Deletion Requests stored in MongoDB
# Run: pip install fastapi uvicorn httpx python-dotenv motor
# Then: python app.py

import os
import json
import logging
import datetime
from collections import deque
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

# Import real backend services (still used for compliance logging)
from services.deletion_service import DeletionService
from services.compliance_logger import ComplianceLogger

# ===================== CONFIGURATION =====================
HF_TOKEN = "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"  # Replace with your actual token
MODEL_NAME = "deepseek-ai/DeepSeek-R1:fastest"
API_URL = "https://router.huggingface.co/v1/chat/completions"

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://babinraj23comp_db_user:oygb4xukCMnKPWS0@chatbot.dwwgtcw.mongodb.net/?appName=Chatbot")
client = AsyncIOMotorClient(MONGO_URI)
db = client.privacyguardian

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== CONVERSATION MEMORY =====================
class ConversationMemory:
    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self._store: Dict[str, deque] = {}

    def add_message(self, user_id: str, user_msg: str, bot_reply: str):
        if user_id not in self._store:
            self._store[user_id] = deque(maxlen=self.max_history)
        self._store[user_id].append(f"User: {user_msg}")
        self._store[user_id].append(f"Assistant: {bot_reply}")

    def get_history(self, user_id: str) -> str:
        if user_id not in self._store:
            return ""
        return "\n".join(self._store[user_id])

memory = ConversationMemory()

# ===================== HELPER: STORE DELETION REQUEST =====================
async def store_deletion_request(user_id: str, field: Optional[str] = None):
    """
    Insert a deletion request into MongoDB for admin approval.
    field can be a specific field name or "all" for all data.
    """
    request = {
        "user_id": user_id,
        "field": field if field else "all",
        "timestamp": datetime.datetime.utcnow(),
        "status": "pending"
    }
    result = await db.deletion_requests.insert_one(request)
    logger.info(f"Stored deletion request: {request} with id {result.inserted_id}")
    return result.inserted_id

# ===================== HUGGINGFACE CLIENT =====================
async def query_huggingface(message: str, history: str = "") -> dict:
    system_instruction = """You are PrivacyGuardian, an AI assistant that helps users manage their privacy rights under the DPDP Act.

Your tasks:
- Understand user requests about deleting personal data, withdrawing consent, or accessing their information.
- Answer questions about the DPDP Act and user rights.
- Provide helpful information about the services PrivacyGuardian offers.
- Maintain context from the conversation history.

If the user asks to delete or manage data, return an action and relevant field.
If the user asks a general question, return an action "respond" and a helpful answer in the "response" field.

Return ONLY a valid JSON object with the following fields:
- "action": one of ["delete_field", "delete_all", "withdraw_consent", "get_data", "respond", "help", "unknown"]
- "field": (optional) the specific field to delete if action is "delete_field"
- "response": (optional) a natural language reply to the user"""

    messages = [{"role": "system", "content": system_instruction}]

    if history:
        lines = history.split("\n")
        for line in lines:
            if line.startswith("User: "):
                messages.append({"role": "user", "content": line[6:]})
            elif line.startswith("Assistant: "):
                messages.append({"role": "assistant", "content": line[11:]})

    messages.append({"role": "user", "content": message})

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "max_tokens": 300,
        "temperature": 0.1
    }

    logger.info(f"Sending request to Hugging Face router with model {MODEL_NAME}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(API_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling Hugging Face API: {str(e)}")
            raise

# ===================== INTENT PARSER =====================
def parse_ai_response(llm_response: dict) -> dict:
    try:
        content = llm_response["choices"][0]["message"]["content"].strip()
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            json_str = content[start:end]
            data = json.loads(json_str)
        else:
            data = json.loads(content)
        if "action" not in data:
            data["action"] = "unknown"
        return data
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse AI response: {e}")
        return {"action": "unknown", "response": "I'm having trouble understanding. Could you rephrase?"}

# ===================== KEYWORD FALLBACK =====================
async def keyword_fallback(user_id: str, message: str, logger_svc) -> dict:
    msg_lower = message.lower()

    # ----- Answer common questions -----
    if "rights under dpdp" in msg_lower or "what are my rights" in msg_lower:
        return {
            "action": "respond",
            "response": "Under the DPDP Act, you have the right to: 1) Access your data, 2) Correction and erasure, 3) Withdraw consent, 4) Grievance redressal, and 5) Nominate a representative. How can I help you with these rights?"
        }
    if "what can you do" in msg_lower or "help" in msg_lower:
        return {
            "action": "respond",
            "response": "I can help you delete your personal data (like phone, email, aadhaar), answer questions about the DPDP Act, or guide you on withdrawing consent. Just tell me what you'd like to do!"
        }
    if "who are you" in msg_lower or "your name" in msg_lower:
        return {
            "action": "respond",
            "response": "I'm PrivacyGuardian, your AI assistant for privacy rights under the DPDP Act. How can I assist you today?"
        }

    # ----- Delete all data (store request) -----
    if "delete all my data" in msg_lower or "delete all data" in msg_lower:
        await store_deletion_request(user_id, "all")
        await logger_svc.log_action(user_id, "delete_all_requested", None)
        return {"action": "delete_all", "response": "Your request to delete all data has been submitted for admin approval. You will be notified once it is processed."}

    # ----- General data deletion requests (for ambiguous requests) -----
    if ("delete" in msg_lower and "data" in msg_lower) or ("delete" in msg_lower and "information" in msg_lower):
        field_keywords = ["aadhaar", "pan", "phone", "email", "address", "passport", "driving", "account", "bank"]
        if not any(kw in msg_lower for kw in field_keywords):
            return {
                "action": "respond",
                "response": "I can help you delete specific data like your phone number, email, aadhaar, PAN, address, passport, driving license, or bank account. Please tell me which one you'd like to delete, or say 'delete all my data' to remove everything."
            }

    # ----- Field deletions (store request) -----
    fields = {
        "aadhaar": ["aadhaar", "aadhar"],
        "pan": ["pan"],
        "phone": ["phone", "phone number", "mobile", "mobile number"],
        "email": ["email", "email address", "e-mail"],
        "address": ["address", "residence", "home address"],
        "passport": ["passport", "passport number"],
        "driving_license": ["driving license", "driving licence", "license", "licence"],
        "account_number": ["account number", "bank account", "bank account number"]
    }

    for field, keywords in fields.items():
        for kw in keywords:
            if f"delete my {kw}" in msg_lower or f"remove my {kw}" in msg_lower:
                await store_deletion_request(user_id, field)
                await logger_svc.log_action(user_id, f"delete_field_requested:{field}", field)
                return {"action": "delete_field", "field": field, "response": f"Your request to delete your {field.replace('_', ' ')} has been submitted for admin approval. You will be notified once it is processed."}

    # ----- If nothing matched -----
    return {"action": "unknown", "response": "I'm not sure how to help. Try asking to delete your data or about your rights."}

# ===================== CHATBOT PROCESSOR =====================
async def process_chat(user_id: str, message: str) -> dict:
    history = memory.get_history(user_id)

    # Initialize services (only compliance logger is used now)
    logger_svc = ComplianceLogger(db)

    # Try AI interpretation first
    try:
        ai_response = await query_huggingface(message, history)
        intent = parse_ai_response(ai_response)
        action = intent.get("action", "unknown")
        field = intent.get("field")
        ai_reply = intent.get("response", "")
    except Exception as e:
        logger.error(f"Hugging Face API call failed, falling back to keywords: {e}")
        fallback_result = await keyword_fallback(user_id, message, logger_svc)
        action = fallback_result["action"]
        field = fallback_result.get("field")
        ai_reply = fallback_result.get("response", "")
        result = {
            "action": action,
            "field": field,
            "response": ai_reply
        }
        memory.add_message(user_id, message, result["response"])
        return result

    # Log the action locally
    await logger_svc.log_action(user_id, action, field)

    result = {
        "action": action,
        "field": field,
        "response": ai_reply
    }

    if action == "delete_field" and field:
        # Store deletion request instead of deleting directly
        await store_deletion_request(user_id, field)
        result["response"] = ai_reply or f"Your request to delete your {field} has been submitted for admin approval. You will be notified once it is processed."
    elif action == "delete_all":
        await store_deletion_request(user_id, "all")
        result["response"] = ai_reply or "Your request to delete all data has been submitted for admin approval. You will be notified once it is processed."
    elif action == "withdraw_consent":
        result["response"] = ai_reply or "Your consent has been withdrawn."  # This could also be a request if needed
    elif action == "get_data":
        # For now, just a placeholder – you could implement data retrieval if needed
        result["response"] = ai_reply or "Here is your data..."
    elif action in ["respond", "help"]:
        pass
    else:
        fallback_result = await keyword_fallback(user_id, message, logger_svc)
        result["action"] = fallback_result["action"]
        result["field"] = fallback_result.get("field")
        result["response"] = fallback_result.get("response", "I'm not sure how to help.")

    memory.add_message(user_id, message, result["response"])
    return result

# ===================== FASTAPI APP =====================
app = FastAPI(title="PrivacyGuardian Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    action: str
    field: Optional[str] = None
    status: str
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        result = await process_chat(req.user_id, req.message)
        return ChatResponse(
            action=result["action"],
            field=result.get("field"),
            status="completed",
            response=result.get("response", "")
        )
    except Exception as e:
        logger.exception("Unhandled exception in chat endpoint")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTMLResponse(content=HTML_PAGE)

# ===================== FRONTEND HTML (with User ID input) =====================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrivacyGuardian Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .chat-container {
            width: 450px;
            max-width: 90%;
            height: 700px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            animation: slideUp 0.5s ease;
        }
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .chat-header {
            background: #4a3f9d;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            letter-spacing: 1px;
        }
        /* User ID bar */
        .user-id-bar {
            display: flex;
            padding: 10px 20px;
            background: #e8e8f0;
            border-bottom: 1px solid #ccc;
            align-items: center;
            gap: 10px;
        }
        .user-id-bar label {
            font-weight: bold;
            color: #4a3f9d;
        }
        .user-id-bar input {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid #aaa;
            border-radius: 20px;
            outline: none;
        }
        .user-id-bar button {
            background: #4a3f9d;
            color: white;
            border: none;
            padding: 6px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        .user-id-bar button:hover {
            background: #372d7a;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f9f9ff;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user-message {
            justify-content: flex-end;
        }
        .bot-message {
            justify-content: flex-start;
        }
        .message-bubble {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 20px;
            font-size: 0.95rem;
            line-height: 1.4;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .user-message .message-bubble {
            background: #4a3f9d;
            color: white;
            border-bottom-right-radius: 5px;
        }
        .bot-message .message-bubble {
            background: white;
            color: #333;
            border-bottom-left-radius: 5px;
            border: 1px solid #e0e0e0;
        }
        .typing-indicator {
            display: flex;
            padding: 12px 16px;
            background: white;
            border-radius: 20px;
            border-bottom-left-radius: 5px;
            border: 1px solid #e0e0e0;
            width: fit-content;
        }
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background: #888;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: typing 1.4s infinite ease-in-out;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0% { transform: translateY(0px); background: #888; }
            60% { transform: translateY(-5px); background: #4a3f9d; }
            100% { transform: translateY(0px); background: #888; }
        }
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 15px 20px;
            background: #f0f0fa;
            border-top: 1px solid #ddd;
        }
        .suggestion-btn {
            background: white;
            border: 1px solid #4a3f9d;
            color: #4a3f9d;
            padding: 8px 15px;
            border-radius: 25px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .suggestion-btn:hover {
            background: #4a3f9d;
            color: white;
            transform: scale(1.05);
        }
        .chat-input-area {
            display: flex;
            padding: 15px 20px;
            background: white;
            border-top: 1px solid #ddd;
        }
        .chat-input-area input {
            flex: 1;
            padding: 12px 15px;
            border: 1px solid #ddd;
            border-radius: 25px;
            outline: none;
            font-size: 1rem;
            transition: border 0.2s;
        }
        .chat-input-area input:focus {
            border-color: #4a3f9d;
        }
        .chat-input-area button {
            background: #4a3f9d;
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-left: 10px;
            font-size: 1.2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s, transform 0.1s;
        }
        .chat-input-area button:hover {
            background: #372d7a;
            transform: scale(1.05);
        }
        .chat-input-area button:active {
            transform: scale(0.95);
        }
        .popup-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .popup-overlay.show {
            visibility: visible;
            opacity: 1;
        }
        .popup {
            background: white;
            border-radius: 15px;
            padding: 25px;
            width: 350px;
            max-width: 90%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            animation: popupScale 0.3s ease;
        }
        @keyframes popupScale {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .popup h3 {
            color: #4a3f9d;
            margin-bottom: 15px;
        }
        .popup p {
            margin-bottom: 20px;
            color: #555;
        }
        .popup-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
        }
        .popup-btn {
            padding: 10px 25px;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .confirm-btn {
            background: #4a3f9d;
            color: white;
        }
        .confirm-btn:hover {
            background: #372d7a;
        }
        .cancel-btn {
            background: #ddd;
            color: #333;
        }
        .cancel-btn:hover {
            background: #ccc;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            🔒 PrivacyGuardian
        </div>
        <div class="user-id-bar" id="userIdBar">
            <label>User ID:</label>
            <input type="text" id="userIdInput" placeholder="Enter your user ID">
            <button id="setUserIdBtn">Set</button>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                <div class="message-bubble">
                    Hello! Please set your User ID above to begin.
                </div>
            </div>
        </div>
        <div class="suggestions" id="suggestions">
            <button class="suggestion-btn" data-msg="What are my rights under DPDP?">📜 My Rights</button>
            <button class="suggestion-btn" data-msg="Delete my phone number">📱 Delete Phone</button>
            <button class="suggestion-btn" data-msg="Delete my aadhaar">🆔 Delete Aadhaar</button>
            <button class="suggestion-btn" data-msg="I want to withdraw consent">✋ Withdraw Consent</button>
            <button class="suggestion-btn" data-msg="What can you do?">❓ Help</button>
        </div>
        <div class="chat-input-area">
            <input type="text" id="userInput" placeholder="Type your message..." autocomplete="off">
            <button id="sendButton">➤</button>
        </div>
    </div>

    <div class="popup-overlay" id="popupOverlay">
        <div class="popup" id="popup">
            <h3 id="popupTitle">Confirm Action</h3>
            <p id="popupMessage">Are you sure you want to proceed?</p>
            <div class="popup-buttons">
                <button class="popup-btn cancel-btn" id="popupCancel">Cancel</button>
                <button class="popup-btn confirm-btn" id="popupConfirm">Confirm</button>
            </div>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        const sendButton = document.getElementById('sendButton');
        const suggestionBtns = document.querySelectorAll('.suggestion-btn');
        const popupOverlay = document.getElementById('popupOverlay');
        const popupTitle = document.getElementById('popupTitle');
        const popupMessage = document.getElementById('popupMessage');
        const popupConfirm = document.getElementById('popupConfirm');
        const popupCancel = document.getElementById('popupCancel');
        const userIdInput = document.getElementById('userIdInput');
        const setUserIdBtn = document.getElementById('setUserIdBtn');

        // Load user ID from localStorage or default to empty
        let USER_ID = localStorage.getItem('privacy_user_id') || '';
        userIdInput.value = USER_ID;

        function setUserId() {
            const newId = userIdInput.value.trim();
            if (newId) {
                USER_ID = newId;
                localStorage.setItem('privacy_user_id', USER_ID);
                addMessage(`User ID set to: ${USER_ID}`, false);
            } else {
                alert('Please enter a valid User ID');
            }
        }

        setUserIdBtn.addEventListener('click', setUserId);
        userIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') setUserId();
        });

        function addMessage(text, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');

            const bubble = document.createElement('div');
            bubble.classList.add('message-bubble');
            bubble.textContent = text;

            messageDiv.appendChild(bubble);
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.classList.add('message', 'bot-message');
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            chatMessages.appendChild(typingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function removeTyping() {
            const typing = document.getElementById('typingIndicator');
            if (typing) typing.remove();
        }

        function showPopup(title, message, actionData) {
            popupTitle.textContent = title;
            popupMessage.textContent = message;
            pendingAction = actionData;
            popupOverlay.classList.add('show');
        }

        function hidePopup() {
            popupOverlay.classList.remove('show');
            pendingAction = null;
        }

        async function sendMessage(message) {
            if (!message.trim()) return;
            if (!USER_ID) {
                addMessage('Please set your User ID first.', false);
                return;
            }

            addMessage(message, true);
            userInput.value = '';
            showTyping();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: USER_ID, message })
                });

                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();
                removeTyping();

                if (data.action === 'delete_field' || data.action === 'delete_all') {
                    const confirmMsg = data.action === 'delete_all'
                        ? 'Are you sure you want to request deletion of ALL your data? This requires admin approval.'
                        : `Are you sure you want to request deletion of your ${data.field}? This requires admin approval.`;
                    showPopup('Confirm Request', confirmMsg, {
                        action: data.action,
                        field: data.field,
                        originalResponse: data.response
                    });
                } else {
                    addMessage(data.response);
                }
            } catch (error) {
                removeTyping();
                addMessage('Sorry, something went wrong. Please try again.');
                console.error('Error:', error);
            }
        }

        popupConfirm.addEventListener('click', () => {
            if (pendingAction) {
                addMessage(pendingAction.originalResponse || 'Request submitted.');
                hidePopup();
            }
        });

        popupCancel.addEventListener('click', () => {
            if (pendingAction) {
                addMessage('Request cancelled.');
                hidePopup();
            }
        });

        popupOverlay.addEventListener('click', (e) => {
            if (e.target === popupOverlay) {
                addMessage('Request cancelled.');
                hidePopup();
            }
        });

        sendButton.addEventListener('click', () => {
            sendMessage(userInput.value);
        });

        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage(userInput.value);
            }
        });

        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                sendMessage(btn.dataset.msg);
            });
        });

        // If user ID already exists in localStorage, show a welcome message
        if (USER_ID) {
            addMessage(`Hello! I'm your privacy assistant. Your current User ID is ${USER_ID}. You can change it above. How can I help you today?`);
        } else {
            addMessage("Hello! I'm your privacy assistant. Please set your User ID above to begin.");
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting PrivacyGuardian Chatbot Server...")
    print(f"Using model: {MODEL_NAME}")
    print("MongoDB connected.")
    uvicorn.run(app, host="0.0.0.0", port=8900)