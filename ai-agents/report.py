from .interfaces import Agent
from typing import Dict, Any


class ReportAgent(Agent):
    def __init__(self):
        super().__init__('report')

    def handle(self, task: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Compose a simple report from shared context
        snapshot = context.snapshot()
        entities = snapshot.get('entities', [])
        timeline = snapshot.get('timeline', [])
        correlations = snapshot.get('correlations', {})
        report = {
            'entities_count': len(entities),
            'timeline_events': len(timeline),
            'correlations': correlations,
            'summary': f"{len(entities)} entities, {len(timeline)} timeline events",
        }
        context.set('last_report', report)
        return report
