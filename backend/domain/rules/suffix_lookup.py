"""Finds the longest mapping entry that a hostname ends with, comparing whole labels.

"kate.ns.cloudflare.com" matches the entry "ns.cloudflare.com", but "evilcloudflare.com" does not match "cloudflare.com".
Entries are stored in a tree keyed on hostname labels read from right to left, so a lookup walks at most one step per label.
"""

END_OF_ENTRY = ""


class SuffixLookup:
    def __init__(self, entry_keys: list[str]):
        self.label_tree: dict = {}
        for entry_key in entry_keys:
            current_node = self.label_tree
            for label in reversed(entry_key.split(".")):
                current_node = current_node.setdefault(label, {})
            current_node[END_OF_ENTRY] = entry_key

    def find_matching_entry_keys(self, key: str) -> list[str]:
        current_node = self.label_tree
        longest_matching_entry_key = None
        for label in reversed(key.split(".")):
            if label not in current_node:
                break
            current_node = current_node[label]
            longest_matching_entry_key = current_node.get(END_OF_ENTRY, longest_matching_entry_key)
        if longest_matching_entry_key is None:
            return []
        return [longest_matching_entry_key]
