"""Non-synchronizing completion point producer (explicit Gate8 opt-in)."""
from copy import deepcopy
import json
import time

from .gate8_identity import validate_shape

BOUNDARY_PREFIX = "EXPOSEDPATH_BOUNDARY_V1:"


class Gate8BoundaryRecorder:
    def __init__(self, identity, boundary_ids, *, marker_sink=None, clock_ns=time.perf_counter_ns):
        validate_shape("identity", identity)
        if len(boundary_ids) < 2 or any(not isinstance(x, str) or not x for x in boundary_ids) or len(set(boundary_ids)) != len(boundary_ids):
            raise ValueError("BOUNDARY_MISSING: explicit unique request/token boundary plan required")
        if (identity["pass_id"] == "pass1") != (marker_sink is not None):
            raise ValueError("IDENTITY_CONFLICT: pass1 requires marker sink; pass0 forbids it")
        self.identity = deepcopy(identity)
        self.boundary_ids = list(boundary_ids)
        self.marker_sink = marker_sink
        self.clock_ns = clock_ns
        self.records = []

    def observe(self, host_observed_ns, token_index=None):
        ordinal = 0 if token_index is None else token_index + 1
        if ordinal != len(self.records) or ordinal >= len(self.boundary_ids):
            raise ValueError("BOUNDARY_ORDER_INVALID: producer sequence")
        payload = {
            "schema_version": "exposedpath-boundary-payload/0.1.0", "kind": "boundary",
            "identity": deepcopy(self.identity), "boundary_id": self.boundary_ids[ordinal],
            "boundary_kind": "request_start" if token_index is None else "token_ready",
            "token_index": token_index,
            "completion_mechanism": "predrained_inputs_resident" if token_index is None else "device_to_host_token_ids",
            "marker_role": "non_sync_marker",
        }
        validate_shape("boundary_payload", payload)
        label = BOUNDARY_PREFIX + json.dumps(payload, sort_keys=True, separators=(",", ":"))
        before = self.clock_ns()
        if self.marker_sink is not None:
            self.marker_sink(label)
        after = self.clock_ns()
        if not host_observed_ns <= before <= after:
            raise ValueError("BOUNDARY_ORDER_INVALID: host marker diagnostics")
        self.records.append({"payload": payload, "host_observed_ns": host_observed_ns,
                             "host_before_marker_ns": before, "host_after_marker_ns": after,
                             "host_clock_id": "PYTHON_PERF_COUNTER_NS"})
