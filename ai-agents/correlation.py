from .interfaces import Agent
from typing import Dict, Any, List


class CorrelationAgent(Agent):
    def __init__(self):
        super().__init__('correlation')

    def handle(self, task: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # simple correlation: find overlapping entity names across context
        entities = context.get('entities', []) or []
        by_name = {}
        for e in entities:
            by_name.setdefault(e['name'], []).append(e)
        correlated = {name: len(items) for name, items in by_name.items() if len(items) > 1}
        context.set('correlations', correlated)
        return {'correlations': correlated}
