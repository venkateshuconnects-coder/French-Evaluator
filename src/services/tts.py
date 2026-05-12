"""Text-to-Speech (TTS) using edge-tts."""

import asyncio
import edge_tts
from src.config import TTS_VOICE, TTS_RATE


def synthesize_tts(text, voice=TTS_VOICE, rate=TTS_RATE, output_path=None):
    """
    Synthesize speech from text using edge-tts.
    Args:
        text: Text to synthesize
        voice: Voice name (default: French female)
        rate: Speaking rate (default: 1.0)
        output_path: Path to save audio file (optional)
    Returns:
        Path to generated audio file
    """

    async def _synthesize():
        communicate = edge_tts.Communicate(text, voice=voice, rate=f"{rate}")
        if output_path:
            await communicate.save(output_path)
            return output_path
        else:
            # Save to temp file
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                await communicate.save(f.name)
                return f.name

    return asyncio.run(_synthesize())
