"""Finds the longest mapping entry that a key starts with, so "server|nginx/1.18" matches the entry "server|nginx"."""


class PrefixLookup:
    def __init__(self, entry_keys: list[str]):
        self.entry_keys = entry_keys

    def find_matching_entry_keys(self, key: str) -> list[str]:
        matching_entry_keys = [entry_key for entry_key in self.entry_keys if key.startswith(entry_key)]
        if not matching_entry_keys:
            return []
        return [max(matching_entry_keys, key=len)]
