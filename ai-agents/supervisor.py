from typing import Dict, Any, Callable
from .registry import AgentRegistry
from .context import SharedContext
import threading
import uuid


class Supervisor:
    """Orchestrates tasks among registered agents.

    Routing is intentionally simple but pluggable: tasks must include a
    `type` key that maps to an agent name via `route_map`.
    """

    def __init__(self, registry: AgentRegistry, context: SharedContext, route_map: Dict[str, str] | None = None):
        self.registry = registry
        self.context = context
        # default routing: task.type -> agent name
        self.route_map = route_map or {
            'investigate': 'detective',
            'timeline': 'timeline',
            'correlate': 'correlation',
            'report': 'report',
        }
        self._lock = threading.Lock()

    def submit(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a task and synchronously execute the routed agent.

        Returns the agent result and stores it in shared context under
        `tasks` list for later inspection.
        """
        task_id = task.get('id') or str(uuid.uuid4())
        task_type = task.get('type')
        agent_name = self.route_map.get(task_type)
        if not agent_name:
            raise ValueError(f'no route for task type: {task_type}')
        agent = self.registry.get(agent_name)
        if not agent:
            raise ValueError(f'no agent registered with name: {agent_name}')

        # execute agent and capture result
        result = agent.handle(task, self.context)

        # persist to context
        self.context.append('tasks', {'id': task_id, 'type': task_type, 'agent': agent_name, 'result': result})
        return {'id': task_id, 'agent': agent_name, 'result': result}
