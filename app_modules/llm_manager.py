# llm_manager.py - Dynamic Multi-Provider LLM Manager for Free Tiers
import streamlit as st
import requests
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading

# ============================================
# 1. PROVIDER CONFIGURATIONS (All Free Tiers)
# ============================================

@dataclass
class ProviderConfig:
    name: str
    api_url: str
    model_name: str
    auth_type: str  # "bearer", "api_key", "x-api-key"
    rate_limit_per_minute: int
    daily_limit: int
    weight: int = 1  # For load balancing (higher = more requests)
    timeout: int = 30

PROVIDERS = {
    "openrouter": ProviderConfig(
        name="openrouter",
        api_url="https://openrouter.ai/api/v1/chat/completions",
        model_name="google/gemini-2.0-flash-exp:free",
        auth_type="bearer",
        rate_limit_per_minute=60,
        daily_limit=1500,
        weight=3
    ),
    "gemini_free": ProviderConfig(
        name="gemini_free",
        api_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
        model_name="gemini-pro",
        auth_type="api_key",
        rate_limit_per_minute=60,
        daily_limit=1500,
        weight=2
    ),
    "groq_free": ProviderConfig(
        name="groq_free",
        api_url="https://api.groq.com/openai/v1/chat/completions",
        model_name="mixtral-8x7b-32768",
        auth_type="bearer",
        rate_limit_per_minute=30,
        daily_limit=1000,
        weight=1
    ),
    "ollama": ProviderConfig(
        name="ollama",
        api_url="http://localhost:11434/v1/chat/completions",
        model_name="llama3",
        auth_type="none",
        rate_limit_per_minute=100,  # High as it's local
        daily_limit=99999,
        weight=4,
        timeout=5  # Low timeout for local to fail fast
    ),
    "huggingface": ProviderConfig(
        name="huggingface",
        api_url="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
        model_name="mistral-7b",
        auth_type="bearer",
        rate_limit_per_minute=10,
        daily_limit=1000,
        weight=1
    )
}

# ============================================
# 2. KEY & LOAD BALANCING LOGIC
# ============================================

class APIKeyManager:
    def __init__(self):
        self.keys: Dict[str, List[Dict]] = defaultdict(list)
        self._last_reset_date = datetime.now().date()
        self.load_keys_from_secrets()
    
    def load_keys_from_secrets(self):
        # Dynamically load from st.secrets if they exist
        for provider_key in ["OPENROUTER_KEYS", "GEMINI_KEYS", "GROQ_KEYS", "HF_KEYS"]:
            provider_id = provider_key.replace("_KEYS", "").lower()
            if "gemini" in provider_id: provider_id = "gemini_free"
            elif "groq" in provider_id: provider_id = "groq_free"
            elif "hf" in provider_id: provider_id = "huggingface"
            
            keys = st.secrets.get(provider_key, [])
            if isinstance(keys, str):
                keys = [keys]
            for key in keys:
                self.add_key(provider_id, key)
        
        # Add Ollama if reachable
        if self._check_ollama_alive():
            self.add_key("ollama", "local_no_key")

    def _check_ollama_alive(self) -> bool:
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=1)
            return resp.status_code == 200
        except:
            return False

    def get_local_models(self) -> List[str]:
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [m["name"] for m in models]
        except:
            pass
        return []

    def add_key(self, provider: str, api_key: str):
        self.keys[provider].append({
            "key": api_key,
            "usage_today": 0,
            "rate_limit_reset": time.time(),
            "requests_this_minute": 0,
            "healthy": True
        })
    
    def get_next_key(self, provider: str) -> Optional[Tuple[str, Dict]]:
        if provider not in self.keys: return None
        now = time.time()
        for key in self.keys[provider]:
            if key["healthy"] and key["requests_this_minute"] < PROVIDERS[provider].rate_limit_per_minute:
                key["requests_this_minute"] += 1
                key["usage_today"] += 1
                return key["key"], key
        return None

class AdaptiveLoadBalancer:
    def __init__(self):
        self.provider_stats = defaultdict(lambda: {"success_rate": 1.0, "avg_latency": 1.0})
    
    def select_provider(self, available_providers: List[str]) -> str:
        if not available_providers: return "openrouter"
        scores = {p: PROVIDERS[p].weight * self.provider_stats[p]["success_rate"] for p in available_providers}
        return max(scores, key=scores.get)

    def record_result(self, provider: str, success: bool, latency: float):
        stats = self.provider_stats[provider]
        alpha = 0.1
        stats["success_rate"] = alpha * (1.0 if success else 0.0) + (1 - alpha) * stats["success_rate"]
        stats["avg_latency"] = alpha * latency + (1 - alpha) * stats["avg_latency"]

# ============================================
# 3. CONTROLLER
# ============================================

class DynamicLLMController:
    def __init__(self):
        self.key_manager = APIKeyManager()
        self.load_balancer = AdaptiveLoadBalancer()

    async def _call_provider_async(self, provider: str, api_key: str, prompt: str, context: str) -> Tuple[Optional[str], float]:
        config = PROVIDERS[provider]
        start_time = time.time()
        
        if provider == "gemini_free":
            payload = {"contents": [{"parts": [{"text": f"Context: {context}\n\nUser: {prompt}"}]}]}
            headers = {"x-goog-api-key": api_key}
            full_url = f"{config.api_url}?key={api_key}"
        elif provider == "huggingface":
            payload = {
                "inputs": f"Context: {context}\n\nUser: {prompt}",
                "parameters": {"max_new_tokens": 500, "return_full_text": False}
            }
            headers = {"Authorization": f"Bearer {api_key}"}
            full_url = config.api_url
        else:
            # OpenAI compatible (OpenRouter, Groq, Ollama)
            payload = {
                "model": config.model_name,
                "messages": [
                    {"role": "system", "content": f"You are a retail fashion BI assistant. Context: {context}"},
                    {"role": "user", "content": prompt}
                ]
            }
            headers = {}
            if config.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {api_key}"
            elif config.auth_type == "api_key":
                headers["x-api-key"] = api_key
            
            full_url = config.api_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(full_url, json=payload, headers=headers, timeout=config.timeout) as response:
                    latency = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        if provider == "gemini_free":
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                        elif provider == "huggingface":
                            text = data[0]["generated_text"] if isinstance(data, list) else data["generated_text"]
                        else:
                            text = data["choices"][0]["message"]["content"]
                        return text, latency
                    return None, latency
        except Exception:
            return None, 1.0

    async def get_response_async(self, prompt: str, context: str) -> str:
        available_providers = [p for p in PROVIDERS.keys() if p in self.key_manager.keys]
        if not available_providers: return ""
        
        for _ in range(len(available_providers) * 2):
            selected = self.load_balancer.select_provider(available_providers)
            key_res = self.key_manager.get_next_key(selected)
            if not key_res: continue
            
            api_key, _ = key_res
            response, latency = await self._call_provider_async(selected, api_key, prompt, context)
            if response:
                self.load_balancer.record_result(selected, True, latency)
                return response
            self.load_balancer.record_result(selected, False, latency)
        return ""

    def get_response_sync(self, prompt: str, context: str) -> str:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.get_response_async(prompt, context))

def init_llm_controller():
    # Safety: Re-initialize if the stored object is from an old class definition
    if "llm_controller" in st.session_state:
        if not hasattr(st.session_state.llm_controller.key_manager, "get_local_models"):
            del st.session_state.llm_controller
            
    if "llm_controller" not in st.session_state:
        st.session_state.llm_controller = DynamicLLMController()
    return st.session_state.llm_controller
