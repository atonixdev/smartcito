#ifndef ORCA_PLATFORM_H
#define ORCA_PLATFORM_H

#include <stddef.h>

typedef struct {
    const char* name;
    const char* summary;
} orca_component_descriptor;

typedef struct {
    const char* name;
    const char* summary;
    const orca_component_descriptor* components;
    size_t component_count;
} orca_layer_descriptor;

const orca_layer_descriptor* orca_get_platform_layers(size_t* layer_count);

#endif