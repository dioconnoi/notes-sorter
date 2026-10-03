from notes_sorter.categorize.eisenhower import (
    group_by_quadrant,
    quadrant_rank,
    sort_tasks_by_priority,
)
from notes_sorter.categorize.models import EisenhowerQuadrant, ExtractedTask, GTDType


def _task(title: str, quadrant: EisenhowerQuadrant | None, due: str | None = None) -> ExtractedTask:
    return ExtractedTask(title=title, gtd_type=GTDType.NEXT_ACTION, quadrant=quadrant, due_date=due)


def test_quadrant_rank_orders_do_now_first():
    assert quadrant_rank(EisenhowerQuadrant.DO_NOW) < quadrant_rank(EisenhowerQuadrant.SCHEDULE)
    assert quadrant_rank(EisenhowerQuadrant.SCHEDULE) < quadrant_rank(EisenhowerQuadrant.DELEGATE)
    assert quadrant_rank(EisenhowerQuadrant.DELEGATE) < quadrant_rank(EisenhowerQuadrant.ELIMINATE)


def test_unclassified_sorts_last():
    assert quadrant_rank(None) > quadrant_rank(EisenhowerQuadrant.ELIMINATE)


def test_sort_tasks_by_priority_orders_by_quadrant_then_due_date():
    tasks = [
        _task("eliminate me", EisenhowerQuadrant.ELIMINATE),
        _task("urgent later", EisenhowerQuadrant.DO_NOW, due="2026-12-01"),
        _task("urgent sooner", EisenhowerQuadrant.DO_NOW, due="2026-01-01"),
        _task("schedule it", EisenhowerQuadrant.SCHEDULE),
    ]
    ordered = sort_tasks_by_priority(tasks)
    assert [t.title for t in ordered] == ["urgent sooner", "urgent later", "schedule it", "eliminate me"]


def test_group_by_quadrant_buckets_correctly():
    tasks = [
        _task("a", EisenhowerQuadrant.DO_NOW),
        _task("b", EisenhowerQuadrant.DO_NOW),
        _task("c", EisenhowerQuadrant.DELEGATE),
        _task("d", None),  # excluded: no quadrant
    ]
    groups = group_by_quadrant(tasks)
    assert [t.title for t in groups[EisenhowerQuadrant.DO_NOW]] == ["a", "b"]
    assert [t.title for t in groups[EisenhowerQuadrant.DELEGATE]] == ["c"]
    assert groups[EisenhowerQuadrant.SCHEDULE] == []
