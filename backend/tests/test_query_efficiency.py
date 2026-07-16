"""
Regression tests proving list_solutions_for_experiment and get_solution
don't reintroduce N+1 queries — counts actual SQL statements executed via
SQLAlchemy's event system rather than just checking the result is correct
(which N+1 code also produces, just slowly).
"""
from contextlib import contextmanager

from sqlalchemy import event

from app.database import crud


@contextmanager
def count_queries(engine):
    count = [0]

    def _on_execute(*args, **kwargs):
        count[0] += 1

    event.listen(engine, "after_cursor_execute", _on_execute)
    try:
        yield count
    finally:
        event.remove(engine, "after_cursor_execute", _on_execute)


def _seed_experiment_with_n_solutions(db_session, n: int):
    user = crud.create_user(db_session, f"u{n}@example.com", "password123")
    model = crud.create_model(db_session, "gpt-4", "openai")
    experiment = crud.create_experiment(
        db_session, owner_id=user.id, name="Perf test", description=None,
        prompts=[{"problem_statement": f"problem {i}"} for i in range(n)],
        selected_models=["gpt-4"],
    )
    for prompt in experiment.prompts:
        crud.save_generated_solution(
            db_session, prompt_id=prompt.id, model_id=model.id, code="def f(): pass",
            raw_response="...", temperature=0.2, max_tokens=100, tokens_used=5, latency_seconds=0.01,
        )
    return experiment


def test_list_solutions_does_not_scale_linearly_with_solution_count(db_session):
    """The N+1 signature: query count growing with N proves a per-row lazy
    load; a flat query count proves eager loading is working."""
    engine = db_session.get_bind()

    small = _seed_experiment_with_n_solutions(db_session, 2)
    small_id = small.id  # capture as a plain string, same as a route gets it from the URL path —
    # accessing `.id` on the ORM object itself after commit can trigger an
    # incidental refresh query (expire_on_commit), which would pollute the
    # count this test is trying to isolate.
    with count_queries(engine) as count:
        solutions = crud.list_solutions_for_experiment(db_session, small_id)
        for s in solutions:
            _ = (s.model.name, s.prompt.problem_statement, s.execution_result, s.analysis_result)
    queries_for_2 = count[0]

    large = _seed_experiment_with_n_solutions(db_session, 8)
    large_id = large.id
    with count_queries(engine) as count:
        solutions = crud.list_solutions_for_experiment(db_session, large_id)
        for s in solutions:
            _ = (s.model.name, s.prompt.problem_statement, s.execution_result, s.analysis_result)
    queries_for_8 = count[0]

    # Without eager loading this would be ~1 + 4*N (N+1 per relationship);
    # with it, one query regardless of N. Assert it stays flat, not just "low".
    assert queries_for_2 == queries_for_8 == 1


def test_get_solution_loads_owner_chain_in_one_query(db_session):
    engine = db_session.get_bind()
    experiment = _seed_experiment_with_n_solutions(db_session, 1)
    solution_id = crud.list_solutions_for_experiment(db_session, experiment.id)[0].id

    with count_queries(engine) as count:
        fetched = crud.get_solution(db_session, solution_id)
        _ = fetched.prompt.experiment.owner_id  # the ownership check every route performs
        _ = fetched.model.name

    assert count[0] == 1
