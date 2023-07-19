"""
This script creates a daily todo file in the ~/todo directory. It allows you to keep 
track of your tasks on a day-to-day basis and carry forward unfinished tasks from the 
previous day. The script performs the following actions:

- Scans the ~/todo directory for existing todo files and identifies the most recent file
 that contains tasks marked as unfinished.
- Creates a new todo file for the current day, using the format 'todo_YYYY_MM_DD.txt'.
- Retrieves the unfinished tasks from the previous day's todo file (if any) and includes
 them in the current day's file.
- Opens the current day's todo file in the Sublime Text editor.
"""

# Import required libraries
import os
import subprocess
from datetime import datetime
import re

# Define constants
TODO_DIRECTORY = os.path.expanduser("~/todo")
TODO_FILENAME_FORMAT = "todo_{date}.txt"
SUBLIME_ALIAS = "s"
TODO_START = "todo from {date}:\n - \n\n"
PREVIOUS_TODO_HEADER = "\ntodo from {date}:\n"
DATE_FORMAT = "%Y_%m_%d"
TODO_PREFIX = "todo_"
DONE_MARKER = "[done]"
FROM_TODAY_MARKER = "todo from today"
TODO_FROM_TODAY_MARKER = "todo from"

# Get today's date as a string
TODAY = datetime.now().date().strftime(DATE_FORMAT)

if not os.path.exists(TODO_DIRECTORY):
    os.makedirs(TODO_DIRECTORY)


def check_string_is_worth_reprinting(line):
    if DONE_MARKER in line:
        return False

    # If none of the above conditions are met, line is worth reprinting today
    return True


def remove_lines_with_empty_todo_in_them(not_done_items):
    """
    This function checks for any lines in not_done_items that matches the format of
    TODO_START and removes them.
    """
    # The regular expression pattern for a line that matches "todo from {date}:"
    date_pattern = r"^todo from \d{4}_\d{2}_\d{2}:$"
    # The regular expression pattern for a line that matches " - "
    empty_todo_pattern = r"^[-\s]*$"

    not_done_items_with_empty_todo_removed = []
    last_date_line = None

    for line in not_done_items:
        if re.fullmatch(date_pattern, line.strip()):
            if last_date_line is not None:
                last_date_line = None
            # Store the current date line to check against the next line
            last_date_line = line
        elif last_date_line is not None and re.fullmatch(
            empty_todo_pattern, line.strip()
        ):
            # If the last line was a date line and the current line is empty, discard
            last_date_line = None
            continue
        else:
            # If the last line was a date line and wasn't discarded, print it
            if last_date_line is not None:
                not_done_items_with_empty_todo_removed.append(last_date_line)
                last_date_line = None
            # Print the current line
            not_done_items_with_empty_todo_removed.append(line)

    return not_done_items_with_empty_todo_removed


def find_last_not_done_items():
    """
    This function finds the most recent todo file with items that are not yet done,
    and returns these items along with the date of the file.
    """
    # Get a list of todo files, sorted by date
    todo_files = sorted(
        [f for f in os.listdir(TODO_DIRECTORY) if f.startswith(TODO_PREFIX)],
        reverse=True,
    )

    # For each file, starting with the most recent
    for filename in todo_files:
        if filename == TODO_FILENAME_FORMAT.format(date=TODAY):
            continue
        # Open the file and read its lines
        with open(os.path.join(TODO_DIRECTORY, filename), "r") as f:
            lines = f.readlines()

        not_done_items = [
            line for line in lines if (check_string_is_worth_reprinting(line))
        ]

        not_done_items_and_no_empty_dates = remove_lines_with_empty_todo_in_them(
            not_done_items
        )

        # If there are any such lines, return them along with the date from the filename
        if not_done_items_and_no_empty_dates:
            # add a newline at the end between todos
            not_done_items_and_no_empty_dates += "\n"

            # date_str = filename.split(TODO_PREFIX)[1].split(".txt")[0]
            return not_done_items_and_no_empty_dates  # , date_str
        else:
            # if there is nothing from the day being considered, let's continue
            continue

        break  # forget about any earlier days. We only care about the most recent day

    # If no such lines are found in any file, return empty list and string
    return [], ""


def create_today_todo():
    """
    This function creates a todo file for today, which includes any items not yet done
    from the most recent previous todo file. If the file already exists, it will open.
    """

    # Create the filename for today's todo file
    filename = os.path.join(TODO_DIRECTORY, TODO_FILENAME_FORMAT.format(date=TODAY))

    # If the file doesn't exist, create it and populate it with items from the last todo
    if not os.path.exists(filename):
        # Find the not done items from the last todo file
        last_items = find_last_not_done_items()

        # Write to today's todo file
        with open(filename, "w") as f:
            # Write the header for today's tasks
            f.write(TODO_START.format(date=TODAY))

            # If there are any items from the last todo file, write them with a header
            if last_items:
                f.writelines(last_items)

    # Open today's todo file in Sublime
    try:
        subprocess.run([SUBLIME_ALIAS, filename], check=True)
    except subprocess.CalledProcessError:
        print(
            "Failed to open "
            + filename
            + " with Sublime Text."
            + "Please make sure Sublime Text is installed and '"
            + SUBLIME_ALIAS
            + "' is a valid command to open Sublime Text.",
        )


if __name__ == "__main__":
    create_today_todo()
