from faster_whisper import WhisperModel
from transformers import pipeline as hf_pipeline
import numpy as np
import tempfile
import logging
import io

logger = logging.getLogger(__name__)

_whisper_model    = None
_tone_classifier  = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model (base)...")
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Whisper loaded.")
    return _whisper_model


def _get_tone_classifier():
    global _tone_classifier
    if _tone_classifier is None:
        logger.info("Loading audio tone classifier...")
        _tone_classifier = hf_pipeline(
            "audio-classification",
            model="superb/wav2vec2-base-superb-er",  # emotion recognition
        )
        logger.info("Tone classifier loaded.")
    return _tone_classifier


# Tone mapping
TONE_BIAS = {
    "hap": {"occasions": ["casual", "party"], "styles": ["bold", "colorful"]},    # happy
    "ang": {"occasions": ["party"],            "styles": ["edgy", "statement"]},   # angry/energetic
    "sad": {"occasions": ["casual"],           "styles": ["minimalist", "cozy"]},  # sad/low energy
    "neu": {},                                                                      # neutral — no bias
}


async def transcribe_audio(audio_bytes: bytes) -> dict:
    # Write to temp file for Whisper
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Step 1: Transcribe
        whisper = _get_whisper()
        segments, info = whisper.transcribe(tmp_path, beam_size=5)
        transcript = " ".join(seg.text.strip() for seg in segments).strip()
        logger.info(f"Transcribed: '{transcript}' (lang: {info.language})")

        # Step 2: Tone detection
        tone = "neu"
        bias = {}
        try:
            clf    = _get_tone_classifier()
            result = clf(tmp_path)
            top_emotion = result[0]["label"].lower()[:3]
            tone = top_emotion if top_emotion in TONE_BIAS else "neu"
            bias = TONE_BIAS.get(tone, {})
            logger.info(f"Detected tone: {tone}, bias: {bias}")
        except Exception as e:
            logger.warning(f"Tone detection failed (non-critical): {e}")

        return {
            "text": transcript,
            "tone": tone,
            "bias": bias,
            "language": info.language,
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"text": "", "tone": "neu", "bias": {}, "language": "en"}

    finally:
        import os
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
