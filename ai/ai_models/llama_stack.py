from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx


def _normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/v1"):
        normalized = f"{normalized}/v1"
    return normalized


def _extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message")
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = first_choice.get("text", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        return "".join(text_parts).strip()

    return str(content).strip()


@dataclass(slots=True)
class LlamaStackSettings:
    base_url: str | None
    default_model: str | None
    api_key: str | None
    timeout_seconds: float

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.default_model)


@dataclass(slots=True)
class LocalGenerationSettings:
    base_model_id: str | None
    adapter_path: str | None
    backend: str
    device_map: str
    hf_token: str | None
    trust_remote_code: bool
    load_in_4bit: bool

    @property
    def configured(self) -> bool:
        return bool(self.base_model_id)


def load_llama_stack_settings() -> LlamaStackSettings:
    timeout_raw = os.getenv("LLAMA_STACK_TIMEOUT_SECONDS", "30")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 30.0

    return LlamaStackSettings(
        base_url=_normalize_base_url(os.getenv("LLAMA_STACK_BASE_URL")),
        default_model=os.getenv("LLAMA_STACK_MODEL"),
        api_key=os.getenv("LLAMA_STACK_API_KEY"),
        timeout_seconds=timeout_seconds,
    )


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_local_generation_settings() -> LocalGenerationSettings:
    return LocalGenerationSettings(
        base_model_id=os.getenv("ORCA_BASE_MODEL_ID") or os.getenv("HF_MODEL_ID"),
        adapter_path=os.getenv("ORCA_LORA_ADAPTER_PATH"),
        backend=os.getenv("ORCA_LLM_BACKEND", "auto").strip().lower() or "auto",
        device_map=os.getenv("ORCA_DEVICE_MAP", "auto"),
        hf_token=os.getenv("HUGGINGFACE_HUB_TOKEN") or os.getenv("HF_TOKEN"),
        trust_remote_code=_parse_bool(os.getenv("ORCA_TRUST_REMOTE_CODE"), default=False),
        load_in_4bit=_parse_bool(os.getenv("ORCA_LOAD_IN_4BIT"), default=False),
    )


def _build_headers(settings: LlamaStackSettings) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    return headers


def _resolve_backend(requested_backend: str | None = None) -> tuple[str, LlamaStackSettings, LocalGenerationSettings]:
    remote_settings = load_llama_stack_settings()
    local_settings = load_local_generation_settings()
    backend = (requested_backend or local_settings.backend or "auto").strip().lower()

    if backend in {"remote", "llama-stack"}:
        if not remote_settings.configured:
            raise RuntimeError(
                "LLAMA_STACK_BASE_URL and LLAMA_STACK_MODEL must be set for remote inference."
            )
        return "llama-stack", remote_settings, local_settings

    if backend in {"local", "local-lora", "merged-local"}:
        if not local_settings.configured:
            raise RuntimeError(
                "ORCA_BASE_MODEL_ID must be set for local or LoRA-merged inference."
            )
        return backend, remote_settings, local_settings

    if remote_settings.configured:
        return "llama-stack", remote_settings, local_settings

    if local_settings.configured:
        if local_settings.adapter_path:
            return "local-lora", remote_settings, local_settings
        return "local", remote_settings, local_settings

    raise RuntimeError(
        "LLAMA_STACK_BASE_URL and LLAMA_STACK_MODEL must be set for remote inference, or ORCA_BASE_MODEL_ID must be set for local inference."
    )


def _validate_adapter_path(adapter_path: str | None) -> str | None:
    if not adapter_path:
        return None

    path = Path(adapter_path).expanduser()
    if not path.exists():
        raise RuntimeError(f"LoRA adapter path does not exist: {path}")
    return str(path)


def _build_local_model_id(base_model_id: str, adapter_path: str | None, merge_lora: bool) -> str:
    if not adapter_path:
        return base_model_id
    adapter_name = Path(adapter_path).name
    suffix = "merged" if merge_lora else "adapter"
    return f"{base_model_id}+{adapter_name}:{suffix}"


@lru_cache(maxsize=4)
def _get_local_generator(
    base_model_id: str,
    adapter_path: str | None,
    merge_lora: bool,
    load_in_4bit: bool,
    device_map: str,
    trust_remote_code: bool,
    hf_token: str | None,
):
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Local inference requires transformers and torch to be installed."
        ) from exc

    quantization_config = None
    if load_in_4bit:
        try:
            from transformers import BitsAndBytesConfig
        except ImportError as exc:
            raise RuntimeError(
                "QLoRA/local 4-bit inference requires transformers with BitsAndBytesConfig support."
            ) from exc
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

    tokenizer = AutoTokenizer.from_pretrained(
        base_model_id,
        token=hf_token,
        trust_remote_code=trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        token=hf_token,
        trust_remote_code=trust_remote_code,
        device_map=device_map,
        torch_dtype=torch.float16,
        quantization_config=quantization_config,
    )

    if adapter_path:
        try:
            from peft import PeftModel
        except ImportError as exc:
            raise RuntimeError("LoRA inference requires the peft package.") from exc

        model = PeftModel.from_pretrained(model, adapter_path)
        if merge_lora:
            model = model.merge_and_unload()

    model.eval()
    return tokenizer, model


