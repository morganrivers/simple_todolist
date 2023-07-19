"""
This script navigates through ToDo files in a specified directory, analyzes each ToDo list and aggregates 
completed tasks. The aggregated tasks are presented in a weekly view, sorted in reverse chronological order. 

This script performs the following steps:

1. Defines constants for the ToDo directory, file naming convention, task status markers, and date format.

2. Initializes a data structure (dictionary) to hold completed tasks categorized by year, month, and week.

3. Retrieves a list of ToDo files from the directory, sorts them in reverse chronological order.

4. Iterates through each ToDo file, starting with the most recent. For each file, it:

    - Extracts the date from the filename.
    - Retrieves the year, month, and week of the ToDo file.
    - Initializes a new list in the data structure if the current week's key doesn't exist.
    - Opens the file and reads its lines.
    - Finds lines with a completed task marker and appends them to the appropriate list in the data structure.

5. Finally, it prints out the completed tasks sorted by year, month, and week, providing a clear view of 
   completed tasks on a weekly basis.

The script ignores tasks marked with a personal marker ("[p]"). It assumes that tasks are marked as done with a 
"[done]" tag, and the tasks are prefixed with a "-" symbol, which is removed before storage. 

Please adjust the constants at the beginning of the script to match your environment and preference.
"""
import os
import re
from datetime import datetime

# Define constants
TODO_DIRECTORY = os.path.expanduser("~/todo")
TODO_FILENAME_FORMAT = "todo_{date}.txt"
DONE_MARKER = "[done]"
TODO_PREFIX = "todo_"
DATE_FORMAT = "%Y_%m_%d"
PERSONAL_MARKER = "[p]"

# Initialize data structure to hold tasks
done_tasks = {}

# Get a list of todo files, sorted by date
todo_files = sorted(
    [f for f in os.listdir(TODO_DIRECTORY) if f.startswith(TODO_PREFIX)],
    reverse=True,
)

# For each file, starting with the most recent
for filename in todo_files:
    # Extract the date from the filename
    date_str = filename.split(TODO_PREFIX)[1].split(".txt")[0]
    date_obj = datetime.strptime(date_str, DATE_FORMAT)

    # Get the year, month and week
    year = date_obj.year
    month = date_obj.month
    week = date_obj.isocalendar()[1]

    # Create a key for the month and week
    key = (year, month, week)

    # Initialize the list for the key if it doesn't exist
    if key not in done_tasks:
        done_tasks[key] = []

    # Open the file and read its lines
    with open(os.path.join(TODO_DIRECTORY, filename), "r") as f:
        lines = f.readlines()

    # Find lines with DONE_MARKER
    for line in lines:
        if DONE_MARKER in line and (not PERSONAL_MARKER in line):
            # Remove the "-" if it's at the beginning of the line
            task = line.strip()
            if task.startswith("-"):
                task = task[1:].strip()

            # Append tuple of day_of_week and task to the tasks list
            day_of_week = date_obj.strftime("%A")
            done_tasks[key].append((day_of_week, task))

# Print the results
for key in sorted(done_tasks.keys(), reverse=True):
    year, month, week = key
    print(
        f"{datetime(year, month, 1).strftime('%B')} week {week - datetime(year, month, 1).isocalendar()[1] + 1}:"
    )
    for day_of_week, task in done_tasks[key]:
        print(f"{day_of_week}: {task}")
    print()
