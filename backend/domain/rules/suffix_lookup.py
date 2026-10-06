"""Finds the longest mapping entry that a hostname ends with, comparing whole labels.

"kate.ns.cloudflare.com" matches the entry "ns.cloudflare.com", but "evilcloudflare.com" does not match "cloudflare.com".

The entries are stored in a trie, one node per label, read from right to left.
The entries "vercel.app" and "ns.cloudflare.com" give this trie:

    root
     ├── app
     │    └── vercel          entry_key = "vercel.app"
     └── com
          └── cloudflare
               └── ns         entry_key = "ns.cloudflare.com"
"""


class TrieNode:
    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        self.entry_key: str | None = None


class SuffixLookup:
    def __init__(self, entry_keys: list[str]):
        self.root = TrieNode()
        for entry_key in entry_keys:
            self.add_entry(entry_key)

    def add_entry(self, entry_key: str) -> None:
        """Adds one hostname to the trie, one node per label, starting from the last label.

        Args:
            entry_key: the hostname to add, for example "ns.cloudflare.com".

        Example:
            nameserver_lookup = SuffixLookup([])
            nameserver_lookup.add_entry("ns.cloudflare.com")
            # root → "com" → "cloudflare" → "ns" (entry_key = "ns.cloudflare.com")
        """
        current_node = self.root
        for label in reversed(entry_key.split(".")):
            if label not in current_node.children:
                current_node.children[label] = TrieNode()
            current_node = current_node.children[label]
        current_node.entry_key = entry_key

    def find_matching_entry_keys(self, key: str) -> list[str]:
        """Returns the longest entry that the hostname ends with.

        Args:
            key: the hostname to check, for example a nameserver like "kate.ns.cloudflare.com".

        Returns:
            A list with the entry the hostname ends with, for example ['ns.cloudflare.com'].
            An empty list if it ends with none of them.

        Example:
            nameserver_lookup = SuffixLookup(["ns.cloudflare.com", "awsdns-54.net"])

            nameserver_lookup.find_matching_entry_keys("kate.ns.cloudflare.com")   # ['ns.cloudflare.com']
            nameserver_lookup.find_matching_entry_keys("ns-947.awsdns-54.net")     # ['awsdns-54.net']
            nameserver_lookup.find_matching_entry_keys("ns1.evilcloudflare.com")   # []
        """
        current_node = self.root
        longest_matching_entry_key = None
        for label in reversed(key.split(".")):
            if label not in current_node.children:
                break
            current_node = current_node.children[label]
            if current_node.entry_key is not None:
                longest_matching_entry_key = current_node.entry_key

        if longest_matching_entry_key is None:
            return []
        return [longest_matching_entry_key]
