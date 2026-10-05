"""Finds every mapping entry that appears anywhere inside a block of text.

This is a plain loop over the patterns, so it reads the text once per pattern. That is fine for a few dozen patterns.
"""


class SubstringScanner:
    def __init__(self, entry_keys: list[str]):
        self.entry_keys = entry_keys

    def find_matching_entry_keys(self, text: str) -> list[str]:
        return [entry_key for entry_key in self.entry_keys if entry_key in text]
