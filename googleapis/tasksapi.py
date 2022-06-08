from . import googleapi

DEF_TASK_LIST = ""
tasks_service = googleapi.get_service('tasks', v="v1")

class Task:
    def __init__(self, executed, tasklist_id):
        self.title = executed["title"]
        self.id = executed["id"]
        self.tasklist = tasklist_id
    
    def __eq__(self, other):
        if isinstance(other, Task):
            return self.id == other.id
        return self.id == other or self.title == other

    def __str__(self):
        return self.title

    def delete(self):
        tasks_service.tasks().delete(tasklist=self.tasklist, task=self.id).execute()

class TaskList:
    def __init__(self, listid=DEF_TASK_LIST):
        self.id = listid

    def get_tasks(self):
        tasks = tasks_service.tasks().list(tasklist=self.id).execute()
        if not "items" in tasks.keys():return []
        return [Task(x, self.id) for x in tasks["items"]]

    def __str__(self):
        return "TaskList(" + self.name + ", " + self.id + ", {" + ", ".join([str(x) for x in self.get_tasks()]) + "})"

    @property
    def name(self):
        return tasks_service.tasklists().get(tasklist=self.id, fields="title").execute()["title"]

    @property
    def etag(self):
        print(self.id)
        return tasks_service.tasklists().get(tasklist=self.id, fields="etag").execute()["etag"][1:-1]

    @property
    def url(self):
        return f"https://tasks.google.com/embed/list/?id={self.id}&origin=https://mail.google.com&fullWidth=1&lfhs=2"

    def add_task(self, title):
        return Task(tasks_service.tasks().insert(tasklist=self.id, body={"title": title}).execute(), self.id)

    def get_task(self, title):
        for x in self.get_tasks():
            if x.title == title:return x

    def delete_task(self, title):
        task = self.get_task(title)
        task.delete()

def get_or_create_tasks_list(name):
    for x in get_tasks_lists():
        if x.name == name:return x

    return create_tasks_list(name)

def create_tasks_list(name):
    return TaskList(tasks_service.tasklists().insert(body={"title": name}).execute()["id"])
       
def get_tasks_lists():
    return [TaskList(x["id"]) for x in tasks_service.tasklists().list().execute()["items"]]

def get_tasks_list(i):
    return TaskList(tasks_service.tasklists().get(tasklist=i).execute()["id"])

if __name__ == '__main__':
    print(t:=get_tasks_lists()[0])
    print(t.id)
    print(t.url)
    print(t:=get_or_create_tasks_list("project_manager"))
    print(t.url)
    print(t.name)
