import pytest
import sys
import os 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


def test_register_until_capacity_then_waitlist_fifo_positions():
    er = EventRegistration(capacity=2)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")
    s4 = er.register("u4")

    assert s1 == UserStatus("registered")
    assert s2 == UserStatus("registered")
    assert s3 == UserStatus("waitlisted", 1)
    assert s4 == UserStatus("waitlisted", 2)

    snap = er.snapshot()
    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3", "u4"]


def test_cancel_registered_promotes_earliest_waitlisted_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    er.cancel("u1")  # should promote u2

    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


def test_duplicate_register_raises_for_registered_and_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest):
        er.register("u2")


def test_waitlisted_cancel_removes_and_updates_positions():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    er.cancel("u2")    # remove from waitlist

    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]


def test_capacity_zero_all_waitlisted_and_promotion_never_happens():
    er = EventRegistration(capacity=0)
    assert er.register("u1") == UserStatus("waitlisted", 1)
    assert er.register("u2") == UserStatus("waitlisted", 2)

    # No one can ever be registered when capacity=0
    assert er.status("u1") == UserStatus("waitlisted", 1)
    assert er.status("u2") == UserStatus("waitlisted", 2)
    assert er.snapshot()["registered"] == []

    # Cancel unknown should raise NotFound
    with pytest.raises(NotFound):
        er.cancel("missing")



#################################################################################
# Add your own additional tests here to cover more cases and edge cases as needed.
#################################################################################

# =========================
# AC1: Capacity < 0 rejected
# =========================

def test_ac1_negative_capacity_raises_value_error():

    with pytest.raises(ValueError):
        EventRegistration(-1)

# =========================
# AC2: Earliest waitlisted promoted correctly
# =========================
def test_ac2_promotion_moves_user_to_end_of_registered_fifo():
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")  # waitlist pos1
    er.register("u4")  # waitlist pos2

    er.cancel("u1")  # should promote u3

    snap = er.snapshot()

    assert snap["registered"] == ["u2", "u3"]
    assert snap["waitlist"] == ["u4"]
    assert er.status("u3") == UserStatus("registered")

# =========================
# AC3: Duplicate register rejected
# =========================
def test_ac3_duplicate_register_registered_and_waitlisted():
    er = EventRegistration(capacity=1)

    er.register("userA")

    with pytest.raises(DuplicateRequest):
        er.register("userA")

    er.register("userB")  # waitlist

    with pytest.raises(DuplicateRequest):
        er.register("userB")

# =========================
# AC4: At capacity -> user added to end of waitlist
# =========================
def test_ac4_register_when_full_goes_to_end_of_waitlist():
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u2", "u3"]

# =========================
# AC5: Waitlisted cancel preserves FIFO order
def test_ac5_cancel_waitlisted_preserves_fifo():
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.register("u2")
    er.register("u3")
    er.register("u4")

    er.cancel("u3")

    snap = er.snapshot()
    assert snap["waitlist"] == ["u2", "u4"]
    assert er.status("u3") == UserStatus("none")


# =========================
# AC6: Multiple users added FIFO when full
# =========================
def test_ac6_multiple_waitlist_fifo_order():
    er = EventRegistration(capacity=1)
    er.register("u1")

    er.register("a2")
    er.register("u3")
    er.register("u4")

    snap = er.snapshot()
    assert snap["waitlist"] == ["a2", "u3", "u4"]

# =========================
# AC7: Empty string registration is rejected
# =========================
def test_ac7_empty_user_id_rejected():
    er = EventRegistration(capacity=1)

    with pytest.raises(ValueError):
        er.register("")


# =========================
# AC9: Cancel waitlisted when full results in no promotion
# =========================
def test_ac9_cancel_waitlisted_does_not_trigger_promotion():
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.register("u2")
    er.register("u3")

    er.cancel("u2")  # cancel waitlisted user

    snap = er.snapshot()

    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]

# =========================
# AC10: Cancel non-existent user raises NotFound
def test_ac10_cancel_nonexistent_user_raises_notfound():
    er = EventRegistration(capacity=1)

    er.register("u1")

    with pytest.raises(NotFound):
        er.cancel("ghost")

    # Ensure state unchanged
    snap = er.snapshot()
    assert snap["registered"] == ["u1"]

# =========================
# AC11: Case-insensitive duplicate rejected
# =========================
def test_ac11_case_insensitive_duplicate():
    er = EventRegistration(capacity=1)

    er.register("UserA")
    with pytest.raises(DuplicateRequest):
        er.register("usera")

    with pytest.raises(DuplicateRequest):
        er.register("USERA")

# =========================
# AC12: Capacity cannot be changed after initialization
# =========================
def test_ac12_capacity_immutable():
    er = EventRegistration(capacity=2)

    with pytest.raises(AttributeError):
        er.capacity = 5  # property has no setter