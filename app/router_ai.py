import os
import time
import httpx
from typing import List, Dict, Tuple, Optional, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import AIUsageLog, ProviderModel, ProviderStatus
from dotenv import load_dotenv

load_dotenv()

# API Keys
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "groq": os.getenv("GROQ_API_KEY", ""),
    "openrouter": os.getenv("OPENROUTER_API_KEY", ""),
    "cerebras": os.getenv("CEREBRAS_API_KEY", ""),
    "mistral": os.getenv("MISTRAL_API_KEY", ""),
}

# Endpoints
ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "cerebras": "https://api.cerebras.ai/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
}

# Default Models
DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.1-8b-instruct:free",
    "cerebras": "llama3.1-8b",
    "mistral": "open-mixtral-8x7b",
}



SYSTEM_PROMPT = (
    "You are a secure personal AI assistant. You must answer only using the logged-in user's own data "
    "and allowed context. Never reveal, guess, or use another user's data. If the user asks about "
    "another user or unrelated private data, politely refuse."
)

def is_api_key_configured(provider: str) -> bool:
    if provider == "pollinations":
        return True
    key = API_KEYS.get(provider, "")
    return bool(key and not key.startswith("your-") and len(key) > 10)

async def sync_provider_models(provider: str, db: Session):
    is_configured = is_api_key_configured(provider)
    
    status = db.query(ProviderStatus).filter(ProviderStatus.provider == provider).first()
    if not status:
        status = ProviderStatus(provider=provider)
        db.add(status)
        
    status.api_key_configured = is_configured
    
    if not is_configured:
        status.models_fetched = False
        status.working = False
        status.last_error = "API Key not configured"
        status.active_model_count = 0
        db.commit()
        db.query(ProviderModel).filter(ProviderModel.provider == provider).update({"active": False})
        db.commit()
        return

    try:
        models = []
        if provider == "pollinations":
            models = [
                {"id": "flux", "name": "Flux", "supports_chat": False, "supports_image": True},
                {"id": "default", "name": "Default", "supports_chat": False, "supports_image": True}
            ]
        elif provider == "gemini":
            api_key = API_KEYS.get("gemini")
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        model_id = m.get("name", "").replace("models/", "")
                        model_id_lower = model_id.lower()
                        exclude_terms = ["image", "tts", "clip", "computer-use", "robotics", "er-1.5", "er-1.6", "deep-research", "audio", "embedding", "vision", "bidi"]
                        if any(term in model_id_lower for term in exclude_terms):
                            continue
                        display_name = m.get("displayName", model_id)
                        models.append({
                            "id": model_id,
                            "name": display_name,
                            "supports_chat": True,
                            "supports_image": False
                        })
                # Verify Gemini key actually works for completions (detecting 429 quota/limit 0 issues)
                if models:
                    stable_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
                    test_model = next((m["id"] for m in models if m["id"] in stable_models), models[0]["id"])
                    test_url = f"https://generativelanguage.googleapis.com/v1beta/models/{test_model}:generateContent?key={api_key}"
                    test_payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                    test_res = client.post(test_url, json=test_payload, timeout=5.0)
                    test_res.raise_for_status()
        elif provider == "groq":
            api_key = API_KEYS.get("groq")
            url = "https://api.groq.com/openai/v1/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                for m in data.get("data", []):
                    model_id = m.get("id", "")
                    model_id_lower = model_id.lower()
                    exclude_terms = ["guard", "whisper", "safeguard"]
                    if any(term in model_id_lower for term in exclude_terms):
                        continue
                    models.append({
                        "id": model_id,
                        "name": model_id,
                        "supports_chat": True,
                        "supports_image": False
                    })
                # Verify Groq key actually works for completions
                if models:
                    stable_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "groq/compound-mini"]
                    test_model = next((m["id"] for m in models if m["id"] in stable_models), models[0]["id"])
                    test_url = "https://api.groq.com/openai/v1/chat/completions"
                    test_payload = {
                        "model": test_model,
                        "messages": [{"role": "user", "content": "H"}],
                        "max_tokens": 1
                    }
                    test_res = client.post(test_url, json=test_payload, headers=headers, timeout=5.0)
                    test_res.raise_for_status()
        elif provider == "openrouter":
            api_key = API_KEYS.get("openrouter")
            url = "https://openrouter.ai/api/v1/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://chatbot.secure.platform",
                "X-Title": "Secure AI Chatbot",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                for m in data.get("data", []):
                    model_id = m.get("id", "")
                    model_id_lower = model_id.lower()
                    if ":free" not in model_id_lower:
                        continue
                    display_name = m.get("name", model_id)
                    architecture = m.get("architecture", {})
                    modality = architecture.get("modality", "") if architecture else ""
                    
                    is_chat = False
                    if modality:
                        if modality.endswith("text") or "->text" in modality:
                            is_chat = True
                    else:
                        is_chat = True
                        
                    if is_chat:
                        models.append({
                            "id": model_id,
                            "name": display_name,
                            "supports_chat": True,
                            "supports_image": False
                        })
                # Verify OpenRouter key actually works and is not rate-limited/out of quota
                if models:
                    stable_models = ["meta-llama/llama-3.2-3b-instruct:free", "meta-llama/llama-3.3-70b-instruct:free"]
                    test_model = next((m["id"] for m in models if m["id"] in stable_models), models[0]["id"])
                    test_url = "https://openrouter.ai/api/v1/chat/completions"
                    test_payload = {
                        "model": test_model,
                        "messages": [{"role": "user", "content": "H"}],
                        "max_tokens": 1
                    }
                    test_res = client.post(test_url, json=test_payload, headers=headers, timeout=5.0)
                    test_res.raise_for_status()
        elif provider == "cerebras":
            api_key = API_KEYS.get("cerebras")
            url = "https://api.cerebras.ai/v1/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                for m in data.get("data", []):
                    model_id = m.get("id", "")
                    models.append({
                        "id": model_id,
                        "name": model_id,
                        "supports_chat": True,
                        "supports_image": False
                    })
                # Verify Cerebras key actually works for completions (since list-models succeeds with bad keys)
                if models:
                    stable_models = ["llama3.1-8b", "llama3.1-70b"]
                    test_model = next((m["id"] for m in models if m["id"] in stable_models), models[0]["id"])
                    test_url = "https://api.cerebras.ai/v1/chat/completions"
                    test_payload = {
                        "model": test_model,
                        "messages": [{"role": "user", "content": "H"}],
                        "max_tokens": 1
                    }
                    test_res = client.post(test_url, json=test_payload, headers=headers, timeout=5.0)
                    test_res.raise_for_status()
        elif provider == "mistral":
            api_key = API_KEYS.get("mistral")
            url = "https://api.mistral.ai/v1/models"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                for m in data.get("data", []):
                    model_id = m.get("id", "")
                    model_id_lower = model_id.lower()
                    exclude_terms = ["ocr", "tts", "realtime", "transcribe", "vibe", "embed", "moderation", "vision"]
                    if any(term in model_id_lower for term in exclude_terms):
                        continue
                    models.append({
                        "id": model_id,
                        "name": model_id,
                        "supports_chat": True,
                        "supports_image": False
                    })
                # Verify Mistral key actually works for completions
                if models:
                    stable_models = ["open-mistral-nemo", "mistral-tiny"]
                    test_model = next((m["id"] for m in models if m["id"] in stable_models), models[0]["id"])
                    test_url = "https://api.mistral.ai/v1/chat/completions"
                    test_payload = {
                        "model": test_model,
                        "messages": [{"role": "user", "content": "H"}],
                        "max_tokens": 1
                    }
                    test_res = client.post(test_url, json=test_payload, headers=headers, timeout=5.0)
                    test_res.raise_for_status()

        # Save to database
        db.query(ProviderModel).filter(ProviderModel.provider == provider).delete()
        
        # Prepare list of dicts for bulk insert
        db_models = []
        for m in models:
            db_models.append({
                "provider": provider,
                "model_id": m["id"],
                "name": m["name"],
                "active": True,
                "supports_chat": m["supports_chat"],
                "supports_image": m["supports_image"]
            })
            
        if db_models:
            db.bulk_insert_mappings(ProviderModel, db_models)
            
        status.models_fetched = True
        status.working = True
        status.last_error = None
        status.active_model_count = len(models)
        db.commit()

    except Exception as e:
        status.models_fetched = False
        status.working = False
        status.last_error = str(e)
        status.active_model_count = 0
        db.commit()
        db.query(ProviderModel).filter(ProviderModel.provider == provider).update({"active": False})
        db.commit()
        print(f"Failed to sync provider {provider}: {e}")

