#include "orca_handoff.h"

typedef struct {
    orca_handoff_file_id id;
    const char* path;
} orca_handoff_target;

static const orca_handoff_target ORCA_HANDOFF_TARGETS[ORCA_MAX_HANDOFF_FILES] = {
    { ORCA_HANDOFF_FILE_INIT, "init" },
    { ORCA_HANDOFF_FILE_ROOTFS_MANIFEST, "usr/share/orca/rootfs.manifest" },
    { ORCA_HANDOFF_FILE_AI_CONFIG, "etc/orca/ai/config.yaml" },
    { ORCA_HANDOFF_FILE_NET_CONFIG, "etc/orca/network/orca-net.conf" },
    { ORCA_HANDOFF_FILE_OTA_CONFIG, "etc/orca/updater/ota.conf" },
    { ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE, "etc/orca/system/init/profile.conf" },
};

static orca_runtime_handoff ORCA_RUNTIME_HANDOFF = {
    0u,
    0u,
    0u,
    0u,
    {
        { ORCA_HANDOFF_FILE_INIT, "init", 0, 0u, 0u },
        { ORCA_HANDOFF_FILE_ROOTFS_MANIFEST, "usr/share/orca/rootfs.manifest", 0, 0u, 0u },
        { ORCA_HANDOFF_FILE_AI_CONFIG, "etc/orca/ai/config.yaml", 0, 0u, 0u },
        { ORCA_HANDOFF_FILE_NET_CONFIG, "etc/orca/network/orca-net.conf", 0, 0u, 0u },
        { ORCA_HANDOFF_FILE_OTA_CONFIG, "etc/orca/updater/ota.conf", 0, 0u, 0u },
        { ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE, "etc/orca/system/init/profile.conf", 0, 0u, 0u },
    }
};

static size_t string_length(const char* value) {
    size_t length = 0;

    while (value[length] != '\0') {
        ++length;
    }

    return length;
}

static int buffer_equals_string(const char* buffer, size_t buffer_size, const char* value) {
    size_t expected_length = string_length(value);
    size_t i = 0;

    if (buffer_size != expected_length + 1u) {
        return 0;
    }

    for (i = 0; i < expected_length; ++i) {
        if (buffer[i] != value[i]) {
            return 0;
        }
    }

    return buffer[expected_length] == '\0';
}

static int buffer_starts_with(const char* buffer, const char* value, size_t length) {
    size_t i = 0;

    for (i = 0; i < length; ++i) {
        if (buffer[i] != value[i]) {
            return 0;
        }
    }

    return 1;
}

static const uint8_t* trim_leading_ascii_space(const uint8_t* value, const uint8_t* limit) {
    while (value < limit && (*value == ' ' || *value == '\t')) {
        ++value;
    }
    return value;
}

static const uint8_t* trim_trailing_ascii_space(const uint8_t* value, const uint8_t* start) {
    while (value > start && (value[-1] == ' ' || value[-1] == '\t' || value[-1] == '\r')) {
        --value;
    }
    return value;
}

static uint32_t parse_ascii_hex(const char* value, size_t length, int* valid) {
    uint32_t parsed = 0;
    size_t i = 0;

    *valid = 1;
    for (i = 0; i < length; ++i) {
        parsed <<= 4;
        if (value[i] >= '0' && value[i] <= '9') {
            parsed |= (uint32_t)(value[i] - '0');
        } else if (value[i] >= 'A' && value[i] <= 'F') {
            parsed |= (uint32_t)(value[i] - 'A' + 10);
        } else if (value[i] >= 'a' && value[i] <= 'f') {
            parsed |= (uint32_t)(value[i] - 'a' + 10);
        } else {
            *valid = 0;
            return 0u;
        }
    }

    return parsed;
}

static const uint8_t* align_up_4(const uint8_t* value) {
    uintptr_t address = (uintptr_t)value;
    address = (address + 3u) & ~(uintptr_t)3u;
    return (const uint8_t*)address;
}

static int cpio_magic_valid(const char* header) {
    return buffer_starts_with(header, "070701", 6u) || buffer_starts_with(header, "070702", 6u);
}

