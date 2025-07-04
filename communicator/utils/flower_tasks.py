import datetime
import json
import time

from communicator.utils.flower_search import parse_search_terms, satisfies_search_terms


def iter_tasks(
        events,
        limit=None,
        offset=0,
        type=None,
        worker=None,
        state=None,
        sort_by=None,
        received_start=None,
        received_end=None,
        started_start=None,
        started_end=None,
        search=None
):
    i = 0
    tasks = events.state.tasks_by_timestamp()
    if sort_by is not None:
        tasks = sort_tasks(tasks, sort_by)

    def convert(x):
        return time.mktime(datetime.datetime.strptime(x, '%Y-%m-%d %H:%M').timetuple())

    search_terms = parse_search_terms(search or {})

    for uuid, task in tasks:
        if type and task.name != type:
            continue
        if worker and task.worker and task.worker.hostname != worker:
            continue
        if state and task.state != state:
            continue
        if received_start and task.received and task.received < convert(received_start):
            continue
        if received_end and task.received and task.received > convert(received_end):
            continue
        if started_start and task.started and task.started < convert(started_start):
            continue
        if started_end and task.started and task.started > convert(started_end):
            continue
        if not satisfies_search_terms(task, search_terms):
            continue
        if i >= offset:
            yield uuid, task
        i += 1
        if limit is not None:
            if i == limit + offset:
                break


sort_keys = {'name': str, 'state': str, 'received': float, 'started': float}


def sort_tasks(tasks, sort_by):
    assert sort_by.lstrip('-') in sort_keys
    reverse = False
    if sort_by.startswith('-'):
        sort_by = sort_by.lstrip('-')
        reverse = True
    yield from sorted(
        tasks,
        key=lambda x: getattr(x[1], sort_by) or sort_keys[sort_by](),
        reverse=reverse)


def get_task_by_id(events, task_id):
    return events.state.tasks.get(task_id)


def remove_task_by_id(events, task_id):
    with events.state._mutex:
        events.state.tasks.pop(task_id, None)
        events.state.rebuild_taskheap()


def as_dict(task):
    return task.as_dict()


def parse_args(args):
    """
    Parse and process the `args` of the task.
    """
    if not args:
        return []
    try:
        # Attempt to parse JSON
        parsed_args = json.loads(args)
        if isinstance(parsed_args, str) and parsed_args.startswith('(') and parsed_args.endswith(')'):
            return eval(parsed_args)  # Handle stringified tuples
        return parsed_args
    except (json.JSONDecodeError, SyntaxError):
        # Fallback for stringified tuples or ellipsis
        if args == '...':
            return [...]
        if args.startswith('(') and args.endswith(')'):
            return eval(args)

        return [args]


def parse_kwargs(kwargs):
    """
    Parse and process the `kwargs` of the task.
    """
    if not kwargs:
        return {}
    try:
        # Attempt to parse JSON
        return json.loads(kwargs)
    except json.JSONDecodeError:
        try:
            # Fallback for stringified dictionaries
            import ast
            if kwargs.startswith('{') and kwargs.endswith('}'):
                return ast.literal_eval(kwargs)
        except (ValueError, SyntaxError):
            return {}
    return {}


def make_json_serializable(obj):
    """
    Recursively replace non-serializable types with JSON-serializable alternatives.
    """
    if isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif obj is Ellipsis:
        return None  # Replace `...` with `null`
    return obj  # Return the object if it's already serializable
