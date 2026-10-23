from datetime import date, datetime

import pytest

from bakery.inventory import (
    NO_STOCK,
    RECIPES,
    InsufficientStock,
    Stock,
    flatten,
    plan_requirements,
    requirements,
)
from bakery.orders import Order, OrderLine, Status

BAKE_DAY = date(2026, 10, 15)


def full_stock():
    return Stock({"flour": 50_000, "butter": 20_000, "milk": 10_000, "yeast": 2_000,
                  "sugar": 10_000, "egg": 5_000, "water": 40_000, "salt": 1_000,
                  "chocolate": 3_000, "cinnamon": 500, "sesame": 1_000})


def order(order_id, lines, due=BAKE_DAY, status=Status.PLACED, preorder=False):
    return Order(order_id, "cust-0042", "retail", lines, datetime(2026, 10, 12, 9, 0), due,
                 status, preorder)


def test_every_product_on_the_price_list_has_a_recipe_or_needs_no_stock():
    skus = {"sourdough-loaf", "rye-loaf", "baguette", "croissant", "pain-au-chocolat",
            "cinnamon-bun", "sesame-roll", "birthday-cake"}
    assert set(RECIPES) == skus
    assert NO_STOCK == {"filter-coffee", "delivery-fee"}


def test_requirements_scale_each_component():
    per_unit = {part: dict(grams) for part, grams in RECIPES["cinnamon-bun"].items()}
    need = requirements("cinnamon-bun", 4)
    assert need == {part: {k: v * 4 for k, v in grams.items()} for part, grams in per_unit.items()}


def test_flatten_adds_an_ingredient_used_in_two_components():
    need = {"dough": {"flour": 500, "water": 350}, "starter": {"flour": 100, "water": 100}}
    assert flatten(need) == {"flour": 600, "water": 450}


def test_items_without_stock_need_nothing():
    assert requirements("filter-coffee", 3) == {}


def test_unknown_product_has_no_requirements():
    with pytest.raises(KeyError):
        requirements("bagel", 1)


def test_receive_adds_to_stock():
    stock = Stock({"flour": 1_000})
    stock.receive("flour", 500)
    stock.receive("rye-flour", 2_000)
    assert stock.available("flour") == 1_500
    assert stock.available("rye-flour") == 2_000
    with pytest.raises(ValueError):
        stock.receive("flour", 0)


def test_reserve_lowers_available_stock_by_the_reservation():
    stock = full_stock()
    before = stock.available()
    reserved = stock.reserve("O-0001", [OrderLine("sourdough-loaf", 3)])
    after = stock.available()
    assert all(after[name] == before[name] - grams for name, grams in reserved.items())
    assert stock.reserved_for("O-0001") == reserved


def test_reserve_is_all_or_nothing():
    stock = Stock({"flour": 100_000, "water": 100_000, "salt": 1_000, "yeast": 1})
    before = stock.available()
    with pytest.raises(InsufficientStock) as err:
        stock.reserve("O-0001", [OrderLine("sourdough-loaf", 1), OrderLine("baguette", 1)])
    assert err.value.ingredient == "yeast"
    assert stock.available() == before
    with pytest.raises(KeyError):
        stock.reserved_for("O-0001")


def test_same_order_cannot_reserve_twice():
    stock = full_stock()
    stock.reserve("O-0001", [OrderLine("baguette", 1)])
    with pytest.raises(ValueError, match="already"):
        stock.reserve("O-0001", [OrderLine("baguette", 1)])


def test_release_returns_the_reservation():
    stock = full_stock()
    before = stock.available()
    stock.reserve("O-0001", [OrderLine("pain-au-chocolat", 6)])
    stock.release("O-0001")
    assert stock.available() == before


