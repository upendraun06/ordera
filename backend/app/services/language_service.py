"""
Language Detection Service
==========================
Detects the customer's language from their first spoken utterance during a call.
Provides Telnyx TeXML voice and STT (speech-to-text) mappings per language.

Supported languages
-------------------
  en — English (default)
  es — Spanish (Español)
  zh — Chinese Mandarin (普通话)

How language detection works
-----------------------------
1. Chinese: presence of any CJK Unicode character (U+4E00–U+9FFF)
2. Spanish: 2+ known Spanish-only marker words, OR 1+ marker + "hola"
3. English: default fallback if neither rule triggers

Voice & STT mapping
--------------------
TTS voices are Amazon Polly Neural voices delivered via Telnyx TeXML <Say>.
STT language hints are BCP-47 tags passed to Telnyx TeXML <Gather>.
Both are looked up by 2-letter language code at call time.
"""
import re

# ── TTS voice mapping ─────────────────────────────────────────────────────────
# Amazon Polly Neural voices — delivered via Telnyx TeXML <Say voice="...">
# Docs: https://developers.telnyx.com/docs/voice/texml/say
VOICE_MAP = {
    "en": "Polly.Joanna",   # US English, Neural
    "es": "Polly.Lupe",     # US Spanish, Neural
    "zh": "Polly.Zhiyu",    # Chinese Mandarin, Neural
}

# ── STT language hints ────────────────────────────────────────────────────────
# BCP-47 language tags passed to Telnyx TeXML <Gather language="...">
# Improves transcription accuracy by telling the STT model what to expect.
STT_LANGUAGE_MAP = {
    "en": "en-US",
    "es": "es-419",   # Latin American Spanish (broader coverage than es-ES)
    "zh": "zh-CN",    # Simplified Chinese / Mandarin
}

# ── Spanish marker words ──────────────────────────────────────────────────────
# Words that reliably appear in Spanish but not English conversation.
# Two or more matches required to avoid false positives (e.g., "menu" is shared).
_SPANISH_MARKERS = {
    "hola", "quiero", "quisiera", "gracias", "buenos", "buenas", "noches",
    "tardes", "dias", "señor", "señora", "por", "favor", "llamar", "pedir",
    "ordenar", "cuánto", "cuanto", "dónde", "donde", "cómo", "como",
    "cuál", "cual", "menú", "número", "necesito",
}


def detect_language(text: str) -> str:
    """
    Detect the spoken language from a customer's first utterance.

    Called once per call on the first SpeechResult. The result is stored in
    Conversation.language_detected and reused for all subsequent turns.

    Args:
        text: The raw transcription of the customer's speech.

    Returns:
        'en', 'es', or 'zh'
    """
    # Chinese: any CJK ideograph = Mandarin
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"

    # Spanish: count distinct Spanish-only marker words
    words = set(re.findall(r"\b\w+\b", text.lower()))
    spanish_hits = words & _SPANISH_MARKERS
    if len(spanish_hits) >= 2 or ("hola" in words and len(spanish_hits) >= 1):
        return "es"

    # Default
    return "en"
