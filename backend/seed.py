"""
Seed script — inserts realistic sample data for Mario's Pizza.

Usage (from C:\RAG\backend):
    python seed.py

Creates:
  - 1 owner  (demo@marios.com / password123)
  - 1 restaurant
  - 18 menu items across 4 categories
  - 10 orders today  (mix of statuses + payment types)
  - 7 days of call logs for analytics charts
"""

import sys, os, uuid, json, random
from datetime import datetime, timedelta, timezone

# Make sure app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, create_tables
import app.models  # noqa — registers all models with SQLAlchemy

from app.models.owner       import Owner
from app.models.restaurant  import Restaurant
from app.models.menu_item   import MenuItem
from app.models.order       import Order, OrderItem
from app.models.call_log    import CallLog

import bcrypt

# ── helpers ──────────────────────────────────────────────────────────────────

def uid(): return str(uuid.uuid4())

def now_tz(): return datetime.now(timezone.utc)

def today_at(hour, minute=0):
    d = datetime.now(timezone.utc)
    return d.replace(hour=hour, minute=minute, second=0, microsecond=0)

# ── data ─────────────────────────────────────────────────────────────────────

MENU = [
    # Appetizers
    ("Appetizers", "Garlic Bread",          "Toasted with herb butter & parmesan",               5.99),
    ("Appetizers", "Mozzarella Sticks",     "6 pcs, served with marinara dipping sauce",          8.49),
    ("Appetizers", "Caesar Salad",          "Romaine, croutons, parmesan, house dressing",         9.99),
    ("Appetizers", "Chicken Wings",         "8 pcs — choose buffalo or BBQ",                     12.99),
    # Pizzas
    ("Pizzas",     "Margherita",            "San Marzano tomato, fresh mozzarella, basil",        14.99),
    ("Pizzas",     "Pepperoni Classic",     "Double pepperoni, mozzarella, tomato",               16.49),
    ("Pizzas",     "BBQ Chicken",           "Grilled chicken, red onion, cheddar, BBQ base",      17.99),
    ("Pizzas",     "Veggie Supreme",        "Bell peppers, mushrooms, olives, spinach, feta",     15.99),
    ("Pizzas",     "Meat Lover's",          "Pepperoni, sausage, bacon, ham, mozzarella",         19.99),
    ("Pizzas",     "Four Cheese",           "Mozzarella, provolone, cheddar, parmesan",           16.99),
    # Pastas
    ("Pastas",     "Spaghetti Bolognese",   "Slow-cooked beef ragù, fresh parmesan",              14.49),
    ("Pastas",     "Fettuccine Alfredo",    "Creamy parmesan sauce, choice of protein",           13.99),
    ("Pastas",     "Penne Arrabbiata",      "Spicy tomato, garlic, basil — vegan",                12.49),
    ("Pastas",     "Lasagna",               "Layers of beef, ricotta, béchamel",                  15.99),
    # Drinks
    ("Drinks",     "Fountain Soda",         "Coke, Diet Coke, Sprite, Lemonade",                   2.99),
    ("Drinks",     "Sparkling Water",       "San Pellegrino 500ml",                                3.49),
    ("Drinks",     "Fresh Lemonade",        "House-made with mint",                                4.49),
    ("Drinks",     "Italian Soda",          "Flavored sparkling — strawberry, peach, or mango",   3.99),
]

ORDERS = [
    # (customer_name, phone, status, pay_method, payment_status, special_instructions,
    #  items: [(name, qty, price, mod)])
    (
        "James Rivera", "+12155550101", "new", "stripe_link", "pending",
        "",
        [("Pepperoni Classic", 1, 16.49, ""), ("Fountain Soda", 2, 2.99, "Coke")]
    ),
    (
        "Sofia Chen", "+12155550102", "new", "cash", "pending",
        "Please ring doorbell twice",
        [("Margherita", 1, 14.99, "extra basil"), ("Caesar Salad", 1, 9.99, "dressing on side")]
    ),
    (
        "Marcus Thompson", "+12155550103", "confirmed", "stripe_link", "paid",
        "",
        [("Meat Lover's", 1, 19.99, ""), ("Garlic Bread", 2, 5.99, ""), ("Sparkling Water", 1, 3.49, "")]
    ),
    (
        "Aisha Patel", "+12155550104", "preparing", "cash", "pending",
        "No onions anywhere please",
        [("BBQ Chicken", 1, 17.99, "no red onions"), ("Mozzarella Sticks", 1, 8.49, "")]
    ),
    (
        "Liam O'Brien", "+12155550105", "preparing", "stripe_link", "paid",
        "",
        [("Four Cheese", 2, 16.99, "one gluten-free base"), ("Fresh Lemonade", 2, 4.49, "")]
    ),
    (
        "Natalie Wu", "+12155550106", "ready", "cash", "pending",
        "",
        [("Spaghetti Bolognese", 1, 14.49, ""), ("Garlic Bread", 1, 5.99, "no butter")]
    ),
    (
        "David Kim", "+12155550107", "ready", "stripe_link", "paid",
        "Extra napkins",
        [("Veggie Supreme", 1, 15.99, "add jalapeños"), ("Penne Arrabbiata", 1, 12.49, "")]
    ),
    (
        "Emma Johnson", "+12155550108", "picked_up", "cash", "pending",
        "",
        [("Chicken Wings", 2, 12.99, "extra buffalo sauce"), ("Italian Soda", 2, 3.99, "peach")]
    ),
    (
        "Carlos Mendez", "+12155550109", "picked_up", "stripe_link", "paid",
        "",
        [("Lasagna", 1, 15.99, ""), ("Fettuccine Alfredo", 1, 13.99, "add grilled chicken"), ("Fountain Soda", 1, 2.99, "Sprite")]
    ),
    (
        "Rachel Green", "+12155550110", "cancelled", "stripe_link", "failed",
        "",
        [("Margherita", 1, 14.99, "")]
    ),
]

