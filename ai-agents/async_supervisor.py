import asyncio
import logging
from typing import Dict, Any, Optional
from .registry import AgentRegistry
from .context import SharedContext
from .. import database, models
from threading import Lock

logger = logging.getLogger('agents.async_supervisor')


class AsyncSupervisor:
    def __init__(self, registry: AgentRegistry, context: SharedContext, route_map: Dict[str, str] | None = None):
        self.registry = registry
        self.context = context
        self.route_map = route_map or {}

    async def _run_agent(self, agent, task: Dict[str, Any], timeout: Optional[float], retries: int = 1, retry_delay: float = 0.5):
        attempt = 0
        last_exc = None
        while attempt < retries:
            try:
                if asyncio.iscoroutinefunction(agent.handle):
                    coro = agent.handle(task, self.context)
                else:
                    # run blocking agent in threadpool
                    loop = asyncio.get_running_loop()
                    coro = await loop.run_in_executor(None, agent.handle, task, self.context)
                    return coro

                if timeout:
                    return await asyncio.wait_for(coro, timeout=timeout)
                else:
                    return await coro
            except Exception as e:
                last_exc = e
                logger.exception('agent %s failed on attempt %d', getattr(agent, 'name', '?'), attempt)
                attempt += 1
                if attempt < retries:
                    await asyncio.sleep(retry_delay)
        raise last_exc

    async def submit(self, task: Dict[str, Any], actor_id: Optional[str] = None, timeout: Optional[float] = None, retries: int = 1) -> Dict[str, Any]:
        # determine routing
        task_type = task.get('type')
        agent_name = self.route_map.get(task_type)
        if not agent_name:
            raise ValueError('no route for task type')
        agent = self.registry.get(agent_name)
        if not agent:
            raise ValueError('no agent registered')

        # audit: create audit log entry
        # thread-safe audit write
        db = database.SessionLocal()
        try:
            with database.DB_LOCK:
                al = models.AuditLog(actor_id=actor_id, action='agent.submit', target_type='task', target_id=task.get('id'), detail={'type': task_type, 'agent': agent_name})
                db.add(al)
                db.commit()
        finally:
            db.close()

        # execute agent with retries and timeout
        result = await self._run_agent(agent, task, timeout=timeout, retries=retries)

        # store in shared context
        self.context.append('tasks', {'type': task_type, 'agent': agent_name, 'result': result})

        # audit completion
        db = database.SessionLocal()
        try:
            with database.DB_LOCK:
                al = models.AuditLog(actor_id=actor_id, action='agent.completed', target_type='task', target_id=task.get('id'), detail={'type': task_type, 'agent': agent_name})
                db.add(al)
                db.commit()
        finally:
            db.close()

        return {'agent': agent_name, 'result': result}

    def submit_sync(self, *args, **kwargs):
        return asyncio.run(self.submit(*args, **kwargs))
