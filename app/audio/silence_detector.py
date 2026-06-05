"""Funções auxiliares para identificar áudio vazio ou silencioso."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

DEFAULT_SILENCE_THRESHOLD = 0.01


@dataclass(frozen=True)
class SilenceAnalysis:
    """Resultado simples da análise de volume de um áudio."""

    duration_seconds: float
    rms_volume: float
    peak_volume: float
    is_probably_silent: bool


class SilenceDetectionError(RuntimeError):
    """Erro específico para falhas ao analisar silêncio em áudio."""


def calculate_rms_volume(audio_data: np.ndarray) -> float:
    """Calcula o volume RMS do áudio.

    O RMS resume a energia média do sinal e é mais estável do que olhar apenas
    para o pico. Isso ajuda a detectar gravações vazias sem interromper pausas
    normais de pensamento do estudante.
    """

    if audio_data.size == 0:
        return 0.0

    normalized_audio = audio_data.astype(np.float32)
    return float(np.sqrt(np.mean(np.square(normalized_audio))))


def calculate_peak_volume(audio_data: np.ndarray) -> float:
    """Calcula o maior volume absoluto encontrado no áudio."""

    if audio_data.size == 0:
        return 0.0

    normalized_audio = audio_data.astype(np.float32)
    return float(np.max(np.abs(normalized_audio)))


def analyze_audio_file(
    file_path: Path,
    *,
    silence_threshold: float = DEFAULT_SILENCE_THRESHOLD,
) -> SilenceAnalysis:
    """Analisa se um arquivo parece silencioso.

    Esta função não decide quando parar a gravação. Ela apenas ajuda a avisar
    quando o áudio salvo provavelmente está vazio, baixo demais ou sem fala útil.
    """

    if not file_path.exists():
        msg = f"Arquivo de áudio não encontrado para análise: {file_path}"
        raise SilenceDetectionError(msg)

    try:
        audio_data, sample_rate = sf.read(file_path, dtype="float32")
    except (OSError, RuntimeError) as exc:
        msg = f"Não foi possível ler o áudio para análise: {file_path}"
        raise SilenceDetectionError(msg) from exc

    duration_seconds = len(audio_data) / sample_rate
    rms_volume = calculate_rms_volume(audio_data)
    peak_volume = calculate_peak_volume(audio_data)

    return SilenceAnalysis(
        duration_seconds=duration_seconds,
        rms_volume=rms_volume,
        peak_volume=peak_volume,
        is_probably_silent=rms_volume < silence_threshold,
    )


def is_probably_silent(
    audio_data: np.ndarray,
    *,
    silence_threshold: float = DEFAULT_SILENCE_THRESHOLD,
) -> bool:
    """Indica se um array de áudio parece silêncio.

    A função fica separada para poder ser usada em testes e validações rápidas,
    sem depender de arquivo em disco.
    """

    return calculate_rms_volume(audio_data) < silence_threshold