CALL_LOG_DATA = [
    # (days_ago, count_completed, count_abandoned)
    (6, 8,  2),
    (5, 12, 1),
    (4, 10, 3),
    (3, 15, 2),
    (2, 11, 1),
    (1, 18, 2),
    (0, 14, 1),   # today
]

# ── seed ─────────────────────────────────────────────────────────────────────

def seed():
    create_tables()
    db = SessionLocal()

    try:
        # ── Owner ──
        existing = db.query(Owner).filter(Owner.email == "demo@marios.com").first()
        if existing:
            print("Owner already exists — wiping orders and call_logs for fresh seed...")
            # Delete orders + call logs belonging to this owner's restaurant
            rest = db.query(Restaurant).filter(Restaurant.owner_id == existing.id).first()
            if rest:
                db.query(CallLog).filter(CallLog.restaurant_id == rest.id).delete()
                for order in db.query(Order).filter(Order.restaurant_id == rest.id).all():
                    db.delete(order)
                db.commit()
            owner = existing
        else:
            owner = Owner(
                id=uid(),
                email="demo@marios.com",
                password_hash=bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
                restaurant_name="Mario's Pizza",
                plan="pro",
            )
            db.add(owner)
            db.flush()
            print(f"Created owner: {owner.email}")

        # ── Restaurant ──
        restaurant = db.query(Restaurant).filter(Restaurant.owner_id == owner.id).first()
        if not restaurant:
            restaurant = Restaurant(
                id=uid(),
                owner_id=owner.id,
                name="Mario's Pizza",
                address="1247 South Street, Philadelphia, PA 19147",
                phone="+12155559000",
                telnyx_phone="+12155559000",
                estimated_wait_minutes="20",
                hours=json.dumps({
                    "Monday":    "11:00 AM – 10:00 PM",
                    "Tuesday":   "11:00 AM – 10:00 PM",
                    "Wednesday": "11:00 AM – 10:00 PM",
                    "Thursday":  "11:00 AM – 10:00 PM",
                    "Friday":    "11:00 AM – 11:30 PM",
                    "Saturday":  "10:00 AM – 11:30 PM",
                    "Sunday":    "10:00 AM – 10:00 PM",
                }),
                is_active=True,
            )
            db.add(restaurant)
            db.flush()
            print(f"Created restaurant: {restaurant.name}")
        else:
            print(f"Restaurant exists: {restaurant.name}")

        # ── Menu ──
        existing_menu = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant.id).count()
        if existing_menu == 0:
            for category, name, description, price in MENU:
                db.add(MenuItem(
                    id=uid(),
                    restaurant_id=restaurant.id,
                    category=category,
                    name=name,
                    description=description,
                    price=price,
                    available=True,
                ))
            print(f"Created {len(MENU)} menu items")
        else:
            print(f"Menu already has {existing_menu} items — skipping")

        db.flush()

        # ── Orders (today) ──
        base_hour = 10  # orders start at 10 AM
        for i, (name, phone, status, pay_method, pay_status, notes, items) in enumerate(ORDERS):
            order_time = today_at(base_hour + i, minute=random.randint(0, 55))
            total = sum(price * qty for _, qty, price, _ in items)

            order = Order(
                id=uid(),
                restaurant_id=restaurant.id,
                customer_name=name,
                customer_phone=phone,
                status=status,
                total=round(total, 2),
                pay_method=pay_method,
                payment_status=pay_status,
                call_sid=f"seed_{uid()[:8]}",
                special_instructions=notes,
                created_at=order_time,
            )
            db.add(order)
            db.flush()

            for item_name, qty, price, mod in items:
                db.add(OrderItem(
                    id=uid(),
                    order_id=order.id,
                    name=item_name,
                    quantity=qty,
                    price=price,
                    modification=mod,
                ))

        print(f"Created {len(ORDERS)} orders")

        # ── Call logs (7 days) ──
        for days_ago, completed_n, abandoned_n in CALL_LOG_DATA:
            log_date = datetime.now(timezone.utc) - timedelta(days=days_ago)

            for j in range(completed_n):
                t = log_date.replace(
                    hour=random.randint(11, 21),
                    minute=random.randint(0, 59),
                    second=0,
                )
                db.add(CallLog(
                    id=uid(),
                    restaurant_id=restaurant.id,
                    call_sid=f"log_{uid()[:10]}",
                    caller_phone=f"+1215555{random.randint(1000,9999)}",
                    duration_seconds=random.randint(45, 240),
                    status="completed",
                    ai_turns=random.randint(4, 12),
                    created_at=t,
                ))

            for j in range(abandoned_n):
                t = log_date.replace(
                    hour=random.randint(11, 21),
                    minute=random.randint(0, 59),
                    second=0,
                )
                db.add(CallLog(
                    id=uid(),
                    restaurant_id=restaurant.id,
                    call_sid=f"log_{uid()[:10]}",
                    caller_phone=f"+1215555{random.randint(1000,9999)}",
                    duration_seconds=random.randint(3, 8),
                    status="abandoned",
                    ai_turns=0,
                    created_at=t,
                ))

        total_logs = sum(c + a for _, c, a in CALL_LOG_DATA)
        print(f"Created {total_logs} call log entries across 7 days")

        db.commit()
        print("\nSeed complete.")
        print("-" * 40)
        print("Login:    demo@marios.com")
        print("Password: password123")
        print("-" * 40)

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
