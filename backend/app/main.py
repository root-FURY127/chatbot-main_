from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from routes import (
    dashboard_routes,
    user_routes,
    deletion_routes,
    consent_routes,
    logs_routes,
    pii_routes,
    chatbot_routes,
)

app = FastAPI(title="PrivacyGuardian API", version="1.0.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard_routes.router, prefix="/api", tags=["Dashboard"])
app.include_router(user_routes.router, prefix="/api", tags=["User"])
app.include_router(deletion_routes.router, prefix="/api", tags=["Deletion"])
app.include_router(consent_routes.router, prefix="/api", tags=["Consent"])
app.include_router(logs_routes.router, prefix="/api", tags=["Logs"])
app.include_router(pii_routes.router, prefix="/api", tags=["PII"])
app.include_router(chatbot_routes.router, prefix="/api", tags=["Chatbot"])

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()