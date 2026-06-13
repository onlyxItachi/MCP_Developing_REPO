# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Resuming on a new machine?** Read [`HANDOFF.md`](HANDOFF.md) first — it has the current status and the exact steps to regenerate the profiler fixture and finish the remaining tests (the work moved off Windows because Smart App Control blocks unsigned local builds).

## What this repository is

A development kit for building **MCP (Model Context Protocol) servers**. The main (and currently only real) project is **`perfdigest/`** — everything else at the root is supporting scratch space.

- **`perfdigest/`** — a local MCP server that makes **performance-profiler output** token-efficient for LLM coding agents. It reads profiler reports from disk and returns small, structured, numeric digests instead of letting raw multi-thousand-token tables flood the agent's context. **As of v1.0.0 it is multi-backend**: NVIDIA Nsight Compute (`ncu`), AMD HIP (`rocprof`), Linux `perf` (CPU C++/Rust), and Apple Metal (`xctrace`) — dispatched by a `format → backend` registry. This is the project all real work happens in. Usable from both Claude Code and OpenAI Codex (stdio MCP).
- **`MCP_Developing_Workshop/`** — a Node scratchpad (npm package `mcp_developing_workshop`) with `@anthropic-ai/claude-agent-sdk`, `@anthropic-ai/sdk`, `tsx`, and `typescript` as dependencies. No source files yet.
- **`workshop-env/`** — a POSIX Python 3.10 venv (gitignored, never commit; not used by perfdigest, which targets Python 3.11+ via uv).

## Working in perfdigest — read these first, in this order

1. **`perfdigest/docs/INIT_PROMPT.md`** — the canonical spec. All architectural decisions are locked there with rationale; do not re-litigate them.
2. **`perfdigest/CLAUDE.md`** — the short operational contract: non-negotiable invariants, build order, tool signatures, and open items that must be asked of the user rather than invented.

Current state: **v1.0.0 — multi-backend** (branch `feat/multi-backend-v1`). The NVIDIA path of v1 is refactored onto a `Backend` registry (`core/backend.py` + `adapters/registry.py`); AMD HIP, Linux perf (CPU), and Metal adapters added; a `platform/` layer does **capture gating**; two new tools (`platform_capabilities`, `suggest_profile_command`) advise capture. 58 pytest tests pass (+16 hardware-gated skip). Apache-2.0 licensed; PyPI + Claude Code/Codex configs ready. The earlier A/B context-efficiency benchmark (~36x fewer tokens) lives in `perfdigest/eval/RESULTS.md`. `test_script/` holds the CUDA workload for the real `.ncu-rep` fixture.

**The load-bearing rule**: *digesting* a report is universal (a Mac digests a CI-produced NVIDIA report — CUDA-dev-on-Mac); only *capturing* is platform-gated. Gating lives in `platform/capabilities.py`, never on readers. Future backends (Go, Java, …) are planned; Windows/Metal are validated via GitHub Actions, not the Linux dev box.

## Commands (run from `perfdigest/`)

```bash
uv sync --extra dev          # base + pytest (all pure-Python readers work; no GPU needed)
uv sync --extra nvidia       # + ncu-report for native .ncu-rep parsing (alias: --extra cuda)
uv run perfdigest            # run the multi-backend MCP server over stdio
uv run pytest                # 58 pass + 16 hardware-gated skips
uv build                     # build sdist+wheel (publish.yml does this on a v* tag)
```

## The invariants that must never break (full detail in perfdigest/CLAUDE.md)

- **`None` ≠ `0.0`** — a missing metric means "not measured in this export", never zero. `get_metrics` returns `"not_available_in_this_export"` for absent metrics. Silently substituting zero is the single worst bug this tool can have.
- **`format` is mandatory** in v1 — no auto-detect.
- **Translator, not judge** — no verdict/threshold heuristics; interpretation is the model's job.
- **`server/` is a thin shell** — business logic lives in `core/` and `adapters/`; `core/` never sees vendor metric names.
- **Heavy/CUDA-only imports (`ncu_report`) are lazy** so CSV-only paths never load them.
- **Read ≠ capture.** Digesting any report is universal and ungated; only on-device capture is platform-verified (`platform/capabilities.py`). A new backend = a folder under `adapters/` that builds + `register()`s a `Backend` (reader + `mapping.py` + probe); the server shell never imports a concrete reader.
