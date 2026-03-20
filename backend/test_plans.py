import sys
sys.path.insert(0, ".")
from app.routers.subscription import PLANS
print("=== BASIC FEATURES ===")
for f in PLANS["basic"]["features"]:
    print(f"  - {f}")
print("=== BASIC LIMITS ===")
print(PLANS["basic"]["limits"])
print("=== PRO FEATURES ===")
for f in PLANS["pro"]["features"]:
    print(f"  - {f}")
