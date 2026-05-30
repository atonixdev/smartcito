#ifndef ORCA_NET_H
#define ORCA_NET_H

#include "services/orca_service.h"

typedef struct {
	const char* mode;
	const char* control_socket;
	uint8_t mesh_enabled;
	uint8_t satellite_enabled;
	uint8_t vpn_enabled;
	uint8_t config_loaded;
} orca_net_runtime_policy;

extern const orca_service_descriptor ORCA_NET_SERVICE;
const orca_net_runtime_policy* orca_net_get_runtime_policy(void);

#endif