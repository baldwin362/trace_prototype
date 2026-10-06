"""Finds the longest mapping entry that a key starts with, so "server|nginx/1.18" matches the entry "server|nginx"."""


class PrefixLookup:
    def __init__(self, entry_keys: list[str]):
        self.entry_keys = entry_keys

    def find_matching_entry_keys(self, key: str) -> list[str]:
        """Returns the entry that the key starts with.

        Args:
            key: the text to check, for example a cookie name like "intercom-session-abc123".

        Returns:
            A list with the entry that the key starts with name starts, for example ['intercom-session'].
            An empty list if it starts with none of them.

        Example:
            cookie_lookup = PrefixLookup(["_ga", "_gid", "intercom-session", "__stripe_mid"])

            cookie_lookup.find_matching_entry_keys("intercom-session-abc123")   # ['intercom-session']
            cookie_lookup.find_matching_entry_keys("_ga_XYZ123")               # ['_ga']
            cookie_lookup.find_matching_entry_keys("PHPSESSID")                # []
        """
        matching_entry_keys = [
            entry_key for entry_key in self.entry_keys if key.startswith(entry_key)
        ]
        if not matching_entry_keys:
            return []
        return [max(matching_entry_keys, key=len)]
