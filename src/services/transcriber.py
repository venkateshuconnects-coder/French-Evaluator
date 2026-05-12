"""Speech-to-text transcription using faster-whisper."""

import os
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel
from src.config import WHISPER_MODEL_SIZE, WHISPER_DEVICE


class WhisperTranscriber:
    """Handles speech-to-text transcription using faster-whisper."""

    def __init__(self, model_size=WHISPER_MODEL_SIZE):
        """Initialize Whisper model."""
        compute_type = "int8" if WHISPER_DEVICE == "cpu" else "float16"
        self.model = WhisperModel(
            model_size, device=WHISPER_DEVICE, compute_type=compute_type
        )
        self.model_size = model_size

    def _save_audio_bytes(self, audio_bytes, suffix=".wav"):
        """Save raw audio bytes to a temporary file and return the path."""
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_file.write(audio_bytes)
        tmp_file.flush()
        tmp_file.close()
        return tmp_file.name

    def transcribe(self, audio_bytes, language="fr"):
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Audio data as bytes
            language: Language code (default: 'fr' for French)

        Returns:
            dict with 'text', 'language', and 'segments' keys
        """
        file_path = None
        try:
            file_path = self._save_audio_bytes(audio_bytes)
            segments, _ = self.model.transcribe(file_path, language=language)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return {
                "text": text,
                "language": language,
                "segments": [
                    {"start": segment.start, "end": segment.end, "text": segment.text}
                    for segment in segments
                ],
            }
        except Exception as e:
            return {"text": "", "error": str(e), "language": language}
        finally:
            if file_path and Path(file_path).exists():
                try:
                    os.unlink(file_path)
                except OSError:
                    pass

    def get_word_timestamps(self, audio_bytes, language="fr"):
        """
        Get word-level timestamps from transcription.

        Args:
            audio_bytes: Audio data as bytes
            language: Language code

        Returns:
            list of word segments with timestamps
        """
        file_path = None
        try:
            file_path = self._save_audio_bytes(audio_bytes)
            segments, _ = self.model.transcribe(file_path, language=language)
            words = []
            for segment in segments:
                words.append(
                    {"start": segment.start, "end": segment.end, "text": segment.text}
                )
            return words
        finally:
            if file_path and Path(file_path).exists():
                try:
                    os.unlink(file_path)
                except OSError:
                    pass
