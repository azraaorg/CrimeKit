from .interfaces import Agent
from typing import Dict, Any
import re


class DetectiveAgent(Agent):
    def __init__(self):
        super().__init__('detective')

    def handle(self, task: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # naive entity extraction: proper names (capitalized words) and dates
        text = task.get('text', '')
        names = re.findall(r'\b[A-Z][a-z]{1,}\b', text)
        dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', text)
        entities = [{'name': n, 'type': 'proper_name'} for n in set(names)]
        for d in set(dates):
            entities.append({'name': d, 'type': 'date'})
        # store entities in shared context
        for e in entities:
            context.append('entities', e)
        return {'entities': entities}
