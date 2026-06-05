"""Configurações centrais do English Voice Coach AI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

DEFAULT_ENV_FILE: Final = ".env"
OPENAI_KEY_PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {"", "sua_chave_aqui", "sk-sua_chave_aqui"}
)
TRUE_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes", "y", "sim", "s"})
FALSE_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "no", "n", "nao", "não"})


class ConfigError(RuntimeError):
    """Erro específico para configurações ausentes ou inválidas."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Configurações carregadas do ambiente.

    A dataclass deixa as configurações explícitas e imutáveis. Isso evita que
    uma parte do programa altere valores globais sem querer durante a conversa.
    """

    openai_api_key: str
    app_language: str
    coach_level: str
    sample_rate: int
    silence_threshold: float
    silence_duration_ms: int
    recording_mode: str
    max_recording_seconds: int
    conversation_context_limit: int
    transcription_model: str
    transcription_language: str
    coach_model: str
    enable_tts: bool
    tts_model: str
    voice_name: str
    db_path: Path
    audio_temp_dir: Path


def _read_env(name: str, default: str = "") -> str:
    """Lê uma variável de ambiente removendo espaços acidentais."""

    return os.getenv(name, default).strip()


def _read_int(name: str, default: int) -> int:
    """Lê um inteiro do ambiente com mensagem clara em caso de erro."""

    raw_value = _read_env(name, str(default))

    try:
        return int(raw_value)
    except ValueError as exc:
        msg = f"A variável {name} deve ser um número inteiro. Valor recebido: {raw_value!r}."
        raise ConfigError(msg) from exc


def _read_float(name: str, default: float) -> float:
    """Lê um número decimal do ambiente com validação simples."""

    raw_value = _read_env(name, str(default))

    try:
        return float(raw_value)
    except ValueError as exc:
        msg = f"A variável {name} deve ser um número decimal. Valor recebido: {raw_value!r}."
        raise ConfigError(msg) from exc


def _read_bool(name: str, default: bool) -> bool:
    """Lê booleanos do `.env` aceitando português e inglês.

    Essa função evita bugs comuns com variáveis de ambiente, porque todo valor
    lido do `.env` chega como texto. Sem conversão explícita, a string "false"
    ainda seria tratada como verdadeira em Python.
    """

    default_as_text = "true" if default else "false"
    raw_value = _read_env(name, default_as_text).lower()

    if raw_value in TRUE_VALUES:
        return True

    if raw_value in FALSE_VALUES:
        return False

    msg = (
        f"A variável {name} deve ser booleana. Use true/false ou sim/nao. "
        f"Valor recebido: {raw_value!r}."
    )
    raise ConfigError(msg)


def validate_openai_api_key(api_key: str) -> None:
    """Garante que a chave da OpenAI não ficou vazia nem com placeholder.

    A validação não tenta adivinhar todos os formatos possíveis de chave. Ela
    apenas impede os erros mais comuns nesta fase: esquecer o `.env` ou deixar
    `sua_chave_aqui` no arquivo real.
    """

    if api_key.strip() in OPENAI_KEY_PLACEHOLDERS:
        msg = (
            "OPENAI_API_KEY não foi configurada. Crie um arquivo .env a partir "
            "do .env.example e preencha sua chave real da OpenAI."
        )
        raise ConfigError(msg)


@lru_cache
def get_settings(
    *,
    require_openai_key: bool = False,
    env_file: str = DEFAULT_ENV_FILE,
) -> AppSettings:
    """Carrega as configurações do `.env` e expõe um objeto único para o app.

    O cache evita reler o arquivo em todo ciclo da conversa. O parâmetro
    `require_openai_key` permite validar a chave apenas quando uma etapa que usa
    a API realmente precisar dela.
    """

    load_dotenv(env_file)

    settings = AppSettings(
        openai_api_key=_read_env("OPENAI_API_KEY"),
        app_language=_read_env("APP_LANGUAGE", "pt-BR"),
        coach_level=_read_env("COACH_LEVEL", "intermediate"),
        sample_rate=_read_int("SAMPLE_RATE", 16000),
        silence_threshold=_read_float("SILENCE_THRESHOLD", 0.01),
        silence_duration_ms=_read_int("SILENCE_DURATION_MS", 1500),
        recording_mode=_read_env("RECORDING_MODE", "manual_enter"),
        max_recording_seconds=_read_int("MAX_RECORDING_SECONDS", 120),
        conversation_context_limit=_read_int("CONVERSATION_CONTEXT_LIMIT", 6),
        transcription_model=_read_env(
            "TRANSCRIPTION_MODEL",
            "gpt-4o-mini-transcribe",
        ),
        transcription_language=_read_env("TRANSCRIPTION_LANGUAGE", "en"),
        coach_model=_read_env("COACH_MODEL", "gpt-4.1-mini"),
        enable_tts=_read_bool("ENABLE_TTS", False),
        tts_model=_read_env("TTS_MODEL", "gpt-4o-mini-tts"),
        voice_name=_read_env("VOICE_NAME", "alloy"),
        db_path=Path(_read_env("DB_PATH", "data/conversations.db")),
        audio_temp_dir=Path(_read_env("AUDIO_TEMP_DIR", "data/audio")),
    )

    if require_openai_key:
        validate_openai_api_key(settings.openai_api_key)

    return settings
