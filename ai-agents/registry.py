from typing import Dict, Optional
from .interfaces import Agent


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def all(self):
        return list(self._agents.values())
