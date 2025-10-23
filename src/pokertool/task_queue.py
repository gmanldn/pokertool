"""Task Queue System for AI Agents"""
from queue import PriorityQueue, Queue
from typing import Optional, List
from dataclasses import dataclass, field
from .todo_parser import Task, Priority

@dataclass(order=True)
class QueuedTask:
    priority: int = field(compare=True)
    task: Task = field(compare=False)

class AgentTaskQueue:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.queue = PriorityQueue()
        self.in_progress: Optional[Task] = None
    
    def add_task(self, task: Task):
        priority_num = task.priority.value if hasattr(task, 'priority') else 3
        self.queue.put(QueuedTask(priority_num, task))
    
    def get_next_task(self) -> Optional[Task]:
        if not self.queue.empty():
            self.in_progress = self.queue.get().task
            return self.in_progress
        return None
    
    def mark_complete(self):
        self.in_progress = None
    
    def size(self) -> int:
        return self.queue.qsize()
