## Student Name: Noah Vukosa
## Student ID: 214415525

from dataclasses import dataclass
from typing import List, Optional


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
    position: 1-based waitlist position if waitlisted; otherwise None
    """
    state: str
    position: Optional[int] = None


class EventRegistration:
    """
    Event registration system with:
      - Fixed capacity (immutable)
      - FIFO registered list
      - FIFO waitlist
      - Case-insensitive user handling
      - Deterministic promotion
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("Capacity must be >= 0")

        self._capacity = capacity  # immutable after initialization
        self._registered: List[str] = []
        self._waitlist: List[str] = []

        # maps normalized user_id -> original casing user_id
        self._users = {}

    @property
    def capacity(self) -> int:
        """Read-only capacity property (cannot be modified)."""
        return self._capacity

    def _normalize(self, user_id: str) -> str:
        if not isinstance(user_id, str) or user_id == "":
            raise ValueError("user_id must be a non-empty string")
        return user_id.lower()

    def register(self, user_id: str) -> UserStatus:
        normalized = self._normalize(user_id)

        if normalized in self._users:
            raise DuplicateRequest("User already registered or waitlisted")

        # Capacity available
        if len(self._registered) < self._capacity:
            self._registered.append(user_id)
            self._users[normalized] = user_id
            return UserStatus("registered")

        # Capacity full → waitlist
        self._waitlist.append(user_id)
        self._users[normalized] = user_id
        return UserStatus("waitlisted", len(self._waitlist))

    def cancel(self, user_id: str) -> None:
        normalized = self._normalize(user_id)

        if normalized not in self._users:
            raise NotFound("User not found")

        original = self._users[normalized]

        # If registered
        if original in self._registered:
            self._registered.remove(original)
            del self._users[normalized]

            # Promote earliest waitlisted if capacity allows
            if self._waitlist and len(self._registered) < self._capacity:
                promoted = self._waitlist.pop(0)
                promoted_norm = promoted.lower()
                self._registered.append(promoted)
                self._users[promoted_norm] = promoted

        # If waitlisted
        else:
            self._waitlist.remove(original)
            del self._users[normalized]

    def status(self, user_id: str) -> UserStatus:
        normalized = self._normalize(user_id)

        if normalized not in self._users:
            return UserStatus("none")

        original = self._users[normalized]

        if original in self._registered:
            return UserStatus("registered")

        # Must be waitlisted
        position = self._waitlist.index(original) + 1
        return UserStatus("waitlisted", position)

    def snapshot(self) -> dict:
        return {
            "registered": list(self._registered),
            "waitlist": list(self._waitlist),
        }