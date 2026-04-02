"""
AI Conversation Engine
======================
Core LLM routing layer. Routes requests to Groq or Anthropic Claude
depending on which API key is configured. Groq takes priority.

Provider selection (set in backend/.env)
-----------------------------------------
  GROQ_API_KEY      → Uses Groq (llama models) — faster & cheaper
  ANTHROPIC_API_KEY → Uses Anthropic Claude — fallback

Model tiers
-----------
  Fast    → Groq: llama-3.1-8b-instant        | Claude: claude-haiku-4-5-20251001
  Complex → Groq: llama-3.3-70b-versatile     | Claude: claude-sonnet-4-6

The fast model is used for most turns. Complex queries (allergies, dietary needs,
policies) automatically escalate to the complex model via _select_model_is_fast().

What this module does NOT do
-----------------------------
- Prompt construction → see services/prompt_builder.py
- Language detection  → see services/language_service.py
- Order persistence   → see services/order_service.py
- TeXML generation    → see services/telnyx_service.py
"""
import json
import logging
import re
from typing import List, Optional

from app.config import settings
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.services.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)

# ── Model IDs ─────────────────────────────────────────────────────────────────

HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-6"
GROQ_FAST_MODEL = "llama-3.1-8b-instant"
GROQ_COMPLEX_MODEL = "llama-3.3-70b-versatile"

# ── Keywords that trigger the complex (smarter) model ─────────────────────────
# Allergy and dietary questions require higher accuracy — use the better model.
COMPLEX_KEYWORDS = [
    "allerg", "gluten", "vegan", "vegetarian", "halal", "kosher",
    "dairy", "nut", "peanut", "shellfish", "policy", "refund", "catering",
]

# ── Client initialisation ─────────────────────────────────────────────────────
# Clients are created once at import time and reused across requests.

_groq_client = None
_anthropic_client = None

if settings.GROQ_API_KEY:
    from openai import OpenAI
    _groq_client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    logger.info("AI provider: Groq (%s / %s)", GROQ_FAST_MODEL, GROQ_COMPLEX_MODEL)

elif settings.ANTHROPIC_API_KEY:
    import anthropic
    _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    logger.info("AI provider: Anthropic Claude (%s / %s)", HAIKU_MODEL, SONNET_MODEL)

else:
    logger.warning("No AI provider configured — set GROQ_API_KEY or ANTHROPIC_API_KEY")


# ── Low-level chat helper ─────────────────────────────────────────────────────

def _chat(
    *,
    fast: bool,
    system: str,
    messages: list,
    max_tokens: int,
    cache_system: bool = False,
) -> str:
    """
    Send a chat request to Groq or Anthropic and return the assistant's text.

    Args:
        fast:         True → use the fast/cheap model; False → use the smart model.
        system:       System prompt string (empty string = no system message).
        messages:     List of {"role": ..., "content": ...} dicts.
        max_tokens:   Maximum tokens to generate.
        cache_system: Enable Anthropic prompt caching on the system prompt
                      (reduces cost on repeated calls with the same long prompt).
                      Ignored for Groq.

    Raises:
        RuntimeError: If no AI provider is configured.
    """
    if _groq_client:
        model = GROQ_FAST_MODEL if fast else GROQ_COMPLEX_MODEL
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)
        resp = _groq_client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=all_messages,
        )
        return resp.choices[0].message.content

    if not _anthropic_client:
        raise RuntimeError("No AI provider configured. Set GROQ_API_KEY or ANTHROPIC_API_KEY.")

    model = HAIKU_MODEL if fast else SONNET_MODEL
    system_param = []
    if system:
        block = {"type": "text", "text": system}
        if cache_system:
            block["cache_control"] = {"type": "ephemeral"}
        system_param = [block]

    resp = _anthropic_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_param,
        messages=messages,
    )
    return resp.content[0].text


# ── Model selection ───────────────────────────────────────────────────────────

def _select_model_is_fast(user_message: str) -> bool:
    """
    Return True (fast model) unless the message contains complex-topic keywords.
    Allergy and dietary queries use the smarter model for higher accuracy.
    """
    msg_lower = user_message.lower()
    return not any(kw in msg_lower for kw in COMPLEX_KEYWORDS)


# ── Voice conversation ────────────────────────────────────────────────────────

