# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A 12-week (D1-D84) hands-on learning project for building AI Agents, culminating in a patent analysis assistant. Uses LangChain/LangGraph as the primary framework with Ollama for local LLM inference. The full study plan is in `AGENT_LEARNING.md`.

## Tech Stack

- **Python 3.13** (managed by uv)
- **LangChain + langchain-ollama** for LLM interaction
- **Ollama** for local model inference (qwen2.5:7b, llama3.2)
- **uv** for dependency and virtualenv management

## Commands

```bash
# Install dependencies
uv sync

# Run a lecture's main script
./run lecture01          # or: make run L=lecture01

# Run a lecture's tests (pytest)
./test lecture19         # or: make test L=lecture19

# Run arbitrary python
uv run python <script>
```

## Project Structure

- `lectures/lectureXX/` — Daily learning outputs (D1→lecture01, D2→lecture02, ..., D84→lecture84). Each contains `.py`, `.json`, `.mmd`, or `.md` deliverables.
- `shared/` — Cross-lecture shared code (utils, config, test data)
- `docs/weekly/` — Weekly summary reports (`week01_summary.md`, etc.)
- `docs/comparisons/` — Framework comparison docs (SK vs LangChain, LangGraph Python vs TypeScript)
- `screenshots/` — Verification screenshots (gitignored)
- `AGENT_LEARNING.md` — The full 84-day study plan with links and milestones

## Conventions

- **Script runner**: `./run lectureXX` finds and runs the first `.py` in the lecture dir (prefers `day*_*.py`)
- **Test runner**: `./test lectureXX` finds and runs test files (prefers `test_cases.py`, then `test_*.py`)
- **File naming**: snake_case for code, `test_` prefix for tests
- **Language**: Code comments and UI strings are in Chinese; code identifiers are in English
- **Dependencies**: All managed at root `pyproject.toml` via `uv add`; no per-lecture requirements files
