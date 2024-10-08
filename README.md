# Simple ToDo List
A robust, day-to-day ToDo list tracker and summarizer.

This application creates a daily ToDo file in your ~/todo directory, empowering you to keep track of your tasks on a day-to-day basis and seamlessly carry forward unfinished tasks from the previous day.

The `todo_script.py` script performs a variety of tasks:

- It scans the ~/todo directory for existing ToDo files and identifies the most recent file containing tasks that are marked as unfinished.
- It creates a new ToDo file for the current day, adhering to the 'todo_YYYY_MM_DD.txt' format.
- It fetches any unfinished tasks from the previous day's ToDo file and integrates them into the current day's file.
- It launches the current day's ToDo file in the Sublime Text editor for immediate use and editing.

In addition, the script provides a summarization feature:

- It prints a summary of completed tasks and the dates on which they were accomplished.

# How to Run
To utilize the Simple ToDo List, follow the instructions below:

0. Make sure to have sublime text installed and alias `s` to the `subl` command. Or, you can modify the subprocess call to some other text editor opening command.

1. Clone the repository:
    ```
    git clone github.com/morganrivers/simple_todolist.git
    ```

2. Navigate into the cloned repository:
    ```
    cd simple_todolist
    ```

3. Run the following command to generate today's ToDo list:
    ```
    python3 todo_script.py
    ```
    The ToDo list will be created in a new file in the ~/todo directory.
 
    I have set up my machine to have a keyboard command that opens the to-do list in the text editor. This makes it really easy to get to the ToDo list whenever you want

After completing some tasks, you can print a summary of your progress by executing:

```
python3 summarize_work_done.py
```

This will provide a report of the tasks you have completed and the dates on which they were completed.

