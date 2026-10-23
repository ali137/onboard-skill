from datetime import date, datetime, time

import pytest

from bakery.delivery import (
    SLOTS,
    STOPS_PER_VAN,
    VANS,
    NotADeliveryDay,
    Schedule,
    ScheduleFull,
    earliest_delivery_day,
    format_route_sheet,
    is_delivery_day,
    slot_for,
)

SATURDAY = date(2026, 10, 17)
SUNDAY = date(2026, 10, 18)
MONDAY = date(2026, 10, 19)
MORNING, LATE_MORNING, AFTERNOON = SLOTS


def fill_slot(schedule, day, slot, count, prefix="O"):
    for n in range(count):
        schedule.assign(f"{prefix}-{slot.start:%H}{n:02d}", day, preferred=slot)


def test_sunday_is_not_a_delivery_day():
    assert not is_delivery_day(SUNDAY)
    assert is_delivery_day(SATURDAY)
    assert is_delivery_day(MONDAY)


def test_closure_dates_are_not_delivery_days():
    assert not is_delivery_day(MONDAY, closures=frozenset({MONDAY}))


def test_order_before_cutoff_delivers_next_day():
    assert earliest_delivery_day(datetime(2026, 10, 13, 13, 59)) == date(2026, 10, 14)


def test_order_at_cutoff_delivers_the_day_after_next():
    assert earliest_delivery_day(datetime(2026, 10, 13, 14, 0)) == date(2026, 10, 15)


def test_friday_morning_order_delivers_saturday():
    assert earliest_delivery_day(datetime(2026, 10, 16, 10, 0)) == SATURDAY


def test_late_friday_order_skips_sunday():
    assert earliest_delivery_day(datetime(2026, 10, 16, 15, 0)) == MONDAY


def test_earliest_delivery_skips_a_closure():
    placed = datetime(2026, 10, 16, 15, 0)
    assert earliest_delivery_day(placed, closures=frozenset({MONDAY})) == date(2026, 10, 20)


def test_slots_are_half_open():
    assert slot_for(time(8, 0)) == MORNING
    assert slot_for(time(9, 59)) == MORNING
    assert slot_for(time(10, 0)) == LATE_MORNING
    assert slot_for(time(14, 0)) == AFTERNOON
    assert slot_for(time(12, 0)) is None
    assert slot_for(time(16, 0)) is None
    assert slot_for(time(7, 59)) is None


def test_assign_uses_preferred_slot_and_first_van():
    schedule = Schedule()
    stop = schedule.assign("O-0001", MONDAY, preferred=AFTERNOON)
    assert (stop.slot, stop.van) == (AFTERNOON, 1)


def test_assign_without_preference_takes_first_slot_with_room():
    schedule = Schedule()
    assert schedule.assign("O-0001", MONDAY).slot == MORNING


def test_second_van_fills_after_the_first():
    schedule = Schedule()
    fill_slot(schedule, MONDAY, MORNING, STOPS_PER_VAN)
    stop = schedule.assign("O-0100", MONDAY, preferred=MORNING)
    assert (stop.slot, stop.van) == (MORNING, 2)


def test_full_preferred_slot_moves_to_the_next_slot():
    schedule = Schedule()
    fill_slot(schedule, MONDAY, MORNING, VANS * STOPS_PER_VAN)
    assert schedule.load(MONDAY, MORNING) == 12
    stop = schedule.assign("O-0100", MONDAY, preferred=MORNING)
    assert (stop.slot, stop.van) == (LATE_MORNING, 1)


def test_full_day_raises_schedule_full():
    schedule = Schedule()
    for slot in SLOTS:
        fill_slot(schedule, MONDAY, slot, VANS * STOPS_PER_VAN)
    with pytest.raises(ScheduleFull):
        schedule.assign("O-0100", MONDAY)


def test_assign_refuses_sunday_and_closures():
    schedule = Schedule()
    with pytest.raises(NotADeliveryDay):
        schedule.assign("O-0001", SUNDAY)
    with pytest.raises(NotADeliveryDay):
        schedule.assign("O-0001", MONDAY, closures=frozenset({MONDAY}))


def test_order_is_scheduled_once():
    schedule = Schedule()
    schedule.assign("O-0001", MONDAY)
    with pytest.raises(ValueError, match="already scheduled"):
        schedule.assign("O-0001", SATURDAY)


def test_unassign_frees_the_stop():
    schedule = Schedule()
    schedule.assign("O-0001", MONDAY)
    schedule.unassign("O-0001")
    assert schedule.load(MONDAY, MORNING) == 0


def test_capacity_counts_free_stops_per_slot():
    schedule = Schedule()
    fill_slot(schedule, MONDAY, LATE_MORNING, 5)
    assert schedule.capacity(MONDAY) == {"08:00-10:00": 12, "10:00-12:00": 7, "14:00-16:00": 12}


def test_reschedule_moves_the_stop():
    schedule = Schedule()
    schedule.assign("O-0001", MONDAY)
    moved = schedule.reschedule("O-0001", SATURDAY, preferred=AFTERNOON)
    assert (moved.day, moved.slot) == (SATURDAY, AFTERNOON)
    assert schedule.get("O-0001") == moved
    assert schedule.load(MONDAY, MORNING) == 0


def test_refused_reschedule_keeps_the_old_stop():
    schedule = Schedule()
    old = schedule.assign("O-0001", MONDAY)
    with pytest.raises(NotADeliveryDay):
        schedule.reschedule("O-0001", SUNDAY)
    assert schedule.get("O-0001") == old


def test_route_sheet_is_sorted_by_slot_then_van():
    schedule = Schedule()
    schedule.assign("O-0003", MONDAY, preferred=AFTERNOON)
    fill_slot(schedule, MONDAY, MORNING, STOPS_PER_VAN)
    schedule.assign("O-0002", MONDAY, preferred=MORNING)
    schedule.assign("O-0009", SATURDAY)
    sheet = schedule.route_sheet(MONDAY)
    assert len(sheet) == 8
    assert [(a.slot.label, a.van) for a in sheet[-2:]] == [("08:00-10:00", 2), ("14:00-16:00", 1)]


def test_preorder_flag_is_kept_on_the_stop():
    schedule = Schedule()
    cake = schedule.assign("O-0001", MONDAY, preorder=True)
    bread = schedule.assign("O-0002", MONDAY)
    assert (cake.preorder, bread.preorder) == (True, False)
    assert [a.preorder for a in schedule.route_sheet(MONDAY)] == [True, False]


def test_route_sheet_text_marks_preorders():
    schedule = Schedule()
    schedule.assign("O-0001", MONDAY, preorder=True)
    schedule.assign("O-0002", MONDAY, preferred=AFTERNOON)
    text = format_route_sheet(MONDAY, schedule.route_sheet(MONDAY))
    assert text == ("Route sheet Monday 2026-10-19\n"
                    "08:00-10:00  van 1  O-0001  pre-order\n"
                    "14:00-16:00  van 1  O-0002\n")
