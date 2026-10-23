"""Inventory: recipes, ingredient stock, reservations and the bake plan.

Recipes are nested: product -> component -> ingredient -> grams per unit (D4).
RECIPES is shared module data; nothing may change it at run time (D4). Stock is
reserved for an order when it is placed and released when it is canceled (D5).
"""
import copy
from collections import Counter

# Grams per unit. Items in NO_STOCK are sold but use no ingredients from stock.
RECIPES = {
    "sourdough-loaf": {
        "dough": {"flour": 500, "water": 350, "salt": 10},
        "starter": {"flour": 100, "water": 100},
    },
    "rye-loaf": {
        "dough": {"rye-flour": 400, "flour": 100, "water": 380, "salt": 9},
        "seeds": {"caraway": 4},
    },
    "baguette": {
        "dough": {"flour": 250, "water": 175, "salt": 5, "yeast": 2},
    },
    "croissant": {
        "dough": {"flour": 50, "butter": 25, "milk": 15, "yeast": 2, "sugar": 6},
        "finish": {"egg": 5},
    },
    "pain-au-chocolat": {
        "dough": {"flour": 50, "butter": 25, "milk": 15, "yeast": 2, "sugar": 6},
        "filling": {"chocolate": 12},
        "finish": {"egg": 5},
    },
    "cinnamon-bun": {
        "dough": {"flour": 70, "milk": 40, "butter": 15, "sugar": 10, "yeast": 2},
        "filling": {"butter": 10, "sugar": 12, "cinnamon": 3},
    },
    "sesame-roll": {
        "dough": {"flour": 60, "water": 40, "salt": 1, "yeast": 1},
        "topping": {"sesame": 4},
    },
    "birthday-cake": {
        "sponge": {"flour": 300, "sugar": 300, "butter": 300, "egg": 300},
        "frosting": {"butter": 200, "sugar": 400, "cream": 200},
    },
}

NO_STOCK = frozenset({"filter-coffee", "delivery-fee"})


class InsufficientStock(Exception):
    """Not enough of one ingredient is available for a reservation."""

    def __init__(self, ingredient: str, needed: int, available: int):
        super().__init__(f"need {needed} g of {ingredient}, only {available} g available")
        self.ingredient = ingredient
        self.needed = needed
        self.available = available


def requirements(sku: str, qty: int) -> dict[str, dict[str, int]]:
    """Grams of each ingredient, by component, for `qty` units of `sku` (D4).

    Scales a private copy of the recipe; RECIPES itself stays as written.
    Items in NO_STOCK need nothing.
    """
    if sku in NO_STOCK:
        return {}
    if sku not in RECIPES:
        raise KeyError(f"no recipe for {sku!r}")
    need = copy.deepcopy(RECIPES[sku])
    for part in need.values():
        for ingredient in part:
            part[ingredient] = part[ingredient] * qty
    return need


def flatten(req: dict[str, dict[str, int]]) -> dict[str, int]:
    """Sum a by-component requirement into {ingredient: grams}."""
    total = Counter()
    for part in req.values():
        total.update(part)
    return dict(total)


def lines_requirement(lines) -> dict[str, int]:
    """Total grams per ingredient for order lines (anything with .sku and .qty)."""
    total = Counter()
    for line in lines:
        total.update(flatten(requirements(line.sku, line.qty)))
    return dict(total)


def plan_requirements(plan: dict[str, int]) -> dict[str, int]:
    """Total grams per ingredient to bake a plan of {sku: units}, such as bake_plan's."""
    total = Counter()
    for sku, qty in plan.items():
        total.update(flatten(requirements(sku, qty)))
    return dict(sorted(total.items()))