async def sync_all_providers(db: Session):
    for provider in ["gemini", "groq", "openrouter", "cerebras", "mistral", "pollinations"]:
        await sync_provider_models(provider, db)

def validate_provider_model(provider: str, model: str, operation: str, db: Session) -> bool:
    prov_lower = provider.lower()
    
    if prov_lower == "auto" or model == "auto":
        return True
        
    model_count = db.query(ProviderModel).count()
    if model_count == 0:
        FALLBACK_VALIDATION = {
            "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
            "mistral": ["open-mixtral-8x7b", "mistral-tiny", "mistral-small-latest"],
            "gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
            "openrouter": ["meta-llama/llama-3.1-8b-instruct:free", "google/gemma-2-9b-it:free", "mistralai/mistral-7b-instruct:free"],
            "cerebras": ["llama3.1-8b", "llama3.1-70b"],
            "pollinations": ["flux", "default"]
        }
        valid_models = FALLBACK_VALIDATION.get(prov_lower, [])
        if model not in valid_models:
            return False
        if operation == "image" and prov_lower != "pollinations":
            return False
        if operation == "chat" and prov_lower == "pollinations":
            return False
        return True
        
    db_model = db.query(ProviderModel).filter(
        ProviderModel.provider == prov_lower,
        ProviderModel.model_id == model,
        ProviderModel.active == True
    ).first()
    
    if not db_model:
        return False
        
    status = db.query(ProviderStatus).filter(ProviderStatus.provider == prov_lower).first()
    if status and not status.api_key_configured:
        return False
        
    if operation == "chat" and not db_model.supports_chat:
        return False
    if operation == "image" and not db_model.supports_image:
        return False
        
    return True

