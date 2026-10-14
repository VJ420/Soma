"""
Soma V2 Recursive Agentic Architecture (SMAA-V2).
Tier 3 Hierarchical Swarm Decomposition:
Master Orchestrator -> Regional Worker Cells -> Micro-Assistant Cells.
"""
import time
import json
import uuid
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

@dataclass(slots=True)
class CellTask:
    id: str
    tier: str  # "MASTER", "WORKER", "ASSISTANT"
    name: str
    goal: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    subtasks: List['CellTask'] = field(default_factory=list)
    result: Any = None
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    duration_ms: float = 0.0

class TaskDecomposer:
    """
    Intelligently breaks down macro-level program intentions into
    3-Tier Hierarchical Execution Blocks:
    Master -> 4 Regional Workers -> 4 Micro-Assistants each (16 leaves).
    """
    @staticmethod
    def decompose(macro_goal: str, payload: Any = None, workers_count: int = 4, assistants_per_worker: int = 4) -> CellTask:
        root_id = f"cell_master_{uuid.uuid4().hex[:6]}"
        root_task = CellTask(
            id=root_id,
            tier="MASTER",
            name="MasterOrchestratorCell",
            goal=macro_goal,
            inputs={"payload": payload, "workers_count": workers_count, "assistants_per_worker": assistants_per_worker}
        )

        items = payload if isinstance(payload, list) else list(range(1, 1001))
        total_items = len(items)
        worker_chunk_size = max(1, math.ceil(total_items / workers_count))

        for w_idx in range(workers_count):
            w_start = w_idx * worker_chunk_size
            w_end = min(total_items, (w_idx + 1) * worker_chunk_size)
            worker_items = items[w_start:w_end]

            if not worker_items:
                continue

            worker_id = f"cell_worker_{w_idx}_{uuid.uuid4().hex[:4]}"
            worker_task = CellTask(
                id=worker_id,
                tier="WORKER",
                name=f"WorkerCell_{w_idx}",
                goal=f"Supervise and subdivide partition {w_idx} [{w_start}:{w_end}]",
                inputs={"partition_index": w_idx, "items_count": len(worker_items)}
            )

            # Worker subdivides partition into Micro-Assistant chunks
            asst_chunk_size = max(1, math.ceil(len(worker_items) / assistants_per_worker))
            for a_idx in range(assistants_per_worker):
                a_start = a_idx * asst_chunk_size
                a_end = min(len(worker_items), (a_idx + 1) * asst_chunk_size)
                micro_chunk = worker_items[a_start:a_end]

                if not micro_chunk:
                    continue

                asst_id = f"cell_asst_{w_idx}_{a_idx}_{uuid.uuid4().hex[:4]}"
                asst_task = CellTask(
                    id=asst_id,
                    tier="ASSISTANT",
                    name=f"Worker_{w_idx}_MicroAssistant_{a_idx}",
                    goal=f"Execute vector operations on sub-slice [{w_start + a_start}:{w_start + a_end}]",
                    inputs={"chunk": micro_chunk, "offset": w_start + a_start}
                )
                worker_task.subtasks.append(asst_task)

            root_task.subtasks.append(worker_task)

        return root_task

class MicroAssistantWorker:
    """
    Leaf execution unit that computes sub-chunk vector transformations in isolation.
    """
    def __init__(self, task: CellTask):
        self.task = task

    def execute(self) -> CellTask:
        self.task.status = "RUNNING"
        t0 = time.perf_counter()

        chunk = self.task.inputs.get("chunk", [])
        # Tight vectorized loop
        transformed = [x * x + 7 for x in chunk]
        total_sum = sum(transformed)

        t1 = time.perf_counter()
        self.task.duration_ms = (t1 - t0) * 1000
        self.task.status = "COMPLETED"
        self.task.result = {
            "count": len(chunk),
            "sum": total_sum,
            "sample": transformed[:3] if transformed else []
        }
        return self.task

class ParallelCellEngine:
    """Compatibility name for older swarm scripts. Soma has one swarm coordinator."""

    def __init__(self, max_workers: int = 4, assistants_per_worker: int = 4):
        self._coordinator = None
        self.max_workers = max_workers
        self.assistants_per_worker = assistants_per_worker

    def run_goal(self, goal: str, payload: Any = None) -> Dict[str, Any]:
        from agentic_infra import HierarchicalSwarmCoordinator
        self._coordinator = HierarchicalSwarmCoordinator(
            workers_count=self.max_workers,
            assistants_per_worker=self.assistants_per_worker,
        )
        return self._coordinator.run_swarm(goal, payload)


class HierarchicalSwarmCoordinator:
    """
    Orchestrates the complete 3-Tier Hierarchical Swarm across threads and fibers.
    """
    def __init__(self, workers_count: int = 4, assistants_per_worker: int = 4):
        self.workers_count = workers_count
        self.assistants_per_worker = assistants_per_worker

    def run_swarm(self, macro_goal: str, payload: Any = None) -> Dict[str, Any]:
        t0 = time.perf_counter()
        master_task = TaskDecomposer.decompose(
            macro_goal,
            payload,
            workers_count=self.workers_count,
            assistants_per_worker=self.assistants_per_worker
        )
        master_task.status = "RUNNING"

        # Collect all micro-assistant leaf tasks
        assistant_tasks: List[CellTask] = []
        for worker in master_task.subtasks:
            worker.status = "RUNNING"
            for asst in worker.subtasks:
                assistant_tasks.append(asst)

        # Execute micro-assistant leaves in parallel
        total_leaves = len(assistant_tasks)
        with ThreadPoolExecutor(max_workers=max(1, total_leaves)) as pool:
            futures = [pool.submit(MicroAssistantWorker(task).execute) for task in assistant_tasks]
            for f in as_completed(futures):
                _ = f.result()

        # Bottom-up reduction: Assistant -> Worker -> Master
        global_sum = 0
        global_count = 0
        for worker in master_task.subtasks:
            worker_sum = sum(asst.result["sum"] for asst in worker.subtasks if asst.result)
            worker_count = sum(asst.result["count"] for asst in worker.subtasks if asst.result)
            worker.result = {"worker_sum": worker_sum, "worker_count": worker_count}
            worker.status = "COMPLETED"
            global_sum += worker_sum
            global_count += worker_count

        t1 = time.perf_counter()
        master_task.duration_ms = (t1 - t0) * 1000
        master_task.status = "COMPLETED"
        master_task.result = {
            "total_items": global_count,
            "global_sum": global_sum,
            "active_workers": len(master_task.subtasks),
            "total_active_leaves": total_leaves
        }

        return {
            "master_id": master_task.id,
            "goal": master_task.goal,
            "status": master_task.status,
            "wall_time_ms": master_task.duration_ms,
            "active_workers": len(master_task.subtasks),
            "assistants_per_worker": self.assistants_per_worker,
            "total_active_leaves": total_leaves,
            "result": master_task.result
        }
