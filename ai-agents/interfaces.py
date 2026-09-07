from abc import ABC, abstractmethod
from typing import Any, Dict


class Agent(ABC):
    """Base interface for orchestration agents."""

    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def handle(self, task: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle a task and return a serializable result dict."""
        raise NotImplementedError()
