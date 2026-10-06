"""Finds every mapping entry that appears anywhere inside a block of text.

This is a plain loop over the patterns, so it reads the text once per pattern. That is fine for a few dozen patterns.
"""


class SubstringScanner:
    def __init__(self, entry_keys: list[str]):
        self.entry_keys = entry_keys

    def find_matching_entry_keys(self, text: str) -> list[str]:
        """Returns every entry that appears somewhere in the text.

        Args:
            text: the text to search, for example the inline scripts of a web page.

        Returns:
            A list with every entry found in the text, for example ["fbq('init'", "_hsq.push"].
            An empty list if none of them appear.

        Example:
            script_scanner = SubstringScanner(["fbq('init'", "_hsq.push", "Sentry.init"])

            script_scanner.find_matching_entry_keys("fbq('init', '12345'); _hsq.push(['setPath', '/']);")   # ["fbq('init'", "_hsq.push"]
            script_scanner.find_matching_entry_keys("var cart = [];")                                       # []
        """
        return [entry_key for entry_key in self.entry_keys if entry_key in text]
