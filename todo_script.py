"""
Creates a daily todo file in the configured directory (default: ~/todo).
Carries forward unfinished tasks from the previous day.
Optionally schedules [DUE ...] items via a calendar script (requires
python-dateutil and a fetch_emails_script configured below).

Config file: ~/.config/simple_todolist/config.json
  todo_directory       path to todo files (default: ~/todo)
  fetch_emails_script  path to calendar node script (optional)
  editor               editor command (default: $VISUAL / $EDITOR / xdg-open / nano)
"""

import os
import subprocess
from datetime import datetime
import re

from config import load_config

try:
    from due_date_parser import extract_due, is_scheduled, mark_scheduled
    HAS_DUE_DATE_PARSER = True
except ImportError:
    HAS_DUE_DATE_PARSER = False

CONFIG = load_config()
TODO_DIRECTORY = CONFIG["todo_directory"]
FETCH_EMAILS_SCRIPT = CONFIG.get("fetch_emails_script")

TODO_FILENAME_FORMAT = "todo_{date}.txt"
TODO_START = "todo from {date}:\n - \n\n"
DATE_FORMAT = "%Y_%m_%d"
TODO_PREFIX = "todo_"
DONE_MARKER = "[done]"

TODAY = datetime.now().date().strftime(DATE_FORMAT)

if not os.path.exists(TODO_DIRECTORY):
    os.makedirs(TODO_DIRECTORY)


def check_string_is_worth_reprinting(line):
    return DONE_MARKER not in line.lower()


def remove_lines_with_empty_todo_in_them(not_done_items):
    date_pattern = r"^todo from \d{4}_\d{2}_\d{2}:$"
    empty_todo_pattern = r"^[-\s]*$"
    result = []
    last_date_line = None

    for line in not_done_items:
        if re.fullmatch(date_pattern, line.strip()):
            last_date_line = line
        elif last_date_line is not None and re.fullmatch(empty_todo_pattern, line.strip()):
            last_date_line = None
        else:
            if last_date_line is not None:
                result.append(last_date_line)
                last_date_line = None
            result.append(line)

    return result


def find_last_not_done_items():
    todo_files = sorted(
        [f for f in os.listdir(TODO_DIRECTORY) if f.startswith(TODO_PREFIX)],
        reverse=True,
    )

    for filename in todo_files:
        if filename == TODO_FILENAME_FORMAT.format(date=TODAY):
            continue
        with open(os.path.join(TODO_DIRECTORY, filename), "r") as f:
            lines = f.readlines()

        not_done_items = [line for line in lines if check_string_is_worth_reprinting(line)]
        filtered = remove_lines_with_empty_todo_in_them(not_done_items)

        if filtered:
            return [item if item.endswith('\n') else item + '\n' for item in filtered]

    return []


BLOCK_DATE_PATTERN = re.compile(r'^todo from (\d{4}_\d{2}_\d{2}):')


def parse_blocks_from_file(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()

    blocks = []
    current_date = None
    current_start = None

    for i, line in enumerate(lines):
        m = BLOCK_DATE_PATTERN.match(line.strip())
        if m:
            if current_date is not None:
                blocks.append((current_date, current_start, i))
            current_date = m.group(1)
            current_start = i

    if current_date is not None:
        blocks.append((current_date, current_start, len(lines)))

    return lines, blocks


def schedule_due_items_in_recent_files():
    if not HAS_DUE_DATE_PARSER:
        return
    if not FETCH_EMAILS_SCRIPT or not os.path.exists(FETCH_EMAILS_SCRIPT):
        return

    todo_files = sorted(
        [f for f in os.listdir(TODO_DIRECTORY) if f.startswith(TODO_PREFIX)],
        reverse=True,
    )
    if not todo_files:
        return

    filepath = os.path.join(TODO_DIRECTORY, todo_files[0])
    lines, blocks = parse_blocks_from_file(filepath)
    mutable_lines = list(lines)
    changed = False

    blocks.sort(key=lambda x: x[0], reverse=True)
    for _, start, end in blocks[:3]:
        for i in range(start, end):
            line = mutable_lines[i]
            due = extract_due(line)
            if due and not is_scheduled(line):
                _, dt, is_whole_day = due
                description = line.strip().lstrip("- ").strip()
                try:
                    subprocess.run(
                        ["node", FETCH_EMAILS_SCRIPT, "create-event",
                         description, dt.isoformat(),
                         "true" if is_whole_day else "false"],
                        check=True,
                        timeout=30,
                    )
                    mutable_lines[i] = mark_scheduled(line)
                    changed = True
                    print(f"Scheduled: {description!r}")
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    print(f"Warning: failed to schedule: {description!r} ({e})")

    if changed:
        with open(filepath, "w") as f:
            f.writelines(mutable_lines)


def open_in_editor(filename):
    candidates = list(filter(None, [
        CONFIG.get("editor"),
        os.environ.get("VISUAL"),
        os.environ.get("EDITOR"),
        "xdg-open",
        "nano",
    ]))
    for cmd in candidates:
        try:
            subprocess.run([cmd, filename], check=True)
            return
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError as e:
            print(f"Editor '{cmd}' exited with error {e.returncode}. File at: {filename}")
            return
    print(f"No editor found. File saved at: {filename}")


def create_today_todo():
    filename = os.path.join(TODO_DIRECTORY, TODO_FILENAME_FORMAT.format(date=TODAY))

    if not os.path.exists(filename):
        last_items = find_last_not_done_items()
        with open(filename, "w") as f:
            f.write(TODO_START.format(date=TODAY))
            if last_items:
                f.writelines(last_items)

    schedule_due_items_in_recent_files()
    open_in_editor(filename)


if __name__ == "__main__":
    create_today_todo()
