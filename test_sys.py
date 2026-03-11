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


# ================================
# AC1: Capacity less than 0 rejected
# ================================

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
    er.register("u3")
    er.register("u4")

    er.cancel("u1")

    snap = er.snapshot()

    assert snap["registered"] == ["u2", "u3"]
    assert snap["waitlist"] == ["u4"]
    assert er.status("u3") == UserStatus("registered")
    

# =========================
# AC3:  Duplicate register rejected
# =========================
def test_ac3_duplicate_register_registered_and_waitlisted():
    e_r = EventRegistration(capacity=1)
    e_r.register("userA")    
    with pytest.raises(DuplicateRequest):
        e_r.register("userA")
    
    e_r.register("userB")

    with pytest.raises(DuplicateRequest):
        e_r.register("userB")

# =========================
# AC4: At capacity -> user added to end of waitlist
# =========================

def test_ac4_register_when_full_goes_to_end_of_waitlist():
    e_r= EventRegistration(capacity=1)

    e_r.register("u1")
    e_r.register("u2")
    e_r.register("u3")

    snap = e_r.snapshot()

    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u2", "u3"]

# =========================
# AC5: Waitlisted cancel preserves FIFO order

def test_ac5_cancel_waitlisted_preserves_fifo():
    e_r = EventRegistration(capacity=1)

    e_r.register("u1")
    e_r.register("u2")
    e_r.register("u3")
    e_r.register("u4")

    e_r.cancel("u3")

    snap = e_r.snapshot()
    assert snap["waitlist"] == ["u2", "u4"]
    assert e_r.status("u3")== UserStatus("none")


# =========================
# AC6: Multiple users added FIFO when full
# =========================

def test_ac6_multiple_waitlist_fifo_order():
    e_r = EventRegistration(capacity=1)

    e_r.register("u1")
    
    e_r.register("a2")
    e_r.register("u3")
    e_r.register("u4")
    
    snap = e_r.snapshot()

    assert snap["waitlist"] == ["a2", "u3", "u4"]

# =========================
# AC7: Empty string registration is rejected
# =========================

def test_ac7_empty_user_id_rejected():

    e_r = EventRegistration(capacity=1)

    with pytest.raises(ValueError):
        e_r.register("")

# =========================
# AC9: Cancel waitlisted when full results in no promotion
# =========================
def test_ac9_cancel_waitlisted_does_not_trigger_promotion():

    e_r = EventRegistration(capacity=1)

    e_r.register("a1")
    e_r.register("a2")
    e_r.register("a3")

    e_r.cancel("a2")

    snap = e_r.snapshot()

    assert snap["registered"] == ["a1"]
    assert snap["waitlist"] == ["a3"]

# =========================
# AC10: Cancelling non-existent user raises NotFound

def test_ac10_cancel_nonexistent_user_raises_notfound():
    e_reg = EventRegistration(capacity=1)

    e_reg.register("Reginald")

    with pytest.raises(NotFound):
        e_reg.cancel("Drake")
    
    snap = e_reg.snapshot()
    assert snap["registered"] == ["Reginald"]

# =========================
# AC11: Case insensitive duplicate rejected
# =========================

def test_ac11_case_insensitive_duplicate():
    e_r = EventRegistration(capacity=1)
    
    e_r.register("OrvillePeck")

    with pytest.raises(DuplicateRequest):
        e_r.register("orvillePECK")
    
    with pytest.raises(DuplicateRequest):
        e_r.register("ORVILLEPECK")

# =========================
# AC12: Capacity cannot be changed after initialization
# =========================

def test_ac12_capacity_immutable():
    e_r = EventRegistration(capacity=3)

    with pytest.raises(AttributeError):
        e_r.capacity = 8

####################
# LAB9 TESTS
#####################

#Covers C1, AC1
def test_ac1_cancel_registered_auto_promotes_earliest_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")
    er.register("u3")

    er.cancel("u1")

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)


#Covers C2, AC2
def test_ac2_cancel_shows_who_was_promoted_and_why(capsys):
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")

    capsys.readouterr()  # clear prior output
    er.cancel("u1")
    out = capsys.readouterr().out.strip()

    assert "u1" in out
    assert "u2" in out
    assert "promoted" in out.lower()

#Covers C3, AC3
def test_ac3_cancel_promotion_message_under_100_chars(capsys):
    er = EventRegistration(capacity=1)
    er.register("Alice")
    er.register("Bob")

    capsys.readouterr()
    er.cancel("Alice")
    out = capsys.readouterr().out.strip()

    assert "Alice"[:8] in out or "Alice" in out
    assert "Bob"[:8] in out or "Bob" in out
    assert len(out) <= 100

