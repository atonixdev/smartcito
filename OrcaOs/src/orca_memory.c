#include "orca_memory.h"

static int memory_ready = 0;

int orca_memory_initialize(void) {
    memory_ready = 1;
    return memory_ready;
}

int orca_memory_ready(void) {
    return memory_ready;
}