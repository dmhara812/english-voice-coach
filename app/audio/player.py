"""Reprodução de arquivos de áudio no computador do usuário."""

from __future__ import annotations

from pathlib import Path

import sounddevice as sd
import soundfile as sf


class AudioPlaybackError(RuntimeError):
    """Erro específico para falhas durante a reprodução de áudio."""


def play_audio_file(file_path: Path) -> None:
    """Reproduz um arquivo de áudio local usando o dispositivo padrão do sistema.

    Este módulo será usado primeiro para validar gravações locais e depois para
    tocar a resposta gerada por TTS. Centralizar a reprodução facilita tratar
    erros de saída de áudio em um único lugar.
    """

    if not file_path.exists():
        msg = f"Arquivo de áudio não encontrado: {file_path}"
        raise AudioPlaybackError(msg)

    try:
        audio_data, sample_rate = sf.read(file_path, dtype="float32")
        sd.play(audio_data, sample_rate)
        sd.wait()
    except (OSError, RuntimeError, sd.PortAudioError) as exc:
        msg = (
            "Não foi possível reproduzir o áudio. "
            "Verifique o dispositivo de saída do computador."
        )
        raise AudioPlaybackError(msg) from exc
    