async def call_gemini(message: str, model: str, chat_history: List[Dict[str, str]], system_prompt: str, api_key: str, timeout: float = 15.0) -> Tuple[str, int, int]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Format chat history for Gemini
    contents = []
    for msg in chat_history:
        # Gemini roles: user, model
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}]
        })
        
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })
    
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=timeout)
        
        # Check non-retryable status codes
        if response.status_code in [401, 403]:
            raise httpx.HTTPStatusError("Invalid API key or Authentication error", request=response.request, response=response)
        if response.status_code == 400:
            raise httpx.HTTPStatusError("Bad request or validation error", request=response.request, response=response)
            
        response.raise_for_status()
        data = response.json()
        
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Empty response or potentially blocked by safety policies")
            
        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        if finish_reason == "SAFETY":
            raise ValueError("Safety blocked response")
            
        text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
        if not text:
            raise ValueError("Empty content returned from Gemini")
            
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)
        
        return text, prompt_tokens, completion_tokens

async def call_openai_compatible(provider: str, model: str, message: str, chat_history: List[Dict[str, str]], system_prompt: str, api_key: str, timeout: float = 15.0) -> Tuple[str, int, int]:
    endpoint = ENDPOINTS[provider]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # OpenRouter specifics
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://chatbot.secure.platform"
        headers["X-Title"] = "Secure AI Chatbot"

    # Build messages payload
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({
            "role": msg.get("role"),
            "content": msg.get("content")
        })
    messages.append({"role": "user", "content": message})
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, headers=headers, json=payload, timeout=timeout)
        
        # Check non-retryable status codes
        if response.status_code in [401, 403]:
            print(f"Auth error ({response.status_code}) from {provider}: {response.text}")
            raise httpx.HTTPStatusError("Invalid API key or Authentication error", request=response.request, response=response)
        if response.status_code in [400, 404]:
            print(f"Request error ({response.status_code}) from {provider}: {response.text}")
            raise httpx.HTTPStatusError("Bad request or wrong model name", request=response.request, response=response)
            
        response.raise_for_status()
        data = response.json()
        
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("Empty choices array in API response")
            
        candidate = choices[0]
        text = candidate.get("message", {}).get("content", "")
        
        finish_reason = candidate.get("finish_reason")
        if finish_reason == "content_filter":
            raise ValueError("Safety blocked response")
            
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        return text, prompt_tokens, completion_tokens

