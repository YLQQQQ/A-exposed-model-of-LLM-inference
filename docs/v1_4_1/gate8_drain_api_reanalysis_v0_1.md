# Gate8 drain API suffix audit / offline reanalysis 0.1

## Scope and immutable source

Engineering implementation diagnostic only. Execution commit
`8ef1385604c7d35d8ac15efbe76aa9d3a26ba9a2`; original attempt
`qualification_20260927T143910Z_4b9c1fd9128d4badb1f451843fd51aea` remains BLOCKED.
No server, GPU, model or Nsight operation was performed in this audit.

Sealed ZIP: 246133 bytes, SHA256
`42c40987ae982e9887a5fb2dde0785759d6421ba52efcdae476ee9cb4c3703a5`.
Manifest SHA256 `37ccd956c64d9957f880c2cea03303f85c357ca7019f79a32a1c005631f99ae6`.
Independently checked CRC, safe unique paths, exact 52-item manifest coverage,
sizes and hashes. All 53 extracted files were unchanged after offline analysis.
The original collection report still says `QUALIFICATION_ORACLE_DRAIN_API`.
Server receipt records clean execution commit; its targeted log records 68 passed
in 47.66s (server evidence, not locally executed tests).

## Root cause and bounded repair

Drain markers contain Runtime rows 10 and 18: `cudaDeviceSynchronize_v3020`,
returnValue=0, correlationId 130/140. Physical context-sync rows 2/6 match.
A third device-sync at Runtime row 26 belongs outside these drain windows and
must not be selected. Oracle drain name matching used an exact unversioned
name; operation matching elsewhere already accepted version suffixes.

Oracle 0.1.2 accepts only full-match `cudaDeviceSynchronize(?:_v[0-9]+)?`.
No other API is normalized, no arbitrary suffix/prefix/whitespace is accepted.
Window/thread, uniqueness, successful return, correlation, physical sync kind,
identity and warning gates are unchanged; Measurement Contract and S/A/B unchanged.

Tests first: versioned positive and two downstream guard tests failed at the old
name check (3 failed, 12 passed); after the two-line production change, qualification
and target-Python suites passed 51 tests in 41.84s. Negative tests include malformed
suffix, Unicode digit, other APIs, duplicate calls, failed return, wrong thread,
wrong correlation/sync kind and unknown-impact warning. Static compileall,
contract internal consistency 37/37, Canonical boundary and oracle independence passed.

## Offline result and limits

Run the existing `gate8_qualification.audit` against a byte-identical extracted copy,
with a new `derived-oracle-0.1.2` output; do not modify the old audit directory.
Result: `CONTROLLED_SCOPE_MATCH`. Execution/plan/producer and profiler launch
identity checks, export lineage, Canonical/projection/Engineering A processing,
two requests and all six request/prefill/decode A windows passed. Both LEGACY and
PER_THREAD conditional suffix proofs match independent members (1, 2, 4 per request).
Tokens are 11/12 and 21/22; all component values match, not only their sum.
Local gaps are empty and all six A_unattributed values are zero in this construction.

Verified SQLite SHA256: `9894e76f395d6f44bd10f83742d4340278f9235ed0903cf4589befd37ff124fd`;
REP SHA256: `323b24b22b3f0daad66579dc28287fee60123f6c1ba9f12d08313c6f97715d03`.
Profiler launch row 4 binds PID 61132/global PID 282500601479168 to the producer.
Component order below is Host/API/device-wait/sync-residual/unattributed; units ns:

| Request | Window | Components |
|---|---|---|
| 0 | full_request | 1283948 / 53148 / 25984 / 438459 / 0 |
| 0 | prefill | 768126 / 29123 / 1952 / 257726 / 0 |
| 0 | decode | 515822 / 24025 / 24032 / 180733 / 0 |
| 1 | full_request | 1498397 / 179167 / 24800 / 654534 / 0 |
| 1 | prefill | 1023378 / 147420 / 23424 / 611393 / 0 |
| 1 | decode | 475019 / 31747 / 1376 / 43141 / 0 |

This capture has 14 informational diagnostics and no severity=2 records. That
does not establish zero loss, does not establish why the older warning disappeared,
and does not resolve the older attempt. `dropped_records_status=UNKNOWN`,
`measurement_validity=NOT_ASSESSED`, D disabled, Q0/Gate8 NOT_RUN remain explicit.
No new technical rejection occurred in this offline chain; qualification eligibility
is still a separate review, not conferred by post-hoc repair or this positive example.

Local ignored index: `.local/diagnostics/drain_api_v0_1/reanalysis.json`,
with per-file input hashes, source-code hash and derived output hash; raw data and
machine-specific paths are not committed. Next action is review of this bounded
offline result against the existing qualification plan, not server recollection.
