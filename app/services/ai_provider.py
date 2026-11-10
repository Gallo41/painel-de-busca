import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_CHAVE_ENV_PATH = r"C:\Projetos Soft\Painel\chave.env"


def load_ai_keys(chave_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Carrega chaves de API a partir de `C:\\Projetos Soft\\Painel\\chave.env` e variáveis de ambiente.
    Suporta o formato livre do arquivo chave.env (`key nvidia : nvapi-...`, `key open route : sk-or-v1-...`, etc.)
    sem jamais expor os segredos em logs ou respostas da API.
    """
    target_path = chave_path or os.environ.get("PAINEL_CHAVE_ENV_PATH") or DEFAULT_CHAVE_ENV_PATH
    raw_text = ""
    file_found = False

    if target_path and os.path.isfile(target_path):
        try:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
            file_found = True
        except OSError:
            file_found = False

    openrouter_keys: List[str] = []
    nvidia_keys: List[str] = []
    gemini_keys: List[str] = []

    for m in re.findall(r"sk-or-v1-[A-Za-z0-9_\-]+", raw_text):
        if m not in openrouter_keys:
            openrouter_keys.append(m)

    for m in re.findall(r"nvapi-[A-Za-z0-9_\-]+", raw_text):
        if m not in nvidia_keys:
            nvidia_keys.append(m)

    for m in re.findall(r"AIza[A-Za-z0-9_\-]+", raw_text):
        if m not in gemini_keys:
            gemini_keys.append(m)

    env_or = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if env_or and env_or not in openrouter_keys:
        openrouter_keys.insert(0, env_or)

    env_nv = (os.environ.get("NVIDIA_API_KEY") or "").strip()
    if env_nv and env_nv not in nvidia_keys:
        nvidia_keys.insert(0, env_nv)

    env_gem = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if env_gem and env_gem not in gemini_keys:
        gemini_keys.insert(0, env_gem)

    return {
        "file_found": file_found,
        "source_path": target_path,
        "openrouter_keys": openrouter_keys,
        "nvidia_keys": nvidia_keys,
        "gemini_keys": gemini_keys,
    }


def get_ai_status(chave_path: Optional[str] = None) -> Dict[str, Any]:
    """Retorna metadados seguros (sem expor chaves) sobre os provedores de IA carregados."""
    info = load_ai_keys(chave_path)
    providers: List[str] = []
    if info["gemini_keys"]:
        providers.append("Google Gemini")
    if info["openrouter_keys"]:
        providers.append(f"OpenRouter ({len(info['openrouter_keys'])} chaves)")
    if info["nvidia_keys"]:
        providers.append(f"NVIDIA NIM ({len(info['nvidia_keys'])} chave)")
    providers.append("Motor Comercial Especialista (Fallback Instantâneo)")

    return {
        "file_found": info["file_found"],
        "source_path": info["source_path"],
        "openrouter_count": len(info["openrouter_keys"]),
        "nvidia_count": len(info["nvidia_keys"]),
        "gemini_count": len(info["gemini_keys"]),
        "active_providers": providers,
        "ready": True,
    }


def _call_openai_compatible(
    url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout_sec: float,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_fields:
        payload.update(extra_fields)
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8090",
        "X-Title": "Painel de Busca - Agente Comercial",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="ignore"))
        choices = body.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
            if content and content.strip():
                return content.strip()
    return None


def _call_gemini_native(
    api_key: str,
    system_prompt: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout_sec: float,
) -> Optional[str]:
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    contents = []
    for m in messages:
        role = "model" if m.get("role") in ("assistant", "model") else "user"
        contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="ignore"))
        candidates = body.get("candidates") or []
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            texts = [p.get("text", "") for p in parts if p.get("text")]
            joined = "\n".join(texts).strip()
            if joined:
                return joined
    return None


def call_llm_chat(
    system_prompt: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 450,
    timeout_sec: float = 6.0,
    chave_path: Optional[str] = None,
) -> Tuple[Optional[str], str]:
    """
    Executa chamada em cascata nos provedores configurados em `chave.env` (Gemini -> OpenRouter -> NVIDIA NIM).
    Se `PAINEL_AI_OFFLINE=1` estiver ativo (ou se as APIs externas sofrerem timeout/limite),
    retorna `(None, 'specialist_engine')` para acionamento imediato do motor especialista local.
    """
    if os.environ.get("PAINEL_AI_OFFLINE") == "1":
        return None, "specialist_engine"

    keys = load_ai_keys(chave_path)
    full_messages: List[Dict[str, str]] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        role = "assistant" if m.get("role") in ("assistant", "model") else "user"
        full_messages.append({"role": role, "content": m.get("content", "")})

    # 1. Google Gemini direto se configurado
    for gkey in keys["gemini_keys"]:
        try:
            res = _call_gemini_native(gkey, system_prompt, messages, temperature, max_tokens, timeout_sec)
            if res:
                return res, "gemini:gemini-2.5-flash"
        except Exception:
            continue

    # 2. OpenRouter (modelos gratuitos validados em PT-BR com baixa latencia)
    or_candidates: List[Tuple[str, Optional[Dict[str, Any]]]] = [
        ("nvidia/nemotron-3.5-lightning:free", {"reasoning": {"effort": "none"}}),
        ("dots-studio/dots-3-note-preview:free", None),
        ("openrouter/free", {"reasoning": {"effort": "none"}}),
    ]
    for or_key in keys["openrouter_keys"][:1]:
        for model, extra in or_candidates:
            try:
                effective_tokens = max_tokens if extra else max(max_tokens, 450)
                res = _call_openai_compatible(
                    "https://openrouter.ai/api/v1/chat/completions",
                    or_key,
                    model,
                    full_messages,
                    temperature,
                    effective_tokens,
                    min(max(timeout_sec, 8.0), 10.0),
                    extra_fields=extra,
                )
                if res:
                    return res, f"openrouter:{model}"
            except Exception:
                continue

    # 3. NVIDIA NIM API (backup conversacional validado)
    nv_models = [
        "meta/llama-3.2-90b-vision-instruct",
    ]
    for nv_key in keys["nvidia_keys"][:1]:
        for model in nv_models:
            try:
                res = _call_openai_compatible(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    nv_key,
                    model,
                    full_messages,
                    temperature,
                    max(max_tokens, 900),
                    min(max(timeout_sec, 8.0), 12.0),
                )
                if res:
                    return res, f"nvidia:{model}"
            except Exception:
                continue

    return None, "specialist_engine"