def save_usage_log(db: Session, user_id: int, provider: str, model: str, status: str, response_time_ms: int, fallback_used: bool, error_message: Optional[str] = None, prompt_tokens: int = 0, completion_tokens: int = 0):
    if db:
        try:
            log = AIUsageLog(
                user_id=user_id,
                provider=provider,
                model=model,
                status=status,
                error_message=error_message,
                tokens_input=prompt_tokens,
                tokens_output=completion_tokens,
                response_time_ms=response_time_ms,
                fallback_used=fallback_used
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Failed to save usage log: {e}")

def get_default_model(provider: str, db: Session) -> str:
    db_model = db.query(ProviderModel).filter(
        ProviderModel.provider == provider,
        ProviderModel.active == True,
        ProviderModel.supports_chat == True
    ).first()
    if db_model:
        return db_model.model_id
    return DEFAULT_MODELS.get(provider, "")

async def ask_ai(message: str, user_id: int, provider: str = "auto", model: str = "auto", chat_history: List[Dict[str, str]] = None, fallback_enabled: bool = True, db: Session = None) -> Dict[str, Any]:
    # Validate selected model name if provider and model are specifically requested
    prov_lower = provider.lower()
    if db:
        if not validate_provider_model(provider, model, "chat", db):
            raise HTTPException(
                status_code=400,
                detail="This model is not available for the selected provider."
            )

    if chat_history is None:
        chat_history = []
        
    start_provider = provider.lower()
    
    # Build priority chain dynamically from working providers
    working_providers = []
    if db:
        active_statuses = db.query(ProviderStatus).filter(ProviderStatus.working == True).all()
        working_providers = [s.provider for s in active_statuses if s.provider != "pollinations" and s.provider in DEFAULT_MODELS]
        
    PRIORITY_ORDER = ["groq", "mistral", "gemini", "openrouter", "cerebras"]
    priority_chain = [p for p in PRIORITY_ORDER if p in working_providers]
    if not priority_chain:
        priority_chain = ["groq", "mistral"]
    
    # Build the list of providers to try based on priority chain
    if start_provider == "auto" or start_provider not in priority_chain:
        providers_to_try = priority_chain.copy()
    else:
        # If user specifies a starting provider, try it first.
        # If fallback is enabled, we append subsequent providers from the priority chain.
        idx = priority_chain.index(start_provider)
        if fallback_enabled:
            providers_to_try = priority_chain[idx:]
        else:
            providers_to_try = [start_provider]
            
    failed_providers = []
    fallback_occurred = False
    
    for i, current_prov in enumerate(providers_to_try):
        if model != "auto" and i == 0:
            current_model = model
        else:
            if db:
                current_model = get_default_model(current_prov, db)
            else:
                current_model = DEFAULT_MODELS.get(current_prov, "")
                
        api_key = API_KEYS.get(current_prov)
        
        # Check if API key is present
        if not api_key:
            err_msg = f"API key for {current_prov} not found in environment."
            print(f"[ERROR] Provider: {current_prov}, Model: {current_model}, StatusCode: 500, Message: {err_msg}, RequestType: chat")
            failed_providers.append(current_prov)
            save_usage_log(
                db=db,
                user_id=user_id,
                provider=current_prov,
                model=current_model,
                status="error",
                response_time_ms=0,
                fallback_used=fallback_occurred,
                error_message=err_msg
            )
            if not fallback_enabled or i == len(providers_to_try) - 1:
                raise HTTPException(status_code=500, detail=err_msg)
            fallback_occurred = True
            continue
            
        # Verify API key format for Gemini
        if current_prov == "gemini":
            if not (api_key.startswith("AIzaSy") and len(api_key) == 39) and not (api_key.startswith("AQ") and len(api_key) >= 100):
                err_msg = "Invalid Gemini API key format"
                print(f"[ERROR] Provider: {current_prov}, Model: {current_model}, StatusCode: 400, Message: {err_msg}, RequestType: chat")
                failed_providers.append(current_prov)
                save_usage_log(
                    db=db,
                    user_id=user_id,
                    provider=current_prov,
                    model=current_model,
                    status="error",
                    response_time_ms=0,
                    fallback_used=fallback_occurred,
                    error_message=err_msg
                )
                raise HTTPException(status_code=400, detail=err_msg)
            
        start_time = time.time()
        try:
            # Execute request
            if current_prov == "gemini":
                answer, prompt_tokens, completion_tokens = await call_gemini(
                    message=message,
                    model=current_model,
                    chat_history=chat_history,
                    system_prompt=SYSTEM_PROMPT,
                    api_key=api_key
                )
            else:
                answer, prompt_tokens, completion_tokens = await call_openai_compatible(
                    provider=current_prov,
                    model=current_model,
                    message=message,
                    chat_history=chat_history,
                    system_prompt=SYSTEM_PROMPT,
                    api_key=api_key
                )
                
            elapsed_time_ms = int((time.time() - start_time) * 1000)
            
            # Save success log
            save_usage_log(
                db=db,
                user_id=user_id,
                provider=current_prov,
                model=current_model,
                status="success",
                response_time_ms=elapsed_time_ms,
                fallback_used=fallback_occurred,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            return {
                "answer": answer,
                "provider_used": current_prov,
                "model_used": current_model,
                "fallback_used": fallback_occurred,
                "failed_providers": failed_providers,
                "response_time_ms": elapsed_time_ms,
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            }
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            elapsed_time_ms = int((time.time() - start_time) * 1000)
            err_msg = f"HTTP {status_code}: {e.response.text}"
            
            print(f"[ERROR] Provider: {current_prov}, Model: {current_model}, StatusCode: {status_code}, Message: HTTP Status Error, RequestType: chat")
            save_usage_log(
                db=db,
                user_id=user_id,
                provider=current_prov,
                model=current_model,
                status="error",
                response_time_ms=elapsed_time_ms,
                fallback_used=fallback_occurred,
                error_message=err_msg
            )
            
            if status_code in [429, 500, 502, 503, 504]:
                # Fallback only for 429, 500, 502, 503, 504
                failed_providers.append(current_prov)
                if not fallback_enabled or i == len(providers_to_try) - 1:
                    raise HTTPException(status_code=status_code, detail=f"AI Provider Error ({current_prov}): {e.response.text}")
                fallback_occurred = True
            else:
                # Halt and raise immediately (Do NOT fallback on 400, 401, 403, 404, etc.)
                if current_prov == "groq" and status_code in [400, 404]:
                    detail_msg = "Bad request or wrong model name for Groq"
                    raise HTTPException(status_code=400, detail=detail_msg)
                else:
                    detail_msg = f"AI Provider Error ({current_prov}): {e.response.text}"
                    raise HTTPException(status_code=status_code, detail=detail_msg)
            
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            elapsed_time_ms = int((time.time() - start_time) * 1000)
            err_msg = f"Network Timeout/Connection Error: {str(e)}"
            
            print(f"[ERROR] Provider: {current_prov}, Model: {current_model}, StatusCode: 504, Message: {err_msg}, RequestType: chat")
            save_usage_log(
                db=db,
                user_id=user_id,
                provider=current_prov,
                model=current_model,
                status="error",
                response_time_ms=elapsed_time_ms,
                fallback_used=fallback_occurred,
                error_message=err_msg
            )
            
            failed_providers.append(current_prov)
            if not fallback_enabled or i == len(providers_to_try) - 1:
                raise HTTPException(status_code=504, detail=f"AI Provider Timeout ({current_prov})")
            fallback_occurred = True
            
        except Exception as e:
            # Catch safety blocks or parsing errors
            elapsed_time_ms = int((time.time() - start_time) * 1000)
            err_msg = str(e)
            
            print(f"[ERROR] Provider: {current_prov}, Model: {current_model}, StatusCode: 500, Message: {err_msg}, RequestType: chat")
            save_usage_log(
                db=db,
                user_id=user_id,
                provider=current_prov,
                model=current_model,
                status="error",
                response_time_ms=elapsed_time_ms,
                fallback_used=fallback_occurred,
                error_message=err_msg
            )
            
            # Safety Block shouldn't fallback
            if "Safety blocked" in err_msg:
                raise HTTPException(status_code=400, detail=f"Response blocked by AI safety filters ({current_prov})")
                
            failed_providers.append(current_prov)
            if not fallback_enabled or i == len(providers_to_try) - 1:
                raise HTTPException(status_code=500, detail=f"AI Provider Internal Error ({current_prov}): {err_msg}")
            fallback_occurred = True
            
    raise HTTPException(status_code=500, detail="All AI providers failed to respond.")
