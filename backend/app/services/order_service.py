"""
Order Service
=============
Handles order creation from completed AI voice calls.

How an order gets created
--------------------------
1. Customer calls → AI handles the conversation (voice.py / ai_engine.py)
2. AI detects the order is fully confirmed and outputs an <ORDER_COMPLETE> JSON block
3. voice.py calls extract_order_json() (ai_engine.py) to parse the JSON
4. voice.py calls save_order_from_voice() (this file) to persist the order
5. If the customer requested SMS payment, a Stripe payment link is created and
   attached to the order before the SMS is sent via sms_service.py

Database rule
-------------
Every query in this service filters by restaurant_id to prevent cross-tenant data access.
"""
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.order import Order, OrderItem
from app.models.restaurant import Restaurant
from app.services.stripe_service import create_payment_link
from app.config import settings


def save_order_from_voice(
    db: Session,
    restaurant: Restaurant,
    conversation: Conversation,
    order_data: dict,
    customer_phone: str,
) -> Order:
    """
    Persist an order (and its line items) extracted from a completed AI call.

    This function does NOT commit the session — voice.py commits after
    updating conversation and call_log in the same transaction.

    Args:
        db:             Active database session.
        restaurant:     The restaurant receiving the order (tenant boundary).
        conversation:   The call's Conversation record (provides call_sid).
        order_data:     Dict parsed from the AI's ORDER_COMPLETE JSON block.
                        Expected keys: customer_name, items, total, send_sms,
                        special_instructions.
        customer_phone: Caller's E.164 phone number (e.g. "+12155550100").

    Returns:
        The created Order ORM instance (flushed but not committed).
    """
    items = order_data.get("items", [])

    # Prefer the AI-computed total; fall back to summing line items
    total = order_data.get(
        "total",
        sum(i.get("price", 0) * i.get("quantity", 1) for i in items),
    )

    order = Order(
        restaurant_id=restaurant.id,
        customer_name=order_data.get("customer_name"),
        customer_phone=customer_phone,
        status="new",
        total=total,
        pay_method="stripe_link" if order_data.get("send_sms") else "cash",
        payment_status="pending",
        call_sid=conversation.call_sid,
        special_instructions=order_data.get("special_instructions", ""),
    )
    db.add(order)
    db.flush()  # Assigns order.id without committing the transaction

    # Optionally create a Stripe Checkout link for SMS payment
    if order_data.get("send_sms") and settings.STRIPE_SECRET_KEY:
        payment_link = create_payment_link(
            order_id=order.id,
            restaurant_name=restaurant.name,
            total_amount=total,
            items=items,
        )
        order.stripe_payment_link = payment_link

    # Save individual line items
    for item_data in items:
        db.add(OrderItem(
            order_id=order.id,
            name=item_data.get("name", "Unknown"),
            quantity=item_data.get("quantity", 1),
            price=item_data.get("price", 0.0),
            modification=item_data.get("modification", ""),
        ))

    db.flush()
    return order
