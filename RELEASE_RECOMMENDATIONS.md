# Release Recommendations

## Is it ready to release?

The core todo script (`todo_script.py`) works. The carry-forward logic, file creation, and editor launch all function correctly. If you only care about the simple marking-and-saving workflow, it is functionally releasable for personal use with the bugs noted below fixed first.

---

## Bugs Found (not fixed — report only)

### Bug 1 — Directory path mismatch (breaks summarization)
`todo_script.py` writes files to `~/Sync`, but `summarize_work_done.py` reads from `~/Documents/MEGAsync`. These are different directories. The summarizer will always report nothing unless you happen to have todo files in both places.

**File:** `summarize_work_done.py:34`
```python
TODO_DIRECTORY = os.path.expanduser("~/Documents/MEGAsync")  # should match todo_script.py
```

### Bug 2 — README editor alias is wrong
`README.md` tells users to alias `s` to `subl`, but the code uses `u` as the alias.

**File:** `todo_script.py:30`, `README.md:20`
```python
SUBLIME_ALIAS = "u"   # README says "s"
```

### Bug 3 — README refers to `~/todo`, code uses `~/Sync`
The README says files are created in `~/todo`; the actual directory is `~/Sync`.

**File:** `README.md:3, 37`

### Bug 4 — Hardcoded absolute path to calendar script
The email/calendar integration points at a path that only exists on the author's machine. This is gracefully skipped when the file is absent, so it does not crash — but the feature is silently dead for anyone else.

**File:** `todo_script.py:28`
```python
FETCH_EMAILS_SCRIPT = "/home/protected/email_summary/fetch_emails.mjs"
```

### Bug 5 — Unreachable `break` statement
In `find_last_not_done_items()`, the `break` on line 127 can never execute because the preceding `continue` in the `else` branch already advances the loop. It's dead code, harmless but confusing.

**File:** `todo_script.py:127`

### Bug 6 — No declared dependencies
`python-dateutil` is required by `due_date_parser.py` but there is no `requirements.txt`, `pyproject.toml`, or any other dependency declaration. A new user cloning the repo will get an `ImportError` with no hint about what to install.

---

## Best Way to Release for Install

Since this is a personal productivity script (not a library), the right release approach depends on your goal:

### Option A — Simple git clone (recommended for personal use)
No packaging needed. Just keep the README accurate and add a one-liner install:

```bash
git clone https://github.com/morganrivers/simple_todolist.git ~/simple_todolist
pip install python-dateutil
# Add to crontab or bind a keyboard shortcut:
python3 ~/simple_todolist/todo_script.py
```

This is the lowest-friction option for a script you run yourself.

### Option B — `pipx` installable package (recommended if others will use it)
Add a `pyproject.toml` with an entry point so the script can be installed system-wide with one command:

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "simple-todolist"
version = "1.0.0"
dependencies = ["python-dateutil"]

[project.scripts]
todo = "todo_script:create_today_todo"
```

Then anyone can do:
```bash
pipx install git+https://github.com/morganrivers/simple_todolist.git
todo  # runs from anywhere
```

### Option C — Single shell script (no Python required)
See the Python section below.

---

## Is It Reasonable to Not Require Python?

**Short answer: yes, if you drop the calendar integration.**

The core functionality — create today's file, carry forward unfinished tasks, open in editor — uses only Python's standard library (`os`, `subprocess`, `datetime`, `re`). The only external dependency (`python-dateutil`) is used exclusively for parsing `[DUE ...]` tags to schedule calendar events via the external Node.js script.

If you remove or defer the calendar scheduling feature, the whole tool has zero third-party dependencies and works with any Python 3.6+ installation (which ships by default on macOS and most Linux distros).

Alternatively, the core logic could be rewritten as a ~50-line bash script with no dependencies at all. The file format is plain text, the date handling is straightforward, and bash handles file operations and editor launch natively. The trade-off: bash is harder to read and test, and the existing `test_todo.py` suite would be lost.

**Recommendation:** Keep Python (it's already there and tested), add `requirements.txt` with just `python-dateutil`, and document it clearly. Python is a reasonable and minimal requirement for this class of tool.

---

## Summary Checklist Before v1.0

- [ ] Fix `TODO_DIRECTORY` in `summarize_work_done.py` to match `todo_script.py`
- [ ] Fix README: `~/todo` → `~/Sync`, alias `s` → `u`
- [ ] Add `requirements.txt` containing `python-dateutil`
- [ ] Make `FETCH_EMAILS_SCRIPT` configurable (env var or config section at top of file)
- [ ] Remove the unreachable `break` on line 127 of `todo_script.py`
- [ ] Add a `LICENSE` file
- [ ] Consider whether `summarize_work_done.py` belongs in this repo at all given it targets a different directory and a different sync tool (MEGAsync vs Sync)
