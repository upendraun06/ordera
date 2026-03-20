"""
AI Conversation Engine
Uses Claude Haiku 4.5 for order taking and Claude Sonnet 4.6 for complex queries.
Includes prompt caching for restaurant info to reduce token costs by ~90%.
"""
import json
from typing import List, Optional
import anthropic
from app.config import settings
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem

# Model routing
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-6"

# Keywords that trigger Sonnet for more nuanced reasoning
COMPLEX_KEYWORDS = [
    "allerg", "gluten", "vegan", "vegetarian", "halal", "kosher",
    "dairy", "nut", "peanut", "shellfish", "policy", "refund", "catering"
]

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _select_model(user_message: str) -> str:
    """Route to Haiku or Sonnet based on message complexity."""
    msg_lower = user_message.lower()
    for keyword in COMPLEX_KEYWORDS:
        if keyword in msg_lower:
            return SONNET_MODEL
    return HAIKU_MODEL


def _build_menu_text(menu_items: List[MenuItem]) -> str:
    """Format menu items into readable text for the system prompt."""
    if not menu_items:
        return "No menu items available."

    by_category: dict = {}
    for item in menu_items:
        if not item.available:
            continue
        cat = item.category
        if cat not in by_category:
            by_category[cat] = []
        desc = f" - {item.description}" if item.description else ""
        by_category[cat].append(f"  • {item.name}: ${item.price:.2f}{desc}")

    lines = []
    for category, items in by_category.items():
        lines.append(f"\n{category}:")
        lines.extend(items)

    return "\n".join(lines)


def _build_system_prompt(
    restaurant: Restaurant,
    menu_items: List[MenuItem],
    rag_context: str = "",
) -> str:
    """
    Build the Claude system prompt with restaurant info, menu, and RAG context.
    The restaurant info and menu sections are marked for prompt caching.
    """
    menu_text = _build_menu_text(menu_items)

    hours_info = ""
    if restaurant.hours:
        try:
            hours_data = json.loads(restaurant.hours)
            hours_lines = [f"  {day}: {hours}" for day, hours in hours_data.items()]
            hours_info = "Operating Hours:\n" + "\n".join(hours_lines)
        except Exception:
            hours_info = f"Hours: {restaurant.hours}"

    rag_section = ""
    if rag_context:
        rag_section = f"""
## Restaurant Knowledge Base
The following information comes from restaurant-uploaded documents. Use this to answer specific questions:

{rag_context}
"""

    return f"""You are an AI phone agent for {restaurant.name}, a restaurant located at {restaurant.address or "Philadelphia, PA"}.

## Your Role
You answer incoming phone calls, take food orders, and answer customer questions. You are friendly, concise, and efficient.
Customers are calling on the phone, so keep responses SHORT (2-3 sentences max) and conversational.

## Restaurant Information
- Name: {restaurant.name}
- Address: {restaurant.address or "Contact us for address"}
- Phone: {restaurant.phone or "N/A"}
- Estimated wait time: {restaurant.estimated_wait_minutes} minutes
{hours_info}

## Menu
{menu_text}

## Order Flow
1. Greet the customer warmly and ask how you can help
2. Take their order item by item, asking for modifications
3. Confirm the full order and total price
4. Ask for their name for the order
5. Offer a payment link via SMS (ask if they'd like this)
6. When order is complete, output a JSON block like this:

<ORDER_COMPLETE>
{{
  "customer_name": "John",
  "items": [
    {{"name": "Burger", "quantity": 1, "price": 12.99, "modification": "no onions"}},
    {{"name": "Fries", "quantity": 2, "price": 3.99, "modification": ""}}
  ],
  "total": 20.97,
  "send_sms": true,
  "special_instructions": ""
}}
</ORDER_COMPLETE>
{rag_section}
## Rules
- NEVER make up menu items or prices not listed above
- If you don't know something, say "Let me check on that" and use the knowledge base
- Always confirm the order before finalizing
- Keep responses under 50 words for phone clarity
- If a customer asks about allergens or dietary restrictions, check the knowledge base carefully
- Say "Is there anything else I can help you with?" after completing the order
"""


def get_ai_response(
    restaurant: Restaurant,
    menu_items: List[MenuItem],
    conversation_history: List[dict],
    user_message: str,
    rag_context: str = "",
) -> tuple[str, bool]:
    """
    Get AI response from Claude.
    Returns (response_text, is_order_complete).
    """
    model = _select_model(user_message)
    system_prompt = _build_system_prompt(restaurant, menu_items, rag_context)

    messages = conversation_history + [{"role": "user", "content": user_message}]

    try:
        response = client.messages.create(
            model=model,
            max_tokens=500,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},   # Prompt caching
                }
            ],
            messages=messages,
        )
        text = response.content[0].text
        is_complete = "<ORDER_COMPLETE>" in text
        return text, is_complete

    except anthropic.APIError as e:
        # Fallback response
        return "I'm sorry, I'm having a technical issue. Please hold on for a moment.", False


def extract_order_json(response_text: str) -> Optional[dict]:
    """Extract the ORDER_COMPLETE JSON block from an AI response."""
    import re
    pattern = r"<ORDER_COMPLETE>\s*([\s\S]*?)\s*</ORDER_COMPLETE>"
    match = re.search(pattern, response_text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def get_greeting(restaurant: Restaurant, menu_items: List[MenuItem]) -> str:
    """Generate the opening greeting for a new call."""
    model = HAIKU_MODEL
    system_prompt = _build_system_prompt(restaurant, menu_items)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=100,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": "Generate a warm, professional phone greeting. Be brief (2 sentences max).",
                }
            ],
        )
        return response.content[0].text
    except Exception:
        return f"Thank you for calling {restaurant.name}! How can I help you today?"
