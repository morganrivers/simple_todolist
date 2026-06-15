import json
import os

_CONFIG_PATH = os.path.expanduser("~/.config/simple_todolist/config.json")


def load_config():
    config = {
        "todo_directory": "~/todo",
        "fetch_emails_script": None,
        "editor": None,
    }
    if os.path.exists(_CONFIG_PATH):
        with open(_CONFIG_PATH) as f:
            config.update(json.load(f))
    config["todo_directory"] = os.path.expanduser(config["todo_directory"])
    return config
