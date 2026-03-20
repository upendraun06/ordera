from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.models.order import Order
from app.services.stripe_service import verify_webhook

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    event = verify_webhook(payload, stripe_signature or "")

    if not event:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")
        if order_id:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.payment_status = "paid"
                order.stripe_session_id = session.get("id")
                db.commit()

    return {"received": True}


@router.get("/success")
def payment_success(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        return {
            "message": "Payment successful! Your order is being prepared.",
            "order_id": order_id,
            "status": order.status,
        }
    return {"message": "Payment received. Thank you!"}


@router.get("/cancel")
def payment_cancel(order_id: str):
    return {
        "message": "Payment was cancelled. You can pay in person when you pick up your order.",
        "order_id": order_id,
    }