def test_replace_swaps_the_reservation_all_or_nothing():
    stock = full_stock()
    old = stock.reserve("O-0001", [OrderLine("baguette", 2)], preorder=True)
    with pytest.raises(InsufficientStock):
        stock.replace("O-0001", [OrderLine("rye-loaf", 1)])
    assert stock.reserved_for("O-0001") == old
    assert stock.held_for_preorders() == old
    new = stock.replace("O-0001", [OrderLine("sesame-roll", 4)])
    assert stock.reserved_for("O-0001") == new and "sesame" in new


def test_release_of_unknown_order_is_an_error():
    with pytest.raises(KeyError, match="O-0099"):
        full_stock().release("O-0099")


def test_low_stock_lists_ingredients_below_threshold():
    stock = Stock({"flour": 5_000, "yeast": 40, "salt": 300})
    assert stock.low_stock(500) == {"salt": 300, "yeast": 40}


def test_bake_plan_counts_orders_due_that_day():
    orders = [
        order("O-0001", [OrderLine("croissant", 12), OrderLine("filter-coffee", 2)]),
        order("O-0002", [OrderLine("croissant", 6), OrderLine("rye-loaf", 2)]),
        order("O-0003", [OrderLine("baguette", 10)], status=Status.CANCELED),
        order("O-0004", [OrderLine("baguette", 4)], due=date(2026, 10, 16)),
    ]
    assert Stock.bake_plan(orders, BAKE_DAY) == {"croissant": 18, "rye-loaf": 2}


def test_plan_requirements_add_up_the_products():
    baguette = dict(RECIPES["baguette"]["dough"])
    roll = {k: v for part in RECIPES["sesame-roll"].values() for k, v in part.items()}
    need = plan_requirements({"baguette": 2, "sesame-roll": 10})
    assert need["flour"] == 2 * baguette["flour"] + 10 * roll["flour"]
    assert need["sesame"] == 10 * roll["sesame"]


def test_shortfall_lists_what_on_hand_stock_lacks():
    stock = Stock({"flour": 1_000, "butter": 500})
    assert stock.shortfall({"flour": 1_200, "butter": 400, "egg": 60}) == {"egg": 60, "flour": 200}


def test_stock_take_sets_on_hand_and_reports_the_difference():
    stock = full_stock()
    stock.reserve("O-0001", [OrderLine("baguette", 1)])
    assert stock.count("salt", 900) == -100
    assert stock.on_hand("salt") == 900
    with pytest.raises(ValueError, match="reserved"):
        stock.count("salt", 1)


def test_second_order_reserves_only_its_own_quantity():
    stock = full_stock()
    stock.reserve("O-0001", [OrderLine("croissant", 3)])
    second = stock.reserve("O-0002", [OrderLine("croissant", 2)])
    # Two croissants, from the recipe as written: dough 50/25/15/2/6 g, finish 5 g egg.
    assert second == {"flour": 100, "butter": 50, "milk": 30, "yeast": 4, "sugar": 12, "egg": 10}


def test_cancel_restores_stock_exactly():
    stock = full_stock()
    stock.reserve("O-0001", [OrderLine("croissant", 3)])
    stock.reserve("O-0002", [OrderLine("croissant", 2)])
    stock.release("O-0002")
    assert stock.available("butter") == 20_000 - 75
    assert stock.available("flour") == 50_000 - 150
    assert stock.available("egg") == 5_000 - 15


def test_preorder_reservations_are_held_separately():
    stock = full_stock()
    stock.reserve("O-0001", [OrderLine("baguette", 1)])
    buns = stock.reserve("O-0002", [OrderLine("cinnamon-bun", 2)], preorder=True)
    assert stock.held_for_preorders() == buns
    stock.release("O-0002")
    assert stock.held_for_preorders() == {}


def test_bake_plan_includes_preorders_due_that_day():
    orders = [order("O-0001", [OrderLine("cinnamon-bun", 24)], preorder=True),
              order("O-0002", [OrderLine("cinnamon-bun", 6)])]
    assert Stock.bake_plan(orders, BAKE_DAY) == {"cinnamon-bun": 30}
