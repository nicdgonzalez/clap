#!/usr/bin/python

import dataclasses
import datetime as dt
import json
import pathlib
import time

import clap

TASKS_JSON = pathlib.Path(__file__).resolve().parent.joinpath("tasks.json")

app = clap.Application(
    brief="A simple to-do application demonstrating clap.Application!"
)


@dataclasses.dataclass
class Task:
    id: int
    note: str
    is_complete: bool
    created_at: float


tasks_db: list[Task] = []
index = 1


def db_connect():
    global tasks_db, index

    if not TASKS_JSON.exists():
        TASKS_JSON.write_text('{"tasks": []}')
        return

    with open(TASKS_JSON, "r") as f:
        data = json.load(f)

        for task in data["tasks"]:
            if "created_at" not in task.keys():
                task.update(created_at=time.time())

            tasks_db.append(Task(**task))

    try:
        index = tasks_db[-1].id + 1
    except IndexError:
        assert len(tasks_db) < 1


def db_commit():
    data = {"tasks": []}

    for task in tasks_db:
        data["tasks"].append(dataclasses.asdict(task))

    with open(TASKS_JSON, "w+") as f:
        json.dump(data, f, indent=4)


@app.command(name="list", aliases=["ls"])
def list_command(*, all: bool = False):
    """Display all of the available tasks.

    Parameters
    ----------
    all : bool
        Whether to also display completed tasks.
    """
    if not all:
        tasks = list(filter(lambda t: not t.is_complete, tasks_db))
        count = len(tasks)
    else:
        tasks = tasks_db
        count = len(tasks)

    print(f"you have ({count}) tasks:")
    fmt = "%Y-%m-%d %H:%M:%S"
    for task in tasks:
        created_at = dt.datetime.fromtimestamp(task.created_at).strftime(fmt)
        print(f"  {task.id}: {task.note} ({created_at})")


@app.command()
def add(note: str):
    """Create a new task.

    Parameters
    ----------
    note : str
        A message representing the task to be completed.
    """
    global tasks_db, index
    tasks_db.append(
        Task(id=index, note=note, is_complete=False, created_at=time.time())
    )
    print(f"successfully created a new task: id={index}, note={note!r}")
    index += 1
    db_commit()


@app.command()
def update(id: int, note: str):
    """Make changes to an existing task.

    Parameters
    ----------
    id : int
        The unique identifier of an existing task.
    note : str
        A message representing the task to be completed.
    """
    for task in tasks_db:
        if task.id == id:
            original = task.note
            task.note = note
            print(f"updated task with id {id}.\n  {original!r} -> {note!r}")
            break
        else:
            pass
    else:
        raise clap.ErrorMessage(
            "no task matches the given id. use the list command to "
            "see a list of available tasks"
        )


@app.command()
def delete(id: int):
    """Remove an existing task.

    Parameters
    ----------
    id : int
        The unique identifier of an existing task.
    """
    global tasks_db
    for i, task in enumerate(tasks_db):
        if task.id == id:
            _ = tasks_db.pop(i)
            db_commit()
            print(f"successfully removed task with id {id}")
            break
        else:
            pass
    else:
        raise clap.ErrorMessage(
            "no task matches the given id. use the list command to "
            "see a list of available tasks"
        )


@app.command()
def check_all():
    """Mark all existing tasks as finished."""
    for task in tasks_db:
        task.is_complete = True
    else:
        print("successfully marked all tasks as complete")
        db_commit()


@app.command()
def check(id: int):
    """Mark a task as finished.

    Parameters
    ----------
    id : int
        The unique identifier of an existing task.
    """
    for task in tasks_db:
        if task.id == id:
            task.is_complete = True
            print(f"successfully marked task with id {task.id} as complete")
            db_commit()
            break
        else:
            pass
    else:
        raise clap.ErrorMessage(
            "no task matches the given id. use the list command to "
            "see a list of available tasks"
        )


@app.command()
def uncheck_all():
    """Mark all existing tasks as unfinished."""
    for task in tasks_db:
        task.is_complete = False
    else:
        print("successfully marked all tasks as incomplete")
        db_commit()


@app.command()
def uncheck(id: int):
    """Mark a task as unfinished.

    Parameters
    ----------
    id : int
        The unique identifier of an existing task.
    """
    for task in tasks_db:
        if task.id != id:
            continue

        task.is_complete = False
        print(f"successfully marked task with id {task.id} as complete")
        db_commit()
        break
    else:
        raise clap.ErrorMessage(
            "no task matches the given id. use the list command to "
            "see a list of available tasks"
        )


if __name__ == "__main__":
    db_connect()
    clap.parse_args(app)
