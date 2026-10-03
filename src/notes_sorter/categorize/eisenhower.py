from __future__ import annotations

from notes_sorter.categorize.models import EisenhowerQuadrant, ExtractedTask

# Lower number = higher priority, used for sorting a flattened todo view.
_QUADRANT_RANK = {
    EisenhowerQuadrant.DO_NOW: 0,
    EisenhowerQuadrant.SCHEDULE: 1,
    EisenhowerQuadrant.DELEGATE: 2,
    EisenhowerQuadrant.ELIMINATE: 3,
}

QUADRANT_LABELS = {
    EisenhowerQuadrant.DO_NOW: "🔴 Do Now",
    EisenhowerQuadrant.SCHEDULE: "🟡 Schedule",
    EisenhowerQuadrant.DELEGATE: "🔵 Delegate",
    EisenhowerQuadrant.ELIMINATE: "⚪ Eliminate",
}


def quadrant_rank(quadrant: EisenhowerQuadrant | None) -> int:
    """Unclassified (reference/someday) tasks sort last."""
    if quadrant is None:
        return len(_QUADRANT_RANK)
    return _QUADRANT_RANK[quadrant]


def sort_tasks_by_priority(tasks: list[ExtractedTask]) -> list[ExtractedTask]:
    return sorted(tasks, key=lambda t: (quadrant_rank(t.quadrant), t.due_date or "9999-99-99"))


def group_by_quadrant(tasks: list[ExtractedTask]) -> dict[EisenhowerQuadrant, list[ExtractedTask]]:
    groups: dict[EisenhowerQuadrant, list[ExtractedTask]] = {q: [] for q in EisenhowerQuadrant}
    for task in tasks:
        if task.quadrant is not None:
            groups[task.quadrant].append(task)
    return groups
