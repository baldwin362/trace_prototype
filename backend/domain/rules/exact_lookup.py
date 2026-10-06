"""Finds the mapping entry that is exactly equal to a key."""


class ExactLookup:
    def __init__(self, entry_keys: list[str]):
        self.entry_keys = set(entry_keys)

    def find_matching_entry_keys(self, key: str) -> list[str]:
        """Returns the entry that is exactly equal to the key.

        Args:
            key: the text to check, for example a DNS verification name like "docusign".

        Returns:
            A list with the entry equal to the key, for example ['docusign'].
            An empty list if no entry is equal to it.

        Example:
            verification_lookup = ExactLookup(["docusign", "stripe-verification", "atlassian-domain-verification"])

            verification_lookup.find_matching_entry_keys("docusign")              # ['docusign']
            verification_lookup.find_matching_entry_keys("stripe-verification")   # ['stripe-verification']
            verification_lookup.find_matching_entry_keys("docusign-test")         # []
        """
        if key in self.entry_keys:
            return [key]
        return []
