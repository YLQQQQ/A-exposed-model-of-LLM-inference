# Old vs New Timing Audit

## Status: NO_CONFIRMED_OLD_ROOT_CAUSE

The old P1-P4 pilot data shows Pass1/Pass0 ratio 0.26-0.29 (Pass 1 3-4x faster than Pass 0).
The new clock diagnostic (Run A/B/C) shows Pass1/Pass0 ratio 1.27-1.48 (Pass 1 slower, as expected with nsys overhead).

## Audit Findings

### CONFIRMED: OLD_NEGATIVE_OVERHEAD_NOT_REPRODUCED
The new diagnostic runs cannot reproduce the 0.26-0.29 ratio. All new runs show Pass 1 > Pass 0.

### CONFIRMED: PASS1_PROFILING_OVERHEAD_OBSERVED
In both Run A and Run B, Pass 1 (nsys-wrapped) is slower than Pass 0. The profiler overhead is 27-48%.

### CONFIRMED: PROCESS_ORDER_EFFECT_NOT_SUPPORTED
The order of runs (P0 first vs P1 first) does not flip which pass is slower.
Both Run A (P0->P1) and Run B (P1->P0) show P1 > P0.

### Possible Explanations for Old 0.26-0.29 Ratio

1. **Stale/mismatched input (PROBABLE)**: The old P1-P4 Pass 0 may have been generated
   with a different runner version that had an ns-to-ms conversion bug. The old data files
   should be checked: compare runner source hashes, Python executables, and git commits
   between old and new runs.

2. **Field-level mismatch (POSSIBLE)**: The old summarizer may have read a different
   field (e.g., prefill-only instead of e2e). The new summarizer reads
   `inference_e2e_latency_ms` consistently.

3. **Different GPU (UNLIKELY)**: Both old and new runs use GPU UUID
   GPU-0d8fafe6-a1e9-33cc-25fb-632316736455 (RTX 4090 at PCI E1:00.0).

4. **GPU clock state (POSSIBLE)**: The old Pass 0 may have run on a cold GPU while
   Pass 1 benefited from warm state. The new diagnostic attempted clock locking but
   it failed/not verified.

### Clock Lock Status

The clock lock was requested but FAILED_OR_UNVERIFIED. The observed clock did not
match the requested lock frequency. This means the old negative overhead cannot be
attributed to GPU clock/power management with certainty.

### Recommendations

- Do NOT use old P1-P4 Pass 0/Pass 1 ratios for any conclusions
- The new diagnostic data (Run A/B) confirms expected profiler overhead
- Re-run old P1-P4 with current runner to get clean baselines
- Fix clock lock verification before attempting causality analysis
