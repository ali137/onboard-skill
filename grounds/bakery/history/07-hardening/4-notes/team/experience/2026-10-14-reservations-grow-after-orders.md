# Later orders reserve more stock than they need

| Field | Content |
|---|---|
| date | 2026-10-14 |
| commit | {{commit:p7-inventory-fix}} |
| files | bakery/inventory.py |
| symptom | After the first order of a product, later orders of the same product reserve more than their lines need. With a few more orders `Stock.reserve` raises `InsufficientStock` although the stores hold plenty, and canceling an order does not bring stock back to where it was. Found as review finding R1 in phase 6. |
| cause | `requirements()` took `copy.copy(RECIPES[sku])`, a shallow copy, and scaled it by the quantity. The component dicts inside were still those of the shared `RECIPES` entry, so the recipe itself was multiplied in place and every later call started from the inflated grams. |
| fix | `copy.deepcopy(RECIPES[sku])` before scaling, so the recipes stay untouched shared data (D4). |
| verified by | tests/test_inventory.py::test_second_order_reserves_only_its_own_quantity |
| applies when | a function scales, merges or edits nested module-level data (recipes, price tables, slot lists) and returns the result |
| does not apply when | the data is flat, or only read; or the function builds a new structure without starting from the shared one |
