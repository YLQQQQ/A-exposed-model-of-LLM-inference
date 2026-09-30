"""Known resource allocation facts, NOT an A category or completion rule."""
import re

VERSION = 'exposedpath-allocation-diagnostic/0.1.0'
MEMORY_REFERENCE = 'https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/group__CUDART__MEMORY.html'
ORDERING_REFERENCE = 'https://docs.nvidia.com/cuda/archive/12.4.1/cuda-c-programming-guide/index.html#implicit-synchronization'


def describe_allocation(name):
    if not isinstance(name, str) or not re.fullmatch(r'cudaMalloc(?:_v[1-9][0-9]*)?', name):
        return None
    return dict(allocation_diagnostic_version=VERSION, semantic_role='KNOWN_ALLOCATION',
                registry_rule_id='ALLOCATION-CUDAMALLOC-001', completion_support='UNSUPPORTED',
                completion_scope=None, semantic_references=[MEMORY_REFERENCE, ORDERING_REFERENCE])
