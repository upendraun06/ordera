"""
Telnyx TeXML Service
====================
Generates Telnyx TeXML (XML) responses that control inbound phone call flow.

What is TeXML?
--------------
TeXML is Telnyx's XML-based call control language, similar to Twilio TwiML.
When Telnyx calls one of our webhooks, we respond with a TeXML document that
tells Telnyx what to do next: speak text, listen for speech, or hang up.

Call flow in Ringa
-------------------
  POST /voice/incoming  →  txml_gather(greeting)
                              ↓  customer speaks
  POST /voice/respond   →  txml_gather(ai_reply)   (loops until order complete)
                              ↓  order confirmed
  POST /voice/respond   →  txml_say_hangup(confirmation)

Key TeXML elements used
-----------------------
  <Gather input="speech">  Listen for customer speech; POST transcription to action_url
  <Say voice="...">        Speak text via TTS (Amazon Polly Neural voices)
  <Hangup/>                End the call

Telnyx TeXML docs: https://developers.telnyx.com/docs/voice/texml
"""

# Spoken when no customer speech is detected within the timeout window.
# One message per supported language (matched by language_service.detect_language).
_TIMEOUT_MESSAGES = {
    "en": "I didn't hear anything. Please call back if you need help. Goodbye!",
    "es": "No escuché nada. Por favor llame de nuevo si necesita ayuda. ¡Adiós!",
    "zh": "我没有听到任何声音。如果需要帮助请再次致电。再见！",
}


def txml_gather(
    prompt: str,
    action_url: str,
    timeout: int = 8,
    voice: str = "Polly.Joanna",
    stt_language: str = "en-US",
    lang: str = "en",
) -> str:
    """
    Build a TeXML <Gather> response: speak a prompt, then listen for customer speech.

    Telnyx will POST the transcribed speech as `SpeechResult` to `action_url`
    when the customer stops speaking (or after `timeout` seconds of silence).

    Args:
        prompt:       Text to speak to the customer via TTS.
        action_url:   Webhook URL to receive the customer's transcribed speech.
        timeout:      Seconds of silence before giving up and playing the timeout message.
        voice:        Amazon Polly voice name — see VOICE_MAP in language_service.py.
        stt_language: BCP-47 language tag for STT — see STT_LANGUAGE_MAP in language_service.py.
        lang:         Language code ('en'|'es'|'zh') for the timeout fallback message.

    Returns:
        TeXML XML string to return as the HTTP response body.
    """
    timeout_msg = _escape_xml(_TIMEOUT_MESSAGES.get(lang, _TIMEOUT_MESSAGES["en"]))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="{action_url}" timeout="{timeout}" speechTimeout="auto" language="{stt_language}">
    <Say voice="{voice}">{_escape_xml(prompt)}</Say>
  </Gather>
  <Say voice="{voice}">{timeout_msg}</Say>
  <Hangup/>
</Response>"""


def txml_say_hangup(message: str, voice: str = "Polly.Joanna") -> str:
    """
    Build a TeXML response that speaks a final message and ends the call.

    Used for:
    - Order confirmation ("Your order is placed! Ready in ~20 minutes.")
    - Error conditions ("Technical issue, please call back.")
    - Clean call endings after the customer is done.

    Args:
        message: Text to speak before hanging up.
        voice:   Amazon Polly voice name — see VOICE_MAP in language_service.py.

    Returns:
        TeXML XML string to return as the HTTP response body.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="{voice}">{_escape_xml(message)}</Say>
  <Hangup/>
</Response>"""


def _escape_xml(text: str) -> str:
    """Escape XML special characters to prevent TeXML parse errors."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )
