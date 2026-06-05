"""Gravação de áudio controlada manualmente pelo usuário."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Final

import numpy as np
import sounddevice as sd
import soundfile as sf

DEFAULT_CHANNELS: Final = 1
DEFAULT_SUBTYPE: Final = "PCM_16"
MIN_RECORD_SECONDS: Final = 0.3


class AudioRecordingError(RuntimeError):
    """Erro específico para falhas durante a gravação de áudio."""


def build_audio_file_path(audio_dir: Path, prefix: str = "user") -> Path:
    """Cria um caminho único para salvar a fala do usuário em WAV.

    O timestamp evita sobrescrever gravações anteriores e facilita encontrar
    o áudio correspondente a uma conversa quando o histórico for salvo no SQLite.
    """

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return audio_dir / f"{prefix}-{timestamp}.wav"


def _merge_audio_chunks(chunks: list[np.ndarray]) -> np.ndarray:
    """Une os blocos capturados pelo microfone em um único array de áudio."""

    if not chunks:
        msg = "Nenhum áudio foi capturado pelo microfone."
        raise AudioRecordingError(msg)

    audio_data = np.concatenate(chunks, axis=0)

    if audio_data.size == 0:
        msg = "O áudio capturado está vazio."
        raise AudioRecordingError(msg)

    return audio_data


def record_until_enter(
    audio_dir: Path,
    sample_rate: int,
    *,
    channels: int = DEFAULT_CHANNELS,
    start_message: str = "Pressione Enter para começar a gravar.",
    stop_message: str = "Gravando... pressione Enter novamente quando terminar de falar.",
) -> Path:
    """Grava áudio até o usuário pressionar Enter pela segunda vez.

    A gravação manual é a estratégia principal do projeto porque o estudante
    precisa de tempo para pensar em inglês. O detector de silêncio será usado
    apenas como apoio, e não como gatilho automático para interromper a fala.
    """

    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = build_audio_file_path(audio_dir)
    chunks: list[np.ndarray] = []
    stream_warnings: list[str] = []

    input(f"{start_message}\n")

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="float32",
            callback=lambda indata, _frames, _time, status: _capture_chunk(
                indata,
                status,
                chunks,
                stream_warnings,
            ),
        ):
            input(f"{stop_message}\n")
    except KeyboardInterrupt as exc:
        msg = "Gravação cancelada pelo usuário."
        raise AudioRecordingError(msg) from exc
    except (OSError, sd.PortAudioError) as exc:
        msg = (
            "Não foi possível acessar o microfone. "
            "Verifique se ele está conectado e se o sistema permitiu o uso."
        )
        raise AudioRecordingError(msg) from exc

    audio_data = _merge_audio_chunks(chunks)
    duration_seconds = len(audio_data) / sample_rate

    if duration_seconds < MIN_RECORD_SECONDS:
        msg = "A gravação ficou curta demais para ser transcrita com segurança."
        raise AudioRecordingError(msg)

    try:
        sf.write(output_path, audio_data, sample_rate, subtype=DEFAULT_SUBTYPE)
    except (OSError, RuntimeError) as exc:
        msg = f"Não foi possível salvar o áudio em: {output_path}"
        raise AudioRecordingError(msg) from exc

    if stream_warnings:
        # As mensagens do PortAudio não impedem necessariamente a gravação,
        # mas ajudam a diagnosticar cortes, lentidão ou problemas de dispositivo.
        warnings_text = "; ".join(stream_warnings)
        print(f"Avisos durante a gravação: {warnings_text}")

    return output_path


def _capture_chunk(
    indata: np.ndarray,
    status: sd.CallbackFlags,
    chunks: list[np.ndarray],
    stream_warnings: list[str],
) -> None:
    """Guarda um bloco de áudio recebido pelo callback do sounddevice.

    O callback precisa ser pequeno e rápido. Por isso, ele apenas copia o bloco
    atual e registra avisos. Qualquer validação mais pesada fica fora do callback.
    """

    if status:
        stream_warnings.append(str(status))

    chunks.append(indata.copy())