class Stock:
    """Ingredients on hand, less what open orders have reserved (D5)."""

    def __init__(self, on_hand: dict[str, int] | None = None):
        self._on_hand = Counter(on_hand or {})
        self._reserved: dict[str, dict[str, int]] = {}

    def receive(self, ingredient: str, grams: int) -> None:
        """Book a delivery of an ingredient into stock."""
        if grams <= 0:
            raise ValueError(f"received amount must be positive, got {grams}")
        self._on_hand[ingredient] += grams

    def on_hand(self, ingredient: str) -> int:
        return self._on_hand[ingredient]

    def count(self, ingredient: str, grams: int) -> int:
        """Set on-hand stock from a stock-take; return the difference from the books.

        A count below what open orders have reserved is refused: those orders
        would have to be changed first.
        """
        reserved = self._reserved_total()[ingredient]
        if grams < reserved:
            raise ValueError(f"counted {grams} g of {ingredient}, but {reserved} g are reserved")
        difference = grams - self._on_hand[ingredient]
        self._on_hand[ingredient] = grams
        return difference

    def _reserved_total(self) -> Counter:
        total = Counter()
        for amounts in self._reserved.values():
            total.update(amounts)
        return total

    def available(self, ingredient: str | None = None):
        """Grams not reserved: for one ingredient, or {ingredient: grams} for all."""
        reserved = self._reserved_total()
        if ingredient is not None:
            return self._on_hand[ingredient] - reserved[ingredient]
        names = sorted(set(self._on_hand) | set(reserved))
        return {name: self._on_hand[name] - reserved[name] for name in names}

    def reserve(self, order_id: str, lines) -> dict[str, int]:
        """Reserve the ingredients for an order's lines, all or nothing (D5).

        Raises InsufficientStock, reserving nothing, if any ingredient falls short.
        """
        if order_id in self._reserved:
            raise ValueError(f"{order_id} already has a reservation")
        need = lines_requirement(lines)
        for ingredient, grams in sorted(need.items()):
            free = self.available(ingredient)
            if grams > free:
                raise InsufficientStock(ingredient, grams, free)
        self._reserved[order_id] = need
        return dict(need)

    def release(self, order_id: str) -> dict[str, int]:
        """Give an order's reservation back to available stock (the order was canceled)."""
        try:
            amounts = self._reserved.pop(order_id)
        except KeyError:
            raise KeyError(f"no reservation for {order_id!r}") from None
        return amounts

    def replace(self, order_id: str, lines) -> dict[str, int]:
        """Swap an order's reservation for one covering new lines, all or nothing (D5).

        If the new lines cannot be covered, the old reservation stays exactly as it was.
        """
        old = self.release(order_id)
        try:
            return self.reserve(order_id, lines)
        except InsufficientStock:
            self._reserved[order_id] = old
            raise

    def consume(self, order_id: str) -> dict[str, int]:
        """The order was baked: its reserved grams leave on-hand stock for good."""
        amounts = self.release(order_id)
        self._on_hand.subtract(amounts)
        return amounts

    def reserved_for(self, order_id: str) -> dict[str, int]:
        if order_id not in self._reserved:
            raise KeyError(f"no reservation for {order_id!r}")
        return dict(self._reserved[order_id])

    def low_stock(self, threshold: int) -> dict[str, int]:
        """Ingredients whose available grams are below `threshold`, for the order sheet."""
        return {name: grams for name, grams in self.available().items() if grams < threshold}

    def shortfall(self, need: dict[str, int]) -> dict[str, int]:
        """Grams of each ingredient that on-hand stock lacks to cover `need`, for the mill order."""
        return {
            name: grams - self._on_hand[name]
            for name, grams in sorted(need.items())
            if grams > self._on_hand[name]
        }

    @staticmethod
    def bake_plan(orders, day) -> dict[str, int]:
        """Units of each product to bake for orders due on `day`, canceled ones left out.

        Items in NO_STOCK are not baked.
        """
        plan = Counter()
        for order in orders:
            if order.due != day or order.status == "canceled":
                continue
            for line in order.lines:
                if line.sku not in NO_STOCK:
                    plan[line.sku] += line.qty
        return dict(sorted(plan.items()))
