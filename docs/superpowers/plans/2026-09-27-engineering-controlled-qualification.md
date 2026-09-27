# Engineering controlled qualification implementation plan

Goal: implement the approved qualification-next/0.1 connector, not grant qualification.
Spec: `docs/v1_4_1/gate8_engineering_qualification_next_v0_1.md`.
Work in root main as requested; no server/GPU/Nsight execution.

- [x] Tests first: actual producer files with CPU native double and synthetic SQLite;
  literal A expectations; missing boundary/correlation/identity/warning negatives.
- [x] New construction NULL-FIFO-D2H/0.1, explicit controlled declaration/receipt;
  separate native DLL using existing small kernel/copy/read design; old entry unchanged.
  Two sequential requests, tokens11/12 and21/22; first-token internal wait plus two
  token-copy waits. Setup and warmup outside request; existing recorders observe drain.
- [x] Independent Raw oracle: original operation/point labels, API/correlation/physical
  sync and activity membership; interval arithmetic only, no S/A imports/calls.
  Compare concrete A classes; unknown warnings reject, bounded API gaps unattributed.
- [x] Reuse sealed input→Canonical→Engineering A path; explicit controlled schema,
  never fake model/backend fields. New output only, partial/failure never qualifies.
- [x] Offline integration and launcher guards, scoped then CPU full/static,
  progress/handoff, code review, commit/push, one incremental bundle from247f4fd.
  Fixed single-block server plan, bounded collection/export/no retry, one receipt ZIP.

No change to physical S/B, frozen A, old Q0 or old evidence; D/Signature disabled.
Real qualifications remain NOT_RUN; declared assumptions do not become observed facts.
Native ABI/build remains target-platform work, not claimed from CPU tests.
Verification: qualification19, interface42, expanded99; CPU full1472/5 plus final
two review cases in qualification19; static checks PASS. Delivery command is prepared
only; real collection/export, Q0 and Gate8 acceptance are NOT_RUN.
