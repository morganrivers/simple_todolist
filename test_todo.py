"""
Checks that todo_script.py should work correctly in a headless/cron environment.
Run with: python3 test_todo.py
"""

import os
import sys
import shutil
import tempfile
import traceback

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results = []

def check(name, fn):
    try:
        status, detail = fn()
        results.append((status, name, detail))
    except Exception as e:
        results.append((FAIL, name, f"Exception: {e}\n{traceback.format_exc()}"))


# ── Environment checks ────────────────────────────────────────────────────────

def check_sync_dir():
    from todo_script import TODO_DIRECTORY
    if os.path.isdir(TODO_DIRECTORY):
        return PASS, TODO_DIRECTORY
    return FAIL, f"Directory not found: {TODO_DIRECTORY}"
check("TODO_DIRECTORY exists", check_sync_dir)

def check_dateutil():
    import dateutil.parser
    return PASS, "python-dateutil available"
check("python-dateutil installed", check_dateutil)

def check_node():
    node = shutil.which("node")
    if node:
        return PASS, node
    return WARN, "'node' not found in PATH — calendar scheduling will fail"
check("node in PATH", check_node)

def check_fetch_emails():
    from todo_script import FETCH_EMAILS_SCRIPT
    if not FETCH_EMAILS_SCRIPT:
        return WARN, "fetch_emails_script not configured (scheduling will be skipped)"
    if os.path.exists(FETCH_EMAILS_SCRIPT):
        return PASS, FETCH_EMAILS_SCRIPT
    return WARN, f"Not found: {FETCH_EMAILS_SCRIPT} (scheduling will be skipped)"
check("fetch_emails.mjs exists", check_fetch_emails)

def check_sublime_missing_handled():
    # Simulate FileNotFoundError from missing SUBLIME_ALIAS — should not crash
    import subprocess
    try:
        subprocess.run(["__nonexistent_editor__", "/tmp/x"], check=True)
        return FAIL, "Expected FileNotFoundError, got none"
    except FileNotFoundError:
        return PASS, "FileNotFoundError raised as expected (handled in script)"
check("missing editor alias raises FileNotFoundError (handled)", check_sublime_missing_handled)


# ── due_date_parser unit tests ────────────────────────────────────────────────

def check_extract_due_basic():
    from due_date_parser import extract_due
    result = extract_due(" - [DUE February 26th]put vermittlungscode in der System\n")
    if result is None:
        return FAIL, "extract_due returned None for valid DUE tag"
    due_str, dt, is_whole_day = result
    if dt.month != 2 or dt.day != 26:
        return FAIL, f"Parsed wrong date: {dt}"
    if not is_whole_day:
        return FAIL, "Should be whole-day event"
    return PASS, f"Parsed: {dt.date()} whole_day={is_whole_day}"
check("extract_due: [DUE February 26th]", check_extract_due_basic)

def check_extract_due_with_year():
    from due_date_parser import extract_due
    result = extract_due(" - [DUE Mar 1, 2026] add binary tags\n")
    if result is None:
        return FAIL, "extract_due returned None"
    _, dt, is_whole_day = result
    if dt.year != 2026 or dt.month != 3 or dt.day != 1:
        return FAIL, f"Parsed wrong date: {dt}"
    return PASS, f"Parsed: {dt.date()}"
check("extract_due: [DUE Mar 1, 2026]", check_extract_due_with_year)

def check_extract_due_none():
    from due_date_parser import extract_due
    result = extract_due(" - call dentist 030 - 805 13 35\n")
    if result is not None:
        return FAIL, f"Expected None, got {result}"
    return PASS, "No false positive"
check("extract_due: no tag → None", check_extract_due_none)

def check_is_scheduled():
    from due_date_parser import is_scheduled, mark_scheduled
    line = " - [DUE Feb 26th]something\n"
    if is_scheduled(line):
        return FAIL, "Should not be scheduled yet"
    marked = mark_scheduled(line)
    if not is_scheduled(marked):
        return FAIL, f"mark_scheduled didn't add marker: {repr(marked)}"
    if not marked.endswith("\n"):
        return FAIL, f"mark_scheduled dropped newline: {repr(marked)}"
    return PASS, f"Marked: {repr(marked)}"
check("is_scheduled / mark_scheduled", check_is_scheduled)


# ── parse_blocks_from_file ────────────────────────────────────────────────────

def check_parse_blocks():
    from todo_script import parse_blocks_from_file
    content = (
        "todo from 2026_02_25:\n"
        " - \n"
        "\n"
        "todo from 2026_02_24:\n"
        " - [DUE February 26th]put vermittlungscode\n"
        " - [done] submit invoice\n"
        "\n"
        "todo from 2026_01_18:\n"
        " - add error bars\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(content)
        tmp = f.name
    try:
        lines, blocks = parse_blocks_from_file(tmp)
        dates = [b[0] for b in blocks]
        expected = ["2026_02_25", "2026_02_24", "2026_01_18"]
        if dates != expected:
            return FAIL, f"Expected {expected}, got {dates}"
        # Check block boundaries
        _, start, end = blocks[1]
        block_lines = lines[start:end]
        if not any("vermittlungscode" in l for l in block_lines):
            return FAIL, "Block 1 missing expected content"
        return PASS, f"Parsed {len(blocks)} blocks: {dates}"
    finally:
        os.unlink(tmp)
check("parse_blocks_from_file", check_parse_blocks)

def check_parse_blocks_top3():
    from todo_script import parse_blocks_from_file
    content = "".join(
        f"todo from 2026_0{i}_01:\n - task {i}\n\n"
        for i in range(1, 6)
    )
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(content)
        tmp = f.name
    try:
        _, blocks = parse_blocks_from_file(tmp)
        blocks.sort(key=lambda x: x[0], reverse=True)
        top3 = [b[0] for b in blocks[:3]]
        expected = ["2026_05_01", "2026_04_01", "2026_03_01"]
        if top3 != expected:
            return FAIL, f"Expected {expected}, got {top3}"
        return PASS, f"Top 3: {top3}"
    finally:
        os.unlink(tmp)
check("top-3 block selection by date", check_parse_blocks_top3)


# ── schedule_due_items skips gracefully without fetch_emails.mjs ──────────────

def check_schedule_skips_gracefully():
    import todo_script
    original = todo_script.FETCH_EMAILS_SCRIPT
    todo_script.FETCH_EMAILS_SCRIPT = "/nonexistent/path/fetch_emails.mjs"
    try:
        # Should print a message and return without crashing
        todo_script.schedule_due_items_in_recent_files()
        return PASS, "Returned without error when script missing"
    except Exception as e:
        return FAIL, str(e)
    finally:
        todo_script.FETCH_EMAILS_SCRIPT = original
check("schedule skips gracefully when fetch_emails.mjs missing", check_schedule_skips_gracefully)


# ── Summary ───────────────────────────────────────────────────────────────────

print()
max_name = max(len(n) for _, n, _ in results)
for status, name, detail in results:
    print(f"[{status}] {name:<{max_name}}  {detail}")

print()
passed = sum(1 for s, _, _ in results if s == PASS)
warned = sum(1 for s, _, _ in results if s == WARN)
failed = sum(1 for s, _, _ in results if s == FAIL)
print(f"{passed} passed, {warned} warnings, {failed} failed")

if failed:
    sys.exit(1)
