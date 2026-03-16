"""CardRepository — indexed, cache-backed card data access layer.

Single Responsibility: owns card data indexing and lookup.
Does NOT own cache lifecycle (TTL, disk persistence) — that stays in _core.py.
"""

from __future__ import annotations


class CardRepository:
    """Indexed card store. Built from snapshot data, provides O(1) lookups.

    Usage::

        repo = CardRepository()
        repo.load(cards_list)          # Build indexes from flat card list
        card = repo.get("uuid-here")   # O(1) by ID
        started = repo.by_status("started")  # O(1) by status
        repo.clear()                   # Drop all data
    """

    def __init__(self) -> None:
        self._cards: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self._by_status: dict[str, list[dict]] = {}
        self._by_deck: dict[str, list[dict]] = {}
        self._by_owner: dict[str, list[dict]] = {}
        self._deck_name_to_id: dict[str, str] = {}
        self._deck_id_to_name: dict[str, str] = {}

    def load(self, cards: list[dict]) -> None:
        """Rebuild all indexes from a card list.

        Called after cache warm or disk load. Replaces any existing data.
        """
        self._cards = [c for c in cards if isinstance(c, dict)]
        self._by_id = {}
        self._by_status = {}
        self._by_deck = {}
        self._by_owner = {}
        for card in self._cards:
            cid = card.get("id")
            if cid:
                self._by_id[cid] = card
            status = card.get("status", "")
            self._by_status.setdefault(status, []).append(card)
            # Normalize deck name: try both 'deck' and 'deck_name' keys
            deck = str(card.get("deck") or card.get("deck_name") or "").lower()
            if deck:
                self._by_deck.setdefault(deck, []).append(card)
            # Normalize owner: try both 'owner' and 'owner_name' keys
            owner = str(card.get("owner") or card.get("owner_name") or "unassigned").lower()
            self._by_owner.setdefault(owner, []).append(card)

    def load_decks(self, decks: list[dict]) -> None:
        """Build deck name→ID and ID→name mappings from deck list."""
        self._deck_name_to_id = {}
        self._deck_id_to_name = {}
        for deck in decks:
            if not isinstance(deck, dict):
                continue
            did = deck.get("id")
            name = deck.get("title") or deck.get("name") or ""
            if did and name:
                self._deck_name_to_id[name.lower()] = did
                self._deck_id_to_name[did] = name

    def deck_id_for(self, name: str) -> str | None:
        """Resolve deck name to ID (case-insensitive). Returns None if unknown."""
        return self._deck_name_to_id.get(name.lower())

    def deck_name_for(self, deck_id: str) -> str | None:
        """Resolve deck ID to name. Returns None if unknown."""
        return self._deck_id_to_name.get(deck_id)

    def clear(self) -> None:
        """Drop all data and indexes."""
        self._cards.clear()
        self._by_id.clear()
        self._by_status.clear()
        self._by_deck.clear()
        self._by_owner.clear()
        self._deck_name_to_id.clear()
        self._deck_id_to_name.clear()

    @property
    def all_cards(self) -> list[dict]:
        """All cards in load order."""
        return self._cards

    @property
    def count(self) -> int:
        """Total number of loaded cards."""
        return len(self._cards)

    def get(self, card_id: str) -> dict | None:
        """O(1) lookup by card UUID. Returns None if not found."""
        return self._by_id.get(card_id)

    def by_status(self, status: str) -> list[dict]:
        """O(1) lookup by status. Returns empty list if no matches."""
        return self._by_status.get(status, [])

    def by_deck(self, deck_name: str) -> list[dict]:
        """O(1) lookup by deck name (case-insensitive). Returns empty list if no matches."""
        return self._by_deck.get(deck_name.lower(), [])

    def by_owner(self, owner_name: str) -> list[dict]:
        """O(1) lookup by owner name (case-insensitive). Returns empty list if no matches."""
        return self._by_owner.get(owner_name.lower(), [])

    def search(self, text: str) -> list[dict]:
        """Full-text search over title and content fields.

        Linear scan — use indexed lookups when possible.
        """
        text_lower = text.lower()
        return [
            c
            for c in self._cards
            if text_lower in str(c.get("title", "")).lower()
            or text_lower in str(c.get("content", "")).lower()
        ]
