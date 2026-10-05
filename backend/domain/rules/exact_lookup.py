"""Finds the mapping entry that is exactly equal to a key."""


class ExactLookup:
    def __init__(self, entry_keys: list[str]):
        self.entry_keys = set(entry_keys)

    def find_matching_entry_keys(self, key: str) -> list[str]:
        if key in self.entry_keys:
            return [key]
        return []
