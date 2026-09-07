from .interfaces import Agent
from typing import Dict, Any, List
import re


class TimelineAgent(Agent):
    def __init__(self):
        super().__init__('timeline')

    def handle(self, task: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Extract simple timeline events from text (date + snippet)
        text = task.get('text', '')
        events: List[Dict[str, Any]] = []
        for match in re.findall(r'(\d{4}-\d{2}-\d{2}).{0,100}', text):
            events.append({'date': match, 'note': f'Event near {match}'})
        for e in events:
            context.append('timeline', e)
        return {'events': events}
