import os
import time
import httpx
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
from backend.models import AIUsageLog
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

# Priority Chain
PRIORITY_CHAIN = ["gemini", "groq", "openrouter", "cerebras", "mistral"]

SYSTEM_PROMPT = (
    "You are a secure personal AI assistant. You must answer only using the logged-in user's own data "
    "and allowed context. Never reveal, guess, or use another user's data. If the user asks about "
    "another user or unrelated private data, politely refuse."
)

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
        "messages": messages
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, headers=headers, json=payload, timeout=timeout)
        
        # Check non-retryable status codes
        if response.status_code in [401, 403]:
            raise httpx.HTTPStatusError("Invalid API key or Authentication error", request=response.request, response=response)
        if response.status_code == 400:
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

async def ask_ai(message: str, user_id: int, provider: str = "auto", model: str = "auto", chat_history: List[Dict[str, str]] = None, fallback_enabled: bool = True, db: Session = None) -> Dict[str, Any]:
    if chat_history is None:
        chat_history = []
        
    start_provider = provider.lower()
    
    # Build the list of providers to try based on priority chain
    if start_provider == "auto" or start_provider not in PRIORITY_CHAIN:
        providers_to_try = PRIORITY_CHAIN.copy()
    else:
        # If user specifies a starting provider, try it first.
        # If fallback is enabled, we append subsequent providers from the priority chain.
        idx = PRIORITY_CHAIN.index(start_provider)
        if fallback_enabled:
            providers_to_try = PRIORITY_CHAIN[idx:]
        else:
            providers_to_try = [start_provider]
            
    failed_providers = []
    fallback_occurred = False
    
    for i, current_prov in enumerate(providers_to_try):
        current_model = model if (model != "auto" and i == 0) else DEFAULT_MODELS[current_prov]
        api_key = API_KEYS.get(current_prov)
        
        # Check if API key is present
        if not api_key:
            err_msg = f"API key for {current_prov} not found in environment."
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
            if not fallback_enabled:
                raise HTTPException(status_code=500, detail=err_msg)
            fallback_occurred = True
            continue
            
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
            # 401, 403, 400 are non-retryable
            status_code = e.response.status_code
            elapsed_time_ms = int((time.time() - start_time) * 1000)
            err_msg = f"HTTP {status_code}: {e.response.text}"
            
            # Log error
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
            
            if status_code in [400, 401, 403]:
                # Halt and raise immediately (Do NOT fallback on auth errors or bad requests)
                raise HTTPException(status_code=status_code, detail=f"AI Provider Error ({current_prov}): {e.response.text}")
            
            # For 429, 5xx, or other HTTP errors: log and fallback
            failed_providers.append(current_prov)
            if not fallback_enabled or i == len(providers_to_try) - 1:
                raise HTTPException(status_code=status_code, detail=f"AI Provider Error ({current_prov}): {e.response.text}")
            fallback_occurred = True
            
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            elapsed_time_ms = int((time.time() - start_time) * 1000)
            err_msg = f"Network Timeout/Connection Error: {str(e)}"
            
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
