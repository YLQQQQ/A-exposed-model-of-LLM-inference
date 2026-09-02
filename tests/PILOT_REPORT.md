# Small Pilot Report

## Repeat Advice Rules (Pilot Engineering)

- CV <= 3%: PASS0_5_LIKELY_ENOUGH
- 3% < CV <= 5%: CONSIDER_PASS0_10
- CV > 5%: CONSIDER_PASS0_20
- duration_coverage < 90%: DATA_QUALITY_BLOCKED
- exclusion_rate > 5%: DATA_QUALITY_BLOCKED

These are Pilot engineering rules, NOT final paper thresholds.

## Results

### P1
- **gpu_uuid**: None
- **gpu_name**: None
- **gpu_pci_bus_id**: None
- **gpu_index**: None
- **pass0_count**: 5
- **pass0_exclusions**: 0
- **pass0_mean_ms**: 2861.769
- **pass0_median_ms**: 2884.359
- **pass0_std_ms**: 145.602
- **pass0_cv_pct**: 5.09
- **pass0_min_ms**: 2680.527
- **pass0_max_ms**: 3044.923
- **pass1_count**: 5
- **pass1_mean_ms**: 714.784
- **profiler_overhead_ratio**: 0.2498
- **throughput_tokens_per_sec**: 2.8
- **rep_size_mb**: 6.22
- **sqlite_size_mb**: 18.07
- **sync_count_total**: None
- **sync_count_supported**: None
- **sync_count_valid**: None
- **sync_duration_total_ms**: None
- **sync_duration_supported_ms**: None
- **sync_duration_valid_ms**: None
- **count_coverage_pct**: 0.0
- **duration_coverage_pct**: 0.0
- **a_conservation**: missing
- **repeat_advice**: DATA_QUALITY_BLOCKED
- **pilot_status**: NO_GPU_UUID

### P2
- **gpu_uuid**: None
- **gpu_name**: None
- **gpu_pci_bus_id**: None
- **gpu_index**: None
- **pass0_count**: 5
- **pass0_exclusions**: 0
- **pass0_mean_ms**: 2762.43
- **pass0_median_ms**: 2926.053
- **pass0_std_ms**: 365.866
- **pass0_cv_pct**: 13.24
- **pass0_min_ms**: 2182.079
- **pass0_max_ms**: 3081.14
- **pass1_count**: 5
- **pass1_mean_ms**: 774.203
- **profiler_overhead_ratio**: 0.2803
- **throughput_tokens_per_sec**: 2.9
- **rep_size_mb**: 6.18
- **sqlite_size_mb**: 18.03
- **sync_count_total**: None
- **sync_count_supported**: None
- **sync_count_valid**: None
- **sync_duration_total_ms**: None
- **sync_duration_supported_ms**: None
- **sync_duration_valid_ms**: None
- **count_coverage_pct**: 0.0
- **duration_coverage_pct**: 0.0
- **a_conservation**: missing
- **repeat_advice**: DATA_QUALITY_BLOCKED
- **pilot_status**: NO_GPU_UUID

### P3
- **gpu_uuid**: None
- **gpu_name**: None
- **gpu_pci_bus_id**: None
- **gpu_index**: None
- **pass0_count**: 5
- **pass0_exclusions**: 0
- **pass0_mean_ms**: 42533.274
- **pass0_median_ms**: 42566.87
- **pass0_std_ms**: 783.076
- **pass0_cv_pct**: 1.84
- **pass0_min_ms**: 41744.323
- **pass0_max_ms**: 43708.212
- **pass1_count**: 5
- **pass1_mean_ms**: 12149.363
- **profiler_overhead_ratio**: 0.2856
- **throughput_tokens_per_sec**: 3.0
- **rep_size_mb**: 97.81
- **sqlite_size_mb**: 280.53
- **repeat_advice**: PASS0_5_LIKELY_ENOUGH
- **pilot_status**: NO_GPU_UUID

### P4
- **gpu_uuid**: None
- **gpu_name**: None
- **gpu_pci_bus_id**: None
- **gpu_index**: None
- **pass0_count**: 5
- **pass0_exclusions**: 0
- **pass0_mean_ms**: 42238.403
- **pass0_median_ms**: 42237.175
- **pass0_std_ms**: 307.074
- **pass0_cv_pct**: 0.73
- **pass0_min_ms**: 41865.496
- **pass0_max_ms**: 42695.835
- **pass1_count**: 5
- **pass1_mean_ms**: 12394.947
- **profiler_overhead_ratio**: 0.2935
- **throughput_tokens_per_sec**: 3.0
- **rep_size_mb**: 97.56
- **sqlite_size_mb**: 280.53
- **sync_count_total**: None
- **sync_count_supported**: None
- **sync_count_valid**: None
- **sync_duration_total_ms**: None
- **sync_duration_supported_ms**: None
- **sync_duration_valid_ms**: None
- **count_coverage_pct**: 0.0
- **duration_coverage_pct**: 0.0
- **a_conservation**: missing
- **repeat_advice**: DATA_QUALITY_BLOCKED
- **pilot_status**: NO_GPU_UUID
