#include "orca_interrupts.h"

static int interrupts_ready = 0;

int orca_interrupts_initialize(void) {
    interrupts_ready = 1;
    return interrupts_ready;
}

int orca_interrupts_ready(void) {
    return interrupts_ready;
}