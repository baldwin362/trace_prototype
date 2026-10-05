"""The base exception for every failure an engine can report. It carries the engine name and a message."""


class ScanError(Exception):
    engine = "unknown"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
