## Student Name: Noah Vukosa
## Student ID: 214415525

from dataclasses import dataclass
from functools import cmp_to_key
from typing import List, Optional, Tuple, Any


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation."""
    pass


@dataclass(frozen=True)
class UserStatus:
    """
    state:
      - "registered"
      - "waitlisted"
      - "none"
    position:
      - 1-based waitlist position if waitlisted
      - otherwise None
    """
    state: str
    position: Optional[int] = None


@dataclass(frozen=True)
class _QueuedAction:
    action: str          # "register", "cancel", "query"
    user_id: str
    order: int           # original queue order for deterministic final tie-break


class EventRegistration:
    """
    Event registration system with:
      - Fixed capacity (immutable)
      - FIFO registered list
      - FIFO waitlist
      - Case-insensitive user handling
      - Deterministic promotion
      - Batch support for simulating simultaneous requests
    """

    _ACTION_PRIORITY = {
        "register": 0,
        "cancel": 1,
        "query": 2,
    }

    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("Capacity must be >= 0")

        self._capacity = capacity
        self._registered: List[str] = []
        self._waitlist: List[str] = []

        # normalized user_id -> original casing
        self._users = {}

        # batching state for simulating simultaneous requests
        self._batch_mode = False
        self._batch_timestamp: Optional[Any] = None
        self._batch_queue: List[_QueuedAction] = []
        self._batch_results: List[Tuple[str, str, Optional[UserStatus]]] = []

    @property
    def capacity(self) -> int:
        """Read-only capacity property."""
        return self._capacity

    def _normalize(self, user_id: str) -> str:
        if not isinstance(user_id, str) or user_id == "":
            raise ValueError("user_id must be a non-empty string")
        return user_id.lower()

    def _short_name(self, user_id: str) -> str:
        # EC10: keep messages short by using only first 8 chars when needed
        return user_id[:8]

    def _emit(self, message: str) -> None:
        # One concise message per processed action, max 100 chars
        msg = " ".join(message.split())
        print(msg[:100])

    def _compare_simultaneous(self, left: _QueuedAction, right: _QueuedAction) -> int:
        """
        For same timestamp:
        1. same normalized user_id -> register, cancel, query
        2. different user_ids -> ASCII lexicographic order of user_id
        3. original queue order as final deterministic tie-break
        """
        left_norm = self._normalize(left.user_id)
        right_norm = self._normalize(right.user_id)

        if left_norm == right_norm:
            lp = self._ACTION_PRIORITY[left.action]
            rp = self._ACTION_PRIORITY[right.action]
            if lp < rp:
                return -1
            if lp > rp:
                return 1
        else:
            if left.user_id < right.user_id:
                return -1
            if left.user_id > right.user_id:
                return 1

        if left.order < right.order:
            return -1
        if left.order > right.order:
            return 1
        return 0

    def begin_batch(self, timestamp: Any) -> None:
        """
        Start collecting requests that should be treated as simultaneous.
        All actions queued until end_batch() share the same timestamp.
        """
        if self._batch_mode:
            raise ValueError("Batch already active")

        self._batch_mode = True
        self._batch_timestamp = timestamp
        self._batch_queue = []
        self._batch_results = []

    def end_batch(self) -> List[Tuple[str, str, Optional[UserStatus]]]:
        """
        Process all queued actions as simultaneous requests and return results.
        Each result is: (action, user_id, UserStatus or None)
        """
        if not self._batch_mode:
            raise ValueError("No active batch")

        ordered = sorted(self._batch_queue, key=cmp_to_key(self._compare_simultaneous))
        results: List[Tuple[str, str, Optional[UserStatus]]] = []

        try:
            for item in ordered:
                if item.action == "register":
                    status = self._register_now(item.user_id)
                    results.append(("register", item.user_id, status))
                elif item.action == "cancel":
                    self._cancel_now(item.user_id)
                    results.append(("cancel", item.user_id, None))
                elif item.action == "query":
                    status = self._status_now(item.user_id)
                    results.append(("query", item.user_id, status))
                else:
                    raise ValueError("Unknown action")
        finally:
            self._batch_mode = False
            self._batch_timestamp = None
            self._batch_queue = []

        self._batch_results = results
        return list(results)

    def last_batch_results(self) -> List[Tuple[str, str, Optional[UserStatus]]]:
        return list(self._batch_results)

    def register(self, user_id: str) -> UserStatus:
        if self._batch_mode:
            self._normalize(user_id)  # validate immediately
            self._batch_queue.append(_QueuedAction("register", user_id, len(self._batch_queue)))
            # queued only; final result available after end_batch()
            return UserStatus("none")

        return self._register_now(user_id)

    def cancel(self, user_id: str) -> None:
        if self._batch_mode:
            self._normalize(user_id)  # validate immediately
            self._batch_queue.append(_QueuedAction("cancel", user_id, len(self._batch_queue)))
            return

        self._cancel_now(user_id)

    def status(self, user_id: str) -> UserStatus:
        if self._batch_mode:
            self._normalize(user_id)  # validate immediately
            self._batch_queue.append(_QueuedAction("query", user_id, len(self._batch_queue)))
            # queued only; final query result available after end_batch()
            return UserStatus("none")

        return self._status_now(user_id)

    def _register_now(self, user_id: str) -> UserStatus:
        normalized = self._normalize(user_id)

        if normalized in self._users:
            raise DuplicateRequest(
                f"User {self._short_name(user_id)} not registered: already in system"
            )

        if len(self._registered) < self._capacity:
            self._registered.append(user_id)
            self._users[normalized] = user_id
            self._emit(f"Registered {self._short_name(user_id)}")
            return UserStatus("registered")

        self._waitlist.append(user_id)
        self._users[normalized] = user_id
        self._emit(f"Waitlisted {self._short_name(user_id)} pos {len(self._waitlist)}")
        return UserStatus("waitlisted", len(self._waitlist))

    def _cancel_now(self, user_id: str) -> None:
        normalized = self._normalize(user_id)

        if normalized not in self._users:
            raise NotFound(f"Cancel rejected: {self._short_name(user_id)} not found")

        original = self._users[normalized]

        if original in self._registered:
            self._registered.remove(original)
            del self._users[normalized]

            if self._waitlist and len(self._registered) < self._capacity:
                promoted = self._waitlist.pop(0)
                promoted_norm = self._normalize(promoted)
                self._registered.append(promoted)
                self._users[promoted_norm] = promoted

                self._emit(
                    f"Cancelled {self._short_name(original)}; promoted {self._short_name(promoted)}"
                )
            else:
                self._emit(f"Cancelled {self._short_name(original)}")
            return

        self._waitlist.remove(original)
        del self._users[normalized]
        self._emit(f"Removed waitlist {self._short_name(original)}")

    def _status_now(self, user_id: str) -> UserStatus:
        normalized = self._normalize(user_id)

        if normalized not in self._users:
            self._emit(f"Status {self._short_name(user_id)} none")
            return UserStatus("none")

        original = self._users[normalized]

        if original in self._registered:
            self._emit(f"Status {self._short_name(original)} registered")
            return UserStatus("registered")

        position = self._waitlist.index(original) + 1
        self._emit(f"Status {self._short_name(original)} waitlist {position}")
        return UserStatus("waitlisted", position)

    def snapshot(self) -> dict:
        return {
            "registered": list(self._registered),
            "waitlist": list(self._waitlist),
        }