void orca_runtime_handoff_reset(void) {
    size_t i = 0;

    ORCA_RUNTIME_HANDOFF.module_start = 0u;
    ORCA_RUNTIME_HANDOFF.module_end = 0u;
    ORCA_RUNTIME_HANDOFF.archive_entries = 0u;
    ORCA_RUNTIME_HANDOFF.archive_valid = 0u;

    for (i = 0; i < ORCA_MAX_HANDOFF_FILES; ++i) {
        ORCA_RUNTIME_HANDOFF.files[i].data = 0;
        ORCA_RUNTIME_HANDOFF.files[i].size = 0u;
        ORCA_RUNTIME_HANDOFF.files[i].available = 0u;
    }
}

void orca_runtime_handoff_set_module(uint32_t module_start, uint32_t module_end) {
    ORCA_RUNTIME_HANDOFF.module_start = module_start;
    ORCA_RUNTIME_HANDOFF.module_end = module_end;
}

void orca_runtime_handoff_set_archive_state(uint8_t archive_valid, uint32_t archive_entries) {
    ORCA_RUNTIME_HANDOFF.archive_valid = archive_valid;
    ORCA_RUNTIME_HANDOFF.archive_entries = archive_entries;
}

void orca_runtime_handoff_capture_file(orca_handoff_file_id id, const uint8_t* data, uint32_t size) {
    size_t i = 0;

    for (i = 0; i < ORCA_MAX_HANDOFF_FILES; ++i) {
        if (ORCA_HANDOFF_TARGETS[i].id == id) {
            ORCA_RUNTIME_HANDOFF.files[i].data = data;
            ORCA_RUNTIME_HANDOFF.files[i].size = size;
            ORCA_RUNTIME_HANDOFF.files[i].available = 1u;
            return;
        }
    }
}

const orca_runtime_handoff* orca_get_runtime_handoff(void) {
    return &ORCA_RUNTIME_HANDOFF;
}

const orca_handoff_file_record* orca_get_handoff_file(orca_handoff_file_id id) {
    size_t i = 0;

    for (i = 0; i < ORCA_MAX_HANDOFF_FILES; ++i) {
        if (ORCA_RUNTIME_HANDOFF.files[i].id == id) {
            return &ORCA_RUNTIME_HANDOFF.files[i];
        }
    }

    return 0;
}

const orca_handoff_file_record* orca_get_init_program_file(void) {
    return orca_get_handoff_file(ORCA_HANDOFF_FILE_INIT);
}

const orca_handoff_file_record* orca_get_rootfs_manifest_file(void) {
    return orca_get_handoff_file(ORCA_HANDOFF_FILE_ROOTFS_MANIFEST);
}

const orca_handoff_file_record* orca_get_ai_config_file(void) {
    return orca_get_handoff_file(ORCA_HANDOFF_FILE_AI_CONFIG);
}

const orca_handoff_file_record* orca_get_network_config_file(void) {
    return orca_get_handoff_file(ORCA_HANDOFF_FILE_NET_CONFIG);
}

const orca_handoff_file_record* orca_get_update_config_file(void) {
    return orca_get_handoff_file(ORCA_HANDOFF_FILE_OTA_CONFIG);
}

const orca_handoff_file_record* orca_get_init_profile_file(void) {
    return orca_get_handoff_file(ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE);
}