def _format_prompt(prompt: str, system_prompt: str | None) -> str:
    if system_prompt:
        return f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"
    return f"<|user|>\n{prompt}\n<|assistant|>\n"


def _generate_text_locally(
    prompt: str,
    *,
    system_prompt: str | None,
    model: str | None,
    temperature: float,
    max_tokens: int,
    adapter_path: str | None,
    merge_lora: bool,
) -> dict[str, object]:
    settings = load_local_generation_settings()
    base_model_id = model or settings.base_model_id
    if not base_model_id:
        raise RuntimeError("ORCA_BASE_MODEL_ID must be set for local inference.")

    normalized_adapter = _validate_adapter_path(adapter_path or settings.adapter_path)
    tokenizer, loaded_model = _get_local_generator(
        base_model_id,
        normalized_adapter,
        merge_lora,
        settings.load_in_4bit,
        settings.device_map,
        settings.trust_remote_code,
        settings.hf_token,
    )

    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("Local inference requires torch to be installed.") from exc

    rendered_prompt = _format_prompt(prompt, system_prompt)
    encoded = tokenizer(rendered_prompt, return_tensors="pt")
    if hasattr(loaded_model, "device"):
        encoded = {key: value.to(loaded_model.device) for key, value in encoded.items()}

    with torch.inference_mode():
        output = loaded_model.generate(
            **encoded,
            do_sample=temperature > 0,
            temperature=max(temperature, 1e-5),
            max_new_tokens=max_tokens,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_tokens = output[0][encoded["input_ids"].shape[-1] :]
    text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    provider = "local-peft-merged" if merge_lora and normalized_adapter else "local-transformers"

    return {
        "model": _build_local_model_id(base_model_id, normalized_adapter, merge_lora),
        "provider": provider,
        "text": text,
        "raw": {
            "backend": provider,
            "prompt": rendered_prompt,
            "adapter_path": normalized_adapter,
        },
    }


async def list_models() -> dict[str, object]:
    settings = load_llama_stack_settings()
    local_settings = load_local_generation_settings()
    if not settings.configured and not local_settings.configured:
        return {
            "service": "ai-models",
            "provider": "llama-stack",
            "configured": False,
            "models": [],
            "default_model": settings.default_model,
        }

    backend, settings, local_settings = _resolve_backend(None)
    if backend == "llama-stack":
        assert settings.base_url is not None
        async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
            response = await client.get(
                f"{settings.base_url}/models",
                headers=_build_headers(settings),
            )
            response.raise_for_status()
            payload = response.json()

        items = payload.get("data", []) if isinstance(payload, dict) else []
        model_ids = [
            item.get("id")
            for item in items
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]

        return {
            "service": "ai-models",
            "provider": "llama-stack",
            "configured": True,
            "default_model": settings.default_model,
            "models": model_ids,
        }

    return {
        "service": "ai-models",
        "provider": "local-transformers",
        "configured": True,
        "default_model": local_settings.base_model_id,
        "models": [
            _build_local_model_id(
                local_settings.base_model_id,
                _validate_adapter_path(local_settings.adapter_path),
                backend == "merged-local",
            )
        ],
    }


async def generate_text(
    prompt: str,
    *,
    system_prompt: str | None,
    model: str | None,
    temperature: float,
    max_tokens: int,
    backend: str | None = None,
    adapter_path: str | None = None,
    merge_lora: bool = False,
) -> dict[str, object]:
    selected_backend, settings, local_settings = _resolve_backend(backend)
    if selected_backend != "llama-stack":
        use_merged_lora = merge_lora or selected_backend == "merged-local"
        return _generate_text_locally(
            prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            adapter_path=adapter_path or local_settings.adapter_path,
            merge_lora=use_merged_lora,
        )

    assert settings.base_url is not None
    selected_model = model or settings.default_model
    assert selected_model is not None

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
        response = await client.post(
            f"{settings.base_url}/chat/completions",
            headers=_build_headers(settings),
            json={
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        payload = response.json()

    return {
        "model": selected_model,
        "provider": "llama-stack",
        "text": _extract_text(payload),
        "raw": payload,
    }