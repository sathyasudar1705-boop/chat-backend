import os
import sys
import uuid
import urllib.parse
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# If running from the app/ folder directly, add the project root to sys.path
# so absolute imports like "from app.database import ..." resolve correctly.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import httpx

from app.database import engine, Base, get_db
from app.models import User, ChatSession, ChatMessage, AIUsageLog, ImageGeneration, UserSettings, ProviderModel, ProviderStatus
from app.schemas import (
    UserRegister, UserLogin, UserOut, Token,
    ChatSessionCreate, ChatSessionOut, ChatMessageCreate, ChatMessageOut, ChatMessagePostRequest, ChatResponse,
    ImageGenerateRequest, ImageGenerationOut,
    AIUsageLogOut, UsageSummaryOut,
    UserSettingsOut, UserSettingsUpdate
)
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.router_ai import ask_ai, API_KEYS, DEFAULT_MODELS, sync_all_providers, sync_provider_models, validate_provider_model, is_api_key_configured

# Automatically create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure Multi-Provider AI Chatbot Platform")

@app.on_event("startup")
async def startup_event():
    import asyncio
    from app.database import SessionLocal
    async def sync_on_start():
        db = SessionLocal()
        try:
            await sync_all_providers(db)
        except Exception as e:
            print(f"Failed to sync on startup: {e}")
        finally:
            db.close()
            
    asyncio.create_task(sync_on_start())

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Setup Static Files for Generated Images
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
IMAGE_DIR = os.path.join(STATIC_DIR, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def root():
    return {"message": "Backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}


# ==========================================
# AUTH ENDPOINTS
# ==========================================

@app.post("/api/auth/register", response_model=UserOut)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered."
        )
    
    # Validate password length
    if len(user_data.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 72 bytes or less"
        )
    
    # Hash password
    hashed_pwd = get_password_hash(user_data.password)
    
    # Create User
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create Default User Settings
    default_settings = UserSettings(
        user_id=new_user.id,
        default_provider="mistral",
        default_model="open-mixtral-8x7b",
        fallback_enabled=True,
        theme="dark"
    )
    db.add(default_settings)
    db.commit()
    
    return new_user

@app.post("/api/auth/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate Token
    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ==========================================
# CHAT ENDPOINTS
# ==========================================

@app.get("/api/chat/sessions", response_model=List[ChatSessionOut])
def get_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: filter by current_user.id
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return sessions

@app.post("/api/chat/sessions", response_model=ChatSessionOut)
def create_session(session_data: ChatSessionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_session = ChatSession(
        user_id=current_user.id,
        title=session_data.title
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@app.get("/api/chat/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
def get_session_messages(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: Verify session belongs to current_user
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return messages

@app.post("/api/chat/sessions/{session_id}/messages", response_model=ChatMessageOut)
def create_custom_message(session_id: int, req: ChatMessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: Verify session belongs to current_user
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    msg = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        role=req.role,
        content=req.content,
        provider=req.provider,
        model=req.model
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    # Update session's updated_at timestamp
    session.updated_at = datetime.utcnow()
    db.commit()
    
    return msg

@app.delete("/api/chat/sessions/{session_id}")
def delete_session(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: Verify session belongs to current_user
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    db.delete(session)
    db.commit()
    return {"detail": "Chat session deleted successfully."}

@app.post("/api/chat/message", response_model=ChatResponse)
async def post_message(req: ChatMessagePostRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Request validation before calling AI
    if not req.content or not req.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    if not validate_provider_model(req.provider, req.model, "chat", db):
        raise HTTPException(
            status_code=400,
            detail="This model is not available for the selected provider."
        )

    # Security: Verify session belongs to current_user
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    # Get user settings for fallback mode
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    fallback_enabled = settings.fallback_enabled if settings else True
    
    # Save user message
    user_msg = ChatMessage(
        session_id=req.session_id,
        user_id=current_user.id,
        role="user",
        content=req.content,
        provider=req.provider,
        model=req.model
    )
    db.add(user_msg)
    db.commit()
    
    # Gather chat history (limit to last 15 messages for context size)
    history_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == req.session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Format history for API call (omit the last user message we just saved)
    formatted_history = []
    for msg in history_messages[:-1]:
        formatted_history.append({
            "role": msg.role,
            "content": msg.content
        })
        
    # Call multi-provider router
    ai_response = await ask_ai(
        message=req.content,
        user_id=current_user.id,
        provider=req.provider,
        model=req.model,
        chat_history=formatted_history,
        fallback_enabled=fallback_enabled,
        db=db
    )
    
    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=req.session_id,
        user_id=current_user.id,
        role="assistant",
        content=ai_response["answer"],
        provider=ai_response["provider_used"],
        model=ai_response["model_used"]
    )
    db.add(assistant_msg)
    
    # Update session's updated_at timestamp and title if it was default
    session.updated_at = datetime.utcnow()
    if session.title == "New Chat":
        # Generate short title from first 6 words of user prompt
        words = req.content.split()
        short_title = " ".join(words[:6])
        if len(words) > 6:
            short_title += "..."
        session.title = short_title
        
    db.commit()
    db.refresh(assistant_msg)
    
    return {
        "answer": ai_response["answer"],
        "provider_used": ai_response["provider_used"],
        "model_used": ai_response["model_used"],
        "fallback_used": ai_response["fallback_used"],
        "response_time_ms": ai_response["response_time_ms"],
        "tokens_input": ai_response["token_usage"]["prompt_tokens"],
        "tokens_output": ai_response["token_usage"]["completion_tokens"],
        "chat_message_id": assistant_msg.id
    }


# ==========================================
# PROVIDER & MODEL ENDPOINTS
# ==========================================

@app.get("/api/models")
async def get_models(background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Auto-refresh check: if there is no status, or if latest status is older than 24h
    latest_status = db.query(ProviderStatus).order_by(ProviderStatus.updated_at.desc()).first()
    needs_refresh = False
    if not latest_status:
        needs_refresh = True
    else:
        # If older than 24 hours
        if (datetime.utcnow() - latest_status.updated_at.replace(tzinfo=None)) > timedelta(hours=24):
            needs_refresh = True
            
    if needs_refresh:
        background_tasks.add_task(sync_all_providers, db)

    providers_list = []
    statuses = {s.provider: s for s in db.query(ProviderStatus).all()}
    
    models_by_provider = {}
    for m in db.query(ProviderModel).filter(ProviderModel.active == True).all():
        if m.provider not in models_by_provider:
            models_by_provider[m.provider] = []
        models_by_provider[m.provider].append({
            "id": m.model_id,
            "name": m.name,
            "active": m.active,
            "supports_chat": m.supports_chat,
            "supports_image": m.supports_image
        })
        
    for provider in ["gemini", "groq", "openrouter", "cerebras", "mistral", "pollinations"]:
        status = statuses.get(provider)
        enabled = False
        if provider == "pollinations":
            enabled = True
        elif status:
            enabled = status.api_key_configured
        else:
            enabled = is_api_key_configured(provider)
            
        models = models_by_provider.get(provider, [])
        
        # Fresh startup fallbacks to prevent empty UI dropdowns
        if not models and enabled:
            if provider == "groq":
                models = [{"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "active": True, "supports_chat": True, "supports_image": False}]
            elif provider == "mistral":
                models = [{"id": "open-mixtral-8x7b", "name": "Open Mixtral 8x7B", "active": True, "supports_chat": True, "supports_image": False}]
            elif provider == "gemini":
                models = [{"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "active": True, "supports_chat": True, "supports_image": False}]
            elif provider == "openrouter":
                models = [{"id": "meta-llama/llama-3.1-8b-instruct:free", "name": "Llama 3.1 8B Instruct (Free)", "active": True, "supports_chat": True, "supports_image": False}]
            elif provider == "cerebras":
                models = [{"id": "llama3.1-8b", "name": "Llama 3.1 8B", "active": True, "supports_chat": True, "supports_image": False}]
            elif provider == "pollinations":
                models = [
                    {"id": "flux", "name": "Flux", "active": True, "supports_chat": False, "supports_image": True},
                    {"id": "default", "name": "Default", "active": True, "supports_chat": False, "supports_image": True}
                ]
                
        providers_list.append({
            "name": provider,
            "enabled": enabled,
            "models": models
        })
        
    return {"providers": providers_list}

@app.post("/api/models/refresh")
async def refresh_models(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    await sync_all_providers(db)
    return {"detail": "Model registry refreshed successfully."}

@app.get("/api/providers/status")
def get_providers_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    statuses = db.query(ProviderStatus).all()
    status_dict = {s.provider: s for s in statuses}
    
    result = []
    for provider in ["gemini", "groq", "openrouter", "cerebras", "mistral", "pollinations"]:
        s = status_dict.get(provider)
        if s:
            result.append({
                "provider": provider,
                "api_key_configured": s.api_key_configured,
                "models_fetched": s.models_fetched,
                "working": s.working,
                "last_error": s.last_error,
                "active_model_count": s.active_model_count
            })
        else:
            is_configured = is_api_key_configured(provider) if provider != "pollinations" else True
            result.append({
                "provider": provider,
                "api_key_configured": is_configured,
                "models_fetched": False,
                "working": False,
                "last_error": "Not synced yet",
                "active_model_count": 0
            })
    return result


@app.get("/api/models/image")
async def get_image_models(current_user: User = Depends(get_current_user)):
    gemini_models = ["gemini-3.1-flash-image", "gemini-3-pro-image", "gemini-2.5-flash-image"]
    mistral_models = ["pixtral-12b", "mistral-large-latest"]
    openrouter_models = []
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            key = API_KEYS.get("openrouter")
            if key:
                headers["Authorization"] = f"Bearer {key}"
            response = await client.get("https://openrouter.ai/api/v1/models?output_modalities=image", headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                for m in data.get("data", []):
                    model_id = m.get("id", "").lower()
                    description = m.get("description", "").lower()
                    # Filter for models that support image output
                    modalities = m.get("architecture", {}).get("modality", "")
                    is_image = "image" in modalities or "text->image" in modalities
                    
                    if is_image or any(term in model_id for term in ["diffusion", "flux", "dall-e", "midjourney"]) or "generate images" in description:
                        openrouter_models.append(m.get("id"))
    except Exception as e:
        print(f"Failed to fetch OpenRouter image models: {e}")
        
    if not openrouter_models:
        openrouter_models = [
            "stabilityai/stable-diffusion-xl",
            "black-forest-labs/flux-1-schnell",
            "black-forest-labs/flux-1-dev",
            "openai/dall-e-3"
        ]
        
    return {
        "gemini": gemini_models,
        "openrouter": openrouter_models,
        "mistral": mistral_models
    }


# ==========================================
# IMAGE GENERATION ENDPOINTS
# ==========================================

@app.post("/api/image/generate")
async def generate_image(req: ImageGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not validate_provider_model(req.provider, req.model, "image", db):
        raise HTTPException(
            status_code=400,
            detail="This model is not available for the selected provider."
        )
    try:
        # Build image URL using pollinations (no downloading/local file saving)
        prompt_encoded = urllib.parse.quote(req.prompt)
        image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&nologo=true&private=true"
        
        # Save record to Database
        new_image = ImageGeneration(
            user_id=current_user.id,
            provider="pollinations",
            model="default",
            prompt=req.prompt,
            image_url_or_path=image_url,
            status="success"
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        
        return {
            "id": new_image.id,
            "user_id": new_image.user_id,
            "status": "success",
            "provider": "pollinations",
            "model": "default",
            "image_url": image_url,
            "image_url_or_path": image_url,
            "prompt": req.prompt,
            "created_at": new_image.created_at
        }
    except Exception as e:
        print(f"[ERROR] Provider: {req.provider}, Model: {req.model}, StatusCode: 500, Message: {str(e)}, RequestType: image")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@app.get("/api/image/my-gallery", response_model=List[ImageGenerationOut])
def get_my_gallery(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: filter by current_user.id
    images = db.query(ImageGeneration).filter(
        ImageGeneration.user_id == current_user.id,
        ImageGeneration.status == "success"
    ).order_by(ImageGeneration.created_at.desc()).all()
    return images

@app.delete("/api/image/{image_id}")
def delete_image(image_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: Verify ownership
    image = db.query(ImageGeneration).filter(ImageGeneration.id == image_id, ImageGeneration.user_id == current_user.id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found.")
        
    # Delete file from local static directory if it exists
    if image.image_url_or_path:
        filename = os.path.basename(image.image_url_or_path)
        filepath = os.path.join(IMAGE_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Failed to delete file {filepath}: {e}")
                
    db.delete(image)
    db.commit()
    return {"detail": "Image deleted successfully."}


# ==========================================
# ANALYTICS ENDPOINTS
# ==========================================

@app.get("/api/usage/summary", response_model=UsageSummaryOut)
def get_usage_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: filter by current_user.id
    user_id = current_user.id
    
    total_chats = db.query(ChatSession).filter(ChatSession.user_id == user_id).count()
    total_messages = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
    total_images = db.query(ImageGeneration).filter(ImageGeneration.user_id == user_id, ImageGeneration.status == "success").count()
    
    # Gather logs for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    logs = db.query(AIUsageLog).filter(
        AIUsageLog.user_id == user_id,
        AIUsageLog.created_at >= thirty_days_ago
    ).all()
    
    total_requests = len(logs)
    fallback_count = sum(1 for log in logs if log.fallback_used and log.status == "success")
    
    # Average response time
    success_logs = [log for log in logs if log.status == "success"]
    avg_response_time = sum(log.response_time_ms for log in success_logs) / len(success_logs) if success_logs else 0.0
    
    # Provider usage counts
    provider_counts = {}
    for log in success_logs:
        provider_counts[log.provider] = provider_counts.get(log.provider, 0) + 1
        
    most_used_provider = max(provider_counts, key=provider_counts.get) if provider_counts else None
    
    # 7-day daily usage for chart
    daily_stats = {}
    for i in range(7):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_stats[d] = {"date": d, "requests": 0, "success": 0, "error": 0}
        
    for log in logs:
        date_str = log.created_at.strftime("%Y-%m-%d")
        if date_str in daily_stats:
            daily_stats[date_str]["requests"] += 1
            if log.status == "success":
                daily_stats[date_str]["success"] += 1
            else:
                daily_stats[date_str]["error"] += 1
                
    daily_usage_list = sorted(list(daily_stats.values()), key=lambda x: x["date"])
    
    return {
        "total_chats": total_chats,
        "total_messages": total_messages,
        "total_requests": total_requests,
        "total_images": total_images,
        "most_used_provider": most_used_provider,
        "fallback_count": fallback_count,
        "avg_response_time_ms": avg_response_time,
        "provider_usage": provider_counts,
        "daily_usage": daily_usage_list
    }

@app.get("/api/usage/logs", response_model=List[AIUsageLogOut])
def get_usage_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: filter by current_user.id
    logs = db.query(AIUsageLog).filter(
        AIUsageLog.user_id == current_user.id
    ).order_by(AIUsageLog.created_at.desc()).limit(100).all()
    return logs


# ==========================================
# SETTINGS ENDPOINTS
# ==========================================

@app.get("/api/settings", response_model=UserSettingsOut)
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: filter by current_user.id
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        # Fallback create
        settings = UserSettings(
            user_id=current_user.id,
            default_provider="gemini",
            default_model="gemini-1.5-flash",
            fallback_enabled=True,
            theme="dark"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.put("/api/settings", response_model=UserSettingsOut)
def update_settings(update_data: UserSettingsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: filter by current_user.id
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found.")
        
    if update_data.default_provider is not None:
        settings.default_provider = update_data.default_provider
    if update_data.default_model is not None:
        settings.default_model = update_data.default_model
    if update_data.fallback_enabled is not None:
        settings.fallback_enabled = update_data.fallback_enabled
    if update_data.theme is not None:
        settings.theme = update_data.theme
        
    db.commit()
    db.refresh(settings)
    return settings

@app.delete("/api/settings/chat-history")
def clear_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: Verify isolation, only delete sessions belonging to current_user
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()
    for session in sessions:
        db.delete(session)
    db.commit()
    return {"detail": "All chat history cleared successfully."}

@app.delete("/api/settings/image-history")
def clear_image_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: Verify isolation, only delete images belonging to current_user
    images = db.query(ImageGeneration).filter(ImageGeneration.user_id == current_user.id).all()
    for image in images:
        if image.image_url_or_path:
            filename = os.path.basename(image.image_url_or_path)
            filepath = os.path.join(IMAGE_DIR, filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Failed to delete file {filepath}: {e}")
        db.delete(image)
    db.commit()
    return {"detail": "All generated image history cleared successfully."}