int orca_initramfs_lookup_file(const char* path, orca_initramfs_file_view* view) {
    const uint8_t* cursor = (const uint8_t*)(uintptr_t)ORCA_RUNTIME_HANDOFF.module_start;
    const uint8_t* limit = (const uint8_t*)(uintptr_t)ORCA_RUNTIME_HANDOFF.module_end;

    if (view != 0) {
        view->path = path;
        view->data = 0;
        view->size = 0u;
        view->found = 0u;
    }

    if (path == 0 || view == 0 || ORCA_RUNTIME_HANDOFF.archive_valid == 0u) {
        return 0;
    }

    while (cursor + 110u <= limit) {
        const char* header = (const char*)cursor;
        const char* entry_name = 0;
        const uint8_t* file_data = 0;
        const uint8_t* next = 0;
        uint32_t name_size = 0u;
        uint32_t file_size = 0u;
        int valid = 0;

        if (!cpio_magic_valid(header)) {
            return 0;
        }

        file_size = parse_ascii_hex(header + 54, 8u, &valid);
        if (!valid) {
            return 0;
        }

        name_size = parse_ascii_hex(header + 94, 8u, &valid);
        if (!valid || name_size == 0u) {
            return 0;
        }

        if ((size_t)(limit - cursor) < 110u + (size_t)name_size) {
            return 0;
        }

        entry_name = (const char*)(cursor + 110u);
        if (buffer_equals_string(entry_name, name_size, "TRAILER!!!")) {
            return 0;
        }

        file_data = align_up_4(cursor + 110u + name_size);
        if (file_data > limit || (size_t)(limit - file_data) < (size_t)file_size) {
            return 0;
        }

        if (buffer_equals_string(entry_name, name_size, path)) {
            view->path = entry_name;
            view->data = file_data;
            view->size = file_size;
            view->found = 1u;
            return 1;
        }

        next = align_up_4(file_data + file_size);
        if (next > limit || next < file_data) {
            return 0;
        }

        cursor = next;
    }

    return 0;
}

int orca_initramfs_lookup_config_value(const char* path, const char* key, orca_config_value_view* view) {
    orca_initramfs_file_view file_view;
    const uint8_t* cursor = 0;
    const uint8_t* limit = 0;
    size_t key_length = 0;

    if (view != 0) {
        view->key = key;
        view->value = 0;
        view->size = 0u;
        view->found = 0u;
    }

    if (path == 0 || key == 0 || view == 0 || orca_initramfs_lookup_file(path, &file_view) == 0 || file_view.found == 0u) {
        return 0;
    }

    key_length = string_length(key);
    cursor = file_view.data;
    limit = file_view.data + file_view.size;

    while (cursor < limit) {
        const uint8_t* line_start = cursor;
        const uint8_t* line_end = cursor;
        const uint8_t* trimmed_start = 0;
        const uint8_t* value_start = 0;
        const uint8_t* value_end = 0;

        while (line_end < limit && *line_end != '\n') {
            ++line_end;
        }

        trimmed_start = trim_leading_ascii_space(line_start, line_end);
        if (trimmed_start < line_end && *trimmed_start != '#') {
            if ((size_t)(line_end - trimmed_start) > key_length &&
                buffer_starts_with((const char*)trimmed_start, key, key_length) &&
                (trimmed_start[key_length] == '=' || trimmed_start[key_length] == ':')) {
                value_start = trimmed_start + key_length + 1u;
                value_start = trim_leading_ascii_space(value_start, line_end);
                value_end = trim_trailing_ascii_space(line_end, value_start);
                view->value = value_start;
                view->size = (uint32_t)(value_end - value_start);
                view->found = 1u;
                return 1;
            }
        }

        cursor = line_end < limit ? line_end + 1u : line_end;
    }

    return 0;
}

int orca_handoff_lookup_config_value(orca_handoff_file_id id, const char* key, orca_config_value_view* view) {
    const orca_handoff_file_record* record = orca_get_handoff_file(id);

    if (record == 0 || record->available == 0u) {
        if (view != 0) {
            view->key = key;
            view->value = 0;
            view->size = 0u;
            view->found = 0u;
        }
        return 0;
    }

    return orca_initramfs_lookup_config_value(record->path, key, view);
}

const char* orca_handoff_file_token(orca_handoff_file_id id) {
    switch (id) {
        case ORCA_HANDOFF_FILE_INIT:
            return "init";
        case ORCA_HANDOFF_FILE_ROOTFS_MANIFEST:
            return "manifest";
        case ORCA_HANDOFF_FILE_AI_CONFIG:
            return "ai-cfg";
        case ORCA_HANDOFF_FILE_NET_CONFIG:
            return "net-cfg";
        case ORCA_HANDOFF_FILE_OTA_CONFIG:
            return "ota-cfg";
        case ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE:
            return "init-prof";
        default:
            return "unknown";
    }
}