#Covers C4, AC3
def test_ac4_duplicate_register_outputs_explanation():
    er = EventRegistration(capacity=1)
    er.register("u1")

    with pytest.raises(DuplicateRequest) as excinfo:
        er.register("u1")

    assert "already" in str(excinfo.value).lower() or "not registered" in str(excinfo.value).lower()

#Covers C5, AC5
def test_ac5_capacity_zero_places_all_users_on_waitlist_fifo():
    er = EventRegistration(capacity=0)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")

    assert s1 == UserStatus("waitlisted", 1)
    assert s2 == UserStatus("waitlisted", 2)
    assert s3 == UserStatus("waitlisted", 3)

    snap = er.snapshot()
    assert snap["registered"] == []
    assert snap["waitlist"] == ["u1", "u2", "u3"]

#Covers C6, AC6
def test_ac6_simultaneous_different_users_processed_in_ascii_lexicographic_order():
    er = EventRegistration(capacity=2)

    er.begin_batch(timestamp=10)
    er.register("Bob")
    er.register("Alice")
    er.register("Charlie")
    er.end_batch()

    snap = er.snapshot()
    assert snap["registered"] == ["Alice", "Bob"]
    assert snap["waitlist"] == ["Charlie"]

#Covers C7, AC7
def test_ac7_simultaneous_same_user_processed_register_then_cancel_then_query():
    er = EventRegistration(capacity=1)

    er.begin_batch(timestamp=20)
    er.register("Mia")
    er.cancel("Mia")
    er.status("Mia")
    results = er.end_batch()

    assert results[0][0] == "register"
    assert results[1][0] == "cancel"
    assert results[2][0] == "query"
    assert results[2][2] == UserStatus("none")
    assert er.snapshot() == {"registered": [], "waitlist": []}


#Covers C8, AC8
def test_ac8_single_action_produces_at_most_one_output_message(capsys):
    er = EventRegistration(capacity=1)

    capsys.readouterr()
    er.register("u1")
    out = capsys.readouterr().out.strip().splitlines()

    assert len(out) == 1

#Covers C9, AC9
def test_ac9_same_timestamp_bob_and_alice_alice_registered_bob_waitlisted():
    er = EventRegistration(capacity=1)

    er.begin_batch(timestamp=99)
    er.register("Bob")
    er.register("Alice")
    results = er.end_batch()

    snap = er.snapshot()
    assert snap["registered"] == ["Alice"]
    assert snap["waitlist"] == ["Bob"]

    assert results[0][0] == "register"
    assert results[0][1] == "Alice"
    assert results[0][2] == UserStatus("registered")

    assert results[1][0] == "register"
    assert results[1][1] == "Bob"
    assert results[1][2] == UserStatus("waitlisted", 1)

#Covers EC6
def test_ec6_simultaneous_waitlist_cancellations_removed_in_lexicographic_order_preserving_remaining_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("Charlie")
    er.register("Bob")
    er.register("Alice")

    # initial waitlist order is arrival order
    assert er.snapshot()["waitlist"] == ["Charlie", "Bob", "Alice"]

    er.begin_batch(timestamp=4)
    er.cancel("Bob")
    er.cancel("Alice")
    er.end_batch()

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["Charlie"]

#Covers EC7
def test_ec7_simultaneous_registered_cancellations_promote_waitlist_in_fifo_order():
    er = EventRegistration(capacity=2)
    er.register("u1")
    er.register("u2")
    er.register("w1")
    er.register("w2")
    er.register("w3")

    er.begin_batch(timestamp=5)
    er.cancel("u2")
    er.cancel("u1")
    er.end_batch()

    snap = er.snapshot()
    assert snap["registered"] == ["w1", "w2"]
    assert snap["waitlist"] == ["w3"]

#tests ec8
def test_ec8_same_timestamp_cancel_and_register_different_users_deterministic_outcome():
    er = EventRegistration(capacity=1)
    er.register("M")
    er.register("User1")   # earliest waitlist

    er.begin_batch(timestamp=6)
    er.cancel("M")
    er.register("Zed")
    er.end_batch()

    snap = er.snapshot()
    assert snap["registered"] == ["User1"]
    assert snap["waitlist"] == ["Zed"]

#Covers EC9
def test_ec9_same_user_cancel_and_query_same_timestamp_query_returns_none():
    er = EventRegistration(capacity=1)
    er.register("u1")

    er.begin_batch(timestamp=7)
    er.cancel("u1")
    er.status("u1")
    results = er.end_batch()

    assert results[0][0] == "cancel"
    assert results[1][0] == "query"
    assert results[1][2] == UserStatus("none")


