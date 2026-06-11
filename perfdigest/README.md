# perfdigest

Local **MCP server** that makes NVIDIA Nsight Compute (`ncu`) profiler output
**token-efficient** for LLM coding agents. It sits between the profiler and the
agent: reads the report from disk and returns a small, structured, numeric signal
the agent can act on, while keeping a pointer back to the raw report for lazy expansion.

It is a **translator/router, not a judge** — interpretation ("is this kernel
memory-bound?") is the model's job. perfdigest only provides efficient,
deterministic access to clean numeric metrics.

## Two load-bearing invariants (read before running)

1. **Suppress profiler stdout — write to a file.**
   ```
   ncu --set full -o report.ncu-rep ./app
   ```
   If `ncu` prints its summary to stdout, that raw table enters the agent's context
   *before* perfdigest runs — defeating the entire purpose. Always `-o <file>`.

2. **`None` means "not measured in this export", NEVER zero.**
   Readers must never fill a missing metric with `0.0`. For a requested metric the
   export does not contain, `get_metrics` returns `not_available_in_this_export`,
   not a fake value. Silently returning zero = lying to the model = the worst bug
   this tool can have.

## Install (uv)

```bash
uv sync                 # base server (CSV path works without CUDA)
uv sync --extra cuda    # adds ncu_report (NVIDIA PRI) for native .ncu-rep parsing
```

`ncu_report` is imported lazily, so CSV-only paths never load it.

## Tools (v1)

- `list_kernels(report_ref, format)` -> `[{name, index, duration_us}]`
- `get_metrics(report_ref, format, kernel, metrics=None)` -> `KernelDigest`
  (`metrics=None` returns the default core set)
- `expand(report_ref, format, kernel, section)` -> raw section (the safety valve)

`format` is **mandatory** in v1 — the agent passes what it produced. No auto-detect in v1.

## Status

Phase 0 — project scaffold. Build order: contract → reader (isolation) → mapping →
server shell → prompts. Do not one-shot. See the init prompt for locked decisions.
