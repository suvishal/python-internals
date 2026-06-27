# Memory Management in Python

Reference counting, cyclic garbage collection, and CPython's allocation strategy — explained with the production scenarios where each one actually matters, not just the textbook definitions.

## Contents

| File | What it covers |
|---|---|
| [`notes.md`](./notes.md) | Core concepts, mental models, interview Q&A, and a 3-step framework for diagnosing a memory leak in a real service |
| [`reference_counting.py`](./reference_counting.py) | Runnable walkthrough of how ref counts change across aliasing, deletion, and function calls — with predictions to check yourself against |
| [`garbage_collection.py`](./garbage_collection.py) | Builds an actual reference cycle, shows reference counting failing to clean it up, then shows the cyclic collector doing it |

## How to use this folder

1. Read `notes.md` section by section — each one builds on the last.
2. Before running either script, read the comments and **predict the printed numbers yourself**. Then run it and check.
3. Try the "try it yourself" block at the bottom of each script — that's where the concept actually sticks.

```bash
python3 reference_counting.py
python3 garbage_collection.py
```

No dependencies beyond the standard library (`sys`, `gc`).

## Why this folder exists

Most people who can write Python have never had to explain *why* it needs two different memory-management mechanisms, or which one to suspect first when a long-running service starts leaking. That gap is exactly what this folder closes.
