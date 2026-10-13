#include <Windows.h>
#include <cstdint>
#include <vector>
extern "C" std::int32_t native_toolchain_add(std::int32_t, std::int32_t);
static_assert(sizeof(void *) == 8, "x64 only");
// Link Windows SDK + C object + C++ runtime. This executable is NOT run.
int main() {
    const std::vector<std::int32_t> values{1, 3};
    return native_toolchain_add(values[0], values[1]) == 4 && GetCurrentProcessId() ? 0 : 1;
}
