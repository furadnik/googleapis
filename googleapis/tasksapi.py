from datetime import datetime
from typing import Iterator

from . import googleapi
from .list_full import list_all

DEF_TASK_LIST = ""
MAX_TASKS = 100
tasks_service = googleapi.get_service('tasks', v="v1")


class Task:
    def __init__(self, executed: dict, tasklist_id: str) -> None:
        self.title = executed["title"]
        self.id = executed["id"]
        self.notes: str | None = executed.get("notes", None)
        self.tasklist = tasklist_id

    def __eq__(self, other) -> bool:
        if isinstance(other, Task):
            return self.id == other.id
        return self.id == other or self.title == other

    def __str__(self) -> str:
        return self.title

    def delete(self) -> None:
        tasks_service.tasks().delete(tasklist=self.tasklist, task=self.id).execute()


class TaskList:
    def __init__(self, listid=DEF_TASK_LIST):
        self.id = listid

    def get_tasks(self):
        """Return non-completed tasks present in the tasklist."""
        tasks = list_all(tasks_service.tasks().list, tasklist=self.id, maxResults=MAX_TASKS)
        return (Task(x, self.id) for x in tasks)

    def __repr__(self):
        """Return a string representation."""
        return "TaskList(" + self.name + ", " + self.id + ", {" + ", ".join([str(x) for x in self.get_tasks()]) + "})"

    @property
    def name(self):
        return tasks_service.tasklists().get(tasklist=self.id, fields="title").execute()["title"]

    @property
    def etag(self):
        return tasks_service.tasklists().get(tasklist=self.id, fields="etag").execute()["etag"][1:-1]

    @property
    def url(self):
        return f"https://tasks.google.com/embed/list/?id={self.id}&origin=https://mail.google.com&fullWidth=1&lfhs=2"

    def add_task(self, title: str, notes: str = "", due: datetime | None = None) -> Task:
        body = {"title": title, "notes": notes}
        if due is not None:
            body["due"] = due.isoformat()
        return Task(tasks_service.tasks().insert(tasklist=self.id, body=body).execute(),
                    self.id)

    def get_task(self, title: str) -> Task | None:
        for x in self.get_tasks():
            if x.title == title:
                return x
        return None

    def delete_task(self, title: str) -> None:
        task = self.get_task(title)
        if task is not None:
            task.delete()


def get_or_create_tasks_list(name: str) -> TaskList:
    for x in get_tasks_lists():
        if x.name == name:
            return x

    return create_tasks_list(name)


def create_tasks_list(name: str) -> TaskList:
    return TaskList(tasks_service.tasklists().insert(body={"title": name}).execute()["id"])


def get_tasks_lists() -> Iterator[TaskList]:
    return [TaskList(x["id"]) for x in list_all(tasks_service.tasklists().list)]  # type: ignore


def get_tasks_list(name: str) -> TaskList:
    return TaskList(tasks_service.tasklists().get(tasklist=name).execute()["id"])


if __name__ == '__main__':
    for x in get_tasks_lists()[0].get_tasks():
        print("T", x)
