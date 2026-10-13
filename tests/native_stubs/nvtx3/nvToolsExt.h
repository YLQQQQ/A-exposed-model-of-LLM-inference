// Declaration-only sink. This syntax check cannot emit real NVTX events.
#pragma once
void nvtxMarkA(const char *);
int nvtxRangePushA(const char *);
int nvtxRangePop();