def get_ai_response(
    restaurant: Restaurant,
    menu_items: List[MenuItem],
    conversation_history: List[dict],
    user_message: str,
    rag_context: str = "",
    language: str = "en",
) -> tuple[str, bool]:
    """
    Generate the AI's next response in a voice conversation.

    Builds the system prompt (via prompt_builder), appends the user's message
    to the conversation history, calls the LLM, and returns the response.

    Args:
        restaurant:           Restaurant instance (menu, hours, contact info).
        menu_items:           Available menu items for this restaurant.
        conversation_history: Previous turns as [{"role": ..., "content": ...}].
        user_message:         The customer's transcribed speech for this turn.
        rag_context:          Retrieved knowledge base text (from rag_service).
        language:             Detected language code ('en'|'es'|'zh').

    Returns:
        (response_text, is_order_complete)
        is_order_complete is True when the AI's response contains <ORDER_COMPLETE>.
    """
    fast = _select_model_is_fast(user_message)
    system_prompt = build_system_prompt(
        restaurant=restaurant,
        menu_items=menu_items,
        rag_context=rag_context,
        language=language,
    )
    messages = conversation_history + [{"role": "user", "content": user_message}]

    try:
        text = _chat(
            fast=fast,
            system=system_prompt,
            messages=messages,
            max_tokens=500,
            cache_system=True,
        )
        is_complete = "<ORDER_COMPLETE>" in text
        return text, is_complete
    except Exception as e:
        logger.error("AI response error: %s", e)
        return "I'm sorry, I'm having a technical issue. Please hold on for a moment.", False


def get_greeting(restaurant: Restaurant, menu_items: List[MenuItem]) -> str:
    """
    Generate the opening greeting spoken when a customer first calls.

    Always uses English (language is unknown at this point).
    Language detection happens on the customer's first spoken reply.
    """
    system_prompt = build_system_prompt(restaurant, menu_items)
    try:
        return _chat(
            fast=True,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": (
                    "Generate a warm, natural phone greeting. "
                    "Spoken aloud — no markdown, no symbols. "
                    "1-2 sentences max, under 120 characters."
                ),
            }],
            max_tokens=80,
        )
    except Exception:
        return f"Thank you for calling {restaurant.name}! How can I help you today?"


def extract_order_json(response_text: str) -> Optional[dict]:
    """
    Extract and parse the ORDER_COMPLETE JSON block from an AI response.

    The AI outputs this block silently when an order is fully confirmed.
    Format defined in prompt_builder._ORDER_COMPLETE_BLOCK.

    Returns:
        Parsed dict with keys: customer_name, items, total, send_sms,
        special_instructions. Returns None if no valid block is found.
    """
    pattern = r"<ORDER_COMPLETE>\s*([\s\S]*?)\s*</ORDER_COMPLETE>"
    match = re.search(pattern, response_text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


# ── Menu extraction (used by knowledge.py on document upload) ─────────────────

def extract_menu_items(text: str) -> list[dict]:
    """
    Parse a menu document and return structured menu items as a list of dicts.

    Called by routers/knowledge.py when a "menu" type document is uploaded.
    Uses the complex model for better extraction accuracy.
    Processes text in 3000-character chunks to stay within model token limits.

    Returns:
        List of dicts with keys: category, name, description, price.
    """
    CHUNK_SIZE = 3000
    text_chunks = [text[i:i + CHUNK_SIZE] for i in range(0, min(len(text), 12000), CHUNK_SIZE)]
    all_items = []

    for chunk in text_chunks:
        prompt = (
            "Extract all menu items from the restaurant menu text below.\n"
            "Return ONLY a valid JSON array — no markdown, no explanation.\n"
            "Each element must have exactly these keys:\n"
            '  "category": string (e.g. "Appetizers", "Mains", "Sides", "Desserts", "Drinks")\n'
            '  "name": string\n'
            '  "description": string or null\n'
            '  "price": number (e.g. 12.99; use 0 if not found)\n\n'
            f"Menu text:\n{chunk}"
        )
        try:
            raw = _chat(
                fast=False,
                system="",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
            )
            logger.info("Menu extraction raw response (first 300 chars): %s", raw[:300])

            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            try:
                items = json.loads(raw)
            except json.JSONDecodeError:
                items = _parse_partial_json_array(raw)

            if isinstance(items, list):
                all_items.extend(items)

        except Exception as e:
            logger.error("Menu extraction chunk failed: %s", e)

    # Deduplicate by name (case-insensitive)
    seen: set = set()
    unique = []
    for item in all_items:
        name = item.get("name", "").strip().lower()
        if name and name not in seen:
            seen.add(name)
            unique.append(item)

    return unique


def _parse_partial_json_array(raw: str) -> list:
    """Salvage complete JSON objects from a truncated array string."""
    objects = []
    for match in re.finditer(r'\{[^{}]+\}', raw):
        try:
            obj = json.loads(match.group())
            if "name" in obj:
                objects.append(obj)
        except json.JSONDecodeError:
            continue
    return objects
