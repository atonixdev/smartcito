#include <stdint.h>
#include <stddef.h>

#include "orca_drivers.h"
#include "orca_handoff.h"
#include "orca_init.h"
#include "orca_platform.h"
#include "services/orca_net.h"

#define MULTIBOOT_BOOTLOADER_MAGIC 0x2BADB002u
#define MULTIBOOT_INFO_FLAG_MODULES (1u << 3)

typedef struct {
    uint32_t mod_start;
    uint32_t mod_end;
    uint32_t string;
    uint32_t reserved;
} multiboot_module;

typedef struct {
    uint32_t flags;
    uint32_t mem_lower;
    uint32_t mem_upper;
    uint32_t boot_device;
    uint32_t cmdline;
    uint32_t mods_count;
    uint32_t mods_addr;
} multiboot_info;

typedef struct {
    uint32_t entry_count;
    uint8_t valid;
    uint8_t found_init;
    uint8_t found_manifest;
    uint8_t captured_files;
} initramfs_scan_result;

static volatile uint16_t* const VGA_BUFFER = (uint16_t*)0xB8000;
static const size_t VGA_WIDTH = 80;
static const size_t VGA_HEIGHT = 25;
static const uint16_t SERIAL_COM1_PORT = 0x3F8;
static const uint16_t DEBUGCON_PORT = 0xE9;

static inline void io_out8(uint16_t port, uint8_t value) {
    __asm__ __volatile__("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline uint8_t io_in8(uint16_t port) {
    uint8_t value = 0;
    __asm__ __volatile__("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

static void serial_initialize(void) {
    io_out8(SERIAL_COM1_PORT + 1, 0x00);
    io_out8(SERIAL_COM1_PORT + 3, 0x80);
    io_out8(SERIAL_COM1_PORT + 0, 0x03);
    io_out8(SERIAL_COM1_PORT + 1, 0x00);
    io_out8(SERIAL_COM1_PORT + 3, 0x03);
    io_out8(SERIAL_COM1_PORT + 2, 0xC7);
    io_out8(SERIAL_COM1_PORT + 4, 0x0B);
}

static int serial_can_transmit(void) {
    return (io_in8(SERIAL_COM1_PORT + 5) & 0x20) != 0;
}

static void serial_write_char(char value) {
    while (!serial_can_transmit()) {
    }

    io_out8(SERIAL_COM1_PORT, (uint8_t)value);
    io_out8(DEBUGCON_PORT, (uint8_t)value);
}

static void serial_write_string(const char* value) {
    size_t i = 0;

    while (value[i] != '\0') {
        if (value[i] == '\n') {
            serial_write_char('\r');
        }
        serial_write_char(value[i]);
        ++i;
    }
}

static void serial_write_line(const char* value) {
    serial_write_string(value);
    serial_write_string("\n");
}

static inline uint16_t vga_entry(unsigned char c, uint8_t color) {
    return (uint16_t)c | (uint16_t)color << 8;
}

static void clear_screen(uint8_t color) {
    for (size_t y = 0; y < VGA_HEIGHT; ++y) {
        for (size_t x = 0; x < VGA_WIDTH; ++x) {
            VGA_BUFFER[y * VGA_WIDTH + x] = vga_entry(' ', color);
        }
    }
}

static void write_string_at(const char* s, size_t row, size_t col, uint8_t color) {
    size_t i = 0;
    while (s[i] != '\0' && col + i < VGA_WIDTH) {
        VGA_BUFFER[row * VGA_WIDTH + col + i] = vga_entry((unsigned char)s[i], color);
        ++i;
    }
}

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

    if (buffer_size != expected_length + 1) {
        return 0;
    }

    for (i = 0; i < expected_length; ++i) {
        if (buffer[i] != value[i]) {
            return 0;
        }
    }

    return buffer[expected_length] == '\0';
}

static int buffer_equals_target_path(const char* buffer, size_t buffer_size, const char* value) {
    return buffer_equals_string(buffer, buffer_size, value);
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
            return 0;
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
    return buffer_starts_with(header, "070701", 6) || buffer_starts_with(header, "070702", 6);
}

static initramfs_scan_result inspect_initramfs_module(uint32_t module_start, uint32_t module_end) {
    initramfs_scan_result result;
    const uint8_t* cursor = (const uint8_t*)(uintptr_t)module_start;
    const uint8_t* limit = (const uint8_t*)(uintptr_t)module_end;

    result.entry_count = 0;
    result.valid = 0;
    result.found_init = 0;
    result.found_manifest = 0;
    result.captured_files = 0;

    orca_runtime_handoff_reset();
    orca_runtime_handoff_set_module(module_start, module_end);

    if (module_start == 0 || module_end <= module_start) {
        return result;
    }

    while (cursor + 110u <= limit) {
        const char* header = (const char*)cursor;
        const char* entry_name = 0;
        const uint8_t* file_data = 0;
        const uint8_t* next = 0;
        uint32_t name_size = 0;
        uint32_t file_size = 0;
        int valid = 0;

        if (!cpio_magic_valid(header)) {
            return result;
        }

        file_size = parse_ascii_hex(header + 54, 8, &valid);
        if (!valid) {
            return result;
        }

        name_size = parse_ascii_hex(header + 94, 8, &valid);
        if (!valid || name_size == 0) {
            return result;
        }

        if ((size_t)(limit - cursor) < 110u + (size_t)name_size) {
            return result;
        }

        entry_name = (const char*)(cursor + 110u);
        result.entry_count += 1;

        if (buffer_equals_string(entry_name, name_size, "init")) {
            result.found_init = 1;
        }
        if (buffer_equals_string(entry_name, name_size, "usr/share/orca/rootfs.manifest")) {
            result.found_manifest = 1;
        }
        if (buffer_equals_string(entry_name, name_size, "TRAILER!!!")) {
            result.valid = 1;
            orca_runtime_handoff_set_archive_state(result.valid, result.entry_count);
            return result;
        }

        file_data = align_up_4(cursor + 110u + name_size);
        if (file_data > limit || (size_t)(limit - file_data) < (size_t)file_size) {
            return result;
        }

        if (buffer_equals_target_path(entry_name, name_size, "init")) {
            orca_runtime_handoff_capture_file(ORCA_HANDOFF_FILE_INIT, file_data, file_size);
            result.captured_files += 1u;
        } else if (buffer_equals_target_path(entry_name, name_size, "usr/share/orca/rootfs.manifest")) {
            orca_runtime_handoff_capture_file(ORCA_HANDOFF_FILE_ROOTFS_MANIFEST, file_data, file_size);
            result.captured_files += 1u;
        } else if (buffer_equals_target_path(entry_name, name_size, "etc/orca/ai/config.yaml")) {
            orca_runtime_handoff_capture_file(ORCA_HANDOFF_FILE_AI_CONFIG, file_data, file_size);
            result.captured_files += 1u;
        } else if (buffer_equals_target_path(entry_name, name_size, "etc/orca/network/orca-net.conf")) {
            orca_runtime_handoff_capture_file(ORCA_HANDOFF_FILE_NET_CONFIG, file_data, file_size);
            result.captured_files += 1u;
        } else if (buffer_equals_target_path(entry_name, name_size, "etc/orca/updater/ota.conf")) {
            orca_runtime_handoff_capture_file(ORCA_HANDOFF_FILE_OTA_CONFIG, file_data, file_size);
            result.captured_files += 1u;
        } else if (buffer_equals_target_path(entry_name, name_size, "etc/orca/system/init/profile.conf")) {
            orca_runtime_handoff_capture_file(ORCA_HANDOFF_FILE_SYSTEM_INIT_PROFILE, file_data, file_size);
            result.captured_files += 1u;
        }

        next = align_up_4(file_data + file_size);
        if (next > limit || next < file_data) {
            return result;
        }

        cursor = next;
    }

    return result;
}

static void append_token(char* buffer, size_t buffer_size, const char* token) {
    size_t length = 0;
    size_t i = 0;

    while (length < buffer_size && buffer[length] != '\0') {
        ++length;
    }
    if (length >= buffer_size) {
        return;
    }

    if (length > 0 && length + 1 < buffer_size) {
        buffer[length++] = '+';
        buffer[length] = '\0';
    }

    while (token[i] != '\0' && length + 1 < buffer_size) {
        buffer[length++] = token[i++];
    }
    buffer[length] = '\0';
}

static void mask_to_capability_tokens(orca_driver_capability_mask mask, char* buffer, size_t buffer_size) {
    const orca_driver_capability capabilities[] = {
        ORCA_DRIVER_CAPABILITY_NETWORK,
        ORCA_DRIVER_CAPABILITY_STORAGE,
        ORCA_DRIVER_CAPABILITY_SENSORS,
        ORCA_DRIVER_CAPABILITY_CRYPTO,
        ORCA_DRIVER_CAPABILITY_DISPLAY,
    };
    size_t i = 0;

    if (buffer_size == 0) {
        return;
    }

    buffer[0] = '\0';
    if (mask == 0) {
        append_token(buffer, buffer_size, "none");
        return;
    }

    for (i = 0; i < sizeof(capabilities) / sizeof(capabilities[0]); ++i) {
        if ((mask & capabilities[i]) != 0) {
            append_token(buffer, buffer_size, orca_driver_capability_token(capabilities[i]));
        }
    }
}

static void mask_to_dependency_tokens(
    orca_service_dependency_mask mask,
    char* buffer,
    size_t buffer_size
) {
    const orca_service_id services[] = {
        ORCA_SERVICE_NET,
        ORCA_SERVICE_VISION,
        ORCA_SERVICE_CORE,
        ORCA_SERVICE_SECURITY,
        ORCA_SERVICE_UPDATE,
    };
    size_t i = 0;

    if (buffer_size == 0) {
        return;
    }

    buffer[0] = '\0';
    if (mask == 0) {
        append_token(buffer, buffer_size, "none");
        return;
    }

    for (i = 0; i < sizeof(services) / sizeof(services[0]); ++i) {
        if ((mask & ORCA_SERVICE_BIT(services[i])) != 0) {
            append_token(buffer, buffer_size, orca_service_token(services[i]));
        }
    }
}

static void write_layer_row(const orca_layer_descriptor* layer, size_t row, uint8_t color) {
    write_string_at(layer->name, row, 2, color);
    if (layer->component_count > 0) {
        write_string_at(layer->components[0].name, row, 34, color);
    }
}

static const char* service_status_text(orca_service_boot_status status) {
    switch (status) {
        case ORCA_SERVICE_READY:
            return "ready";
        case ORCA_SERVICE_DEFERRED:
            return "deferred";
        case ORCA_SERVICE_BLOCKED:
            return "blocked";
        default:
            return "unknown";
    }
}

static void write_driver_row(const orca_driver_descriptor* driver, size_t row) {
    write_string_at(driver->name, row, 4, 0x1E);
    write_string_at(orca_driver_capability_token(driver->capability), row, 14, 0x1F);
    write_string_at(orca_boot_phase_token(driver->ready_phase), row, 18, 0x1F);
    write_string_at(driver->ready != 0 ? "ready" : "wait", row, 22, 0x1A);
    write_string_at(driver->summary, row, 30, 0x1F);
}

static void write_service_row(const orca_service_boot_record* record, size_t row) {
    char capability_tokens[16];
    char dependency_tokens[16];

    mask_to_capability_tokens(record->service->required_capabilities, capability_tokens, sizeof(capability_tokens));
    mask_to_dependency_tokens(record->service->dependency_mask, dependency_tokens, sizeof(dependency_tokens));

    write_string_at(record->service->component.name, row, 2, 0x1E);
    write_string_at(record->service->boot_stage, row, 16, 0x1F);
    write_string_at(capability_tokens, row, 36, 0x1F);
    write_string_at(dependency_tokens, row, 48, 0x1F);
    write_string_at(orca_boot_phase_token(record->resolved_phase), row, 58, 0x1F);
    write_string_at(service_status_text(record->status), row, 66, 0x1A);
}

static void write_service_note_row(const orca_service_boot_record* record, size_t row) {
    char capability_tokens[16];
    char dependency_tokens[16];

    if (record->status == ORCA_SERVICE_READY) {
        write_string_at("ok", row, 4, 0x1A);
        return;
    }

    mask_to_capability_tokens(record->missing_capabilities, capability_tokens, sizeof(capability_tokens));
    mask_to_dependency_tokens(record->waiting_on_services, dependency_tokens, sizeof(dependency_tokens));

    write_string_at("wait", row, 4, 0x4E);
    write_string_at("drv:", row, 10, 0x1F);
    write_string_at(capability_tokens, row, 15, 0x1F);
    write_string_at("svc:", row, 28, 0x1F);
    write_string_at(dependency_tokens, row, 33, 0x1F);
    write_string_at("try:", row, 48, 0x1F);
    if (record->attempts > 9) {
        write_string_at("9+", row, 53, 0x1F);
    } else {
        char attempt[2];
        attempt[0] = (char)('0' + record->attempts);
        attempt[1] = '\0';
        write_string_at(attempt, row, 53, 0x1F);
    }
}

static void write_phase_row(const orca_boot_phase_record* record, size_t row) {
    char ready[2];
    char deferred[2];

    ready[0] = (char)('0' + (record->services_ready > 9 ? 9 : record->services_ready));
    ready[1] = '\0';
    deferred[0] = (char)('0' + (record->services_deferred > 9 ? 9 : record->services_deferred));
    deferred[1] = '\0';

    write_string_at(orca_boot_phase_token(record->phase), row, 4, 0x1E);
    write_string_at("ready", row, 16, 0x1F);
    write_string_at(ready, row, 22, 0x1A);
    write_string_at("deferred", row, 28, 0x1F);
    write_string_at(deferred, row, 37, 0x4E);
}

static void write_uint_hex(uint32_t value, size_t row, size_t col, uint8_t color) {
    char buffer[11] = "0x00000000";
    static const char hex[] = "0123456789ABCDEF";
    size_t i = 0;

    for (i = 0; i < 8; ++i) {
        buffer[9 - i] = hex[value & 0xFu];
        value >>= 4;
    }

    write_string_at(buffer, row, col, color);
}

static void serial_write_hex(uint32_t value) {
    char buffer[11] = "0x00000000";
    static const char hex[] = "0123456789ABCDEF";
    size_t i = 0;

    for (i = 0; i < 8; ++i) {
        buffer[9 - i] = hex[value & 0xFu];
        value >>= 4;
    }

    serial_write_string(buffer);
}

static void write_uint_decimal(uint32_t value, size_t row, size_t col, uint8_t color) {
    char buffer[11];
    size_t i = 0;
    size_t start = 0;

    for (i = 0; i < sizeof(buffer); ++i) {
        buffer[i] = '\0';
    }

    if (value == 0u) {
        buffer[0] = '0';
        buffer[1] = '\0';
        write_string_at(buffer, row, col, color);
        return;
    }

    i = sizeof(buffer) - 1;
    while (value > 0u && i > 0u) {
        buffer[--i] = (char)('0' + (value % 10u));
        value /= 10u;
    }

    start = i;
    write_string_at(&buffer[start], row, col, color);
}

static void serial_write_decimal(uint32_t value) {
    char buffer[11];
    size_t i = 0;

    for (i = 0; i < sizeof(buffer); ++i) {
        buffer[i] = '\0';
    }

    if (value == 0u) {
        serial_write_string("0");
        return;
    }

    i = sizeof(buffer) - 1;
    while (value > 0u && i > 0u) {
        buffer[--i] = (char)('0' + (value % 10u));
        value /= 10u;
    }

    serial_write_string(&buffer[i]);
}

static size_t render_boot_policy(size_t start_row) {
    const orca_init_boot_policy* policy = orca_get_init_boot_policy();

    write_string_at("Boot policy:", start_row, 2, 0x1E);
    write_string_at(policy->default_target, start_row, 16, 0x1F);
    write_string_at(policy->retry_deferred_services != 0u ? "retry" : "single", start_row, 38, policy->retry_deferred_services != 0u ? 0x1A : 0x4F);
    write_uint_decimal((uint32_t)policy->max_boot_passes, start_row, 48, 0x1F);

    serial_write_string("boot policy target=");
    serial_write_string(policy->default_target);
    serial_write_string(" retry=");
    serial_write_string(policy->retry_deferred_services != 0u ? "yes" : "no");
    serial_write_string(" passes=");
    serial_write_decimal((uint32_t)policy->max_boot_passes);
    serial_write_string("\n");

    return 1;
}

static size_t render_initramfs_lookup(size_t start_row) {
    orca_initramfs_file_view lookup;

    write_string_at("Initramfs lookup:", start_row, 2, 0x1E);
    if (orca_initramfs_lookup_file("etc/hostname", &lookup) != 0 && lookup.found != 0u) {
        write_string_at("etc/hostname", start_row, 20, 0x1F);
        write_string_at("ready", start_row, 40, 0x1A);
        write_uint_decimal(lookup.size, start_row, 48, 0x1F);

        serial_write_string("initramfs lookup path=");
        serial_write_string(lookup.path);
        serial_write_string(" state=ready size=");
        serial_write_decimal(lookup.size);
        serial_write_string("\n");
    } else {
        write_string_at("etc/hostname", start_row, 20, 0x1F);
        write_string_at("miss", start_row, 40, 0x4F);
        serial_write_line("initramfs lookup path=etc/hostname state=miss size=0");
    }

    return 1;
}

static size_t render_network_policy(const orca_service_boot_record* records, size_t record_count, size_t start_row) {
    const orca_net_runtime_policy* policy = orca_net_get_runtime_policy();
    orca_config_value_view mode_lookup;
    const char* service_state = "missing";
    size_t i = 0;

    for (i = 0; i < record_count; ++i) {
        if (records[i].service->id == ORCA_SERVICE_NET) {
            service_state = service_status_text(records[i].status);
            break;
        }
    }

    (void)orca_handoff_lookup_config_value(ORCA_HANDOFF_FILE_NET_CONFIG, "mode", &mode_lookup);

    if (start_row < VGA_HEIGHT) {
        write_string_at("ORCA-Net policy:", start_row, 2, 0x1E);
        write_string_at(policy->mode, start_row, 20, 0x1F);
        write_string_at(policy->mesh_enabled != 0u ? "mesh" : "no-mesh", start_row, 32, policy->mesh_enabled != 0u ? 0x1A : 0x4F);
        write_string_at(policy->vpn_enabled != 0u ? "vpn" : "no-vpn", start_row, 42, policy->vpn_enabled != 0u ? 0x1A : 0x4F);
    }

    serial_write_string("orca-net runtime mode=");
    serial_write_string(policy->mode);
    serial_write_string(" mesh=");
    serial_write_string(policy->mesh_enabled != 0u ? "yes" : "no");
    serial_write_string(" satellite=");
    serial_write_string(policy->satellite_enabled != 0u ? "yes" : "no");
    serial_write_string(" vpn=");
    serial_write_string(policy->vpn_enabled != 0u ? "yes" : "no");
    serial_write_string(" socket=");
    serial_write_string(policy->control_socket);
    serial_write_string(" service=");
    serial_write_string(service_state);
    serial_write_string(" lookup=");
    if (mode_lookup.found != 0u) {
        size_t j = 0;
        for (j = 0; j < mode_lookup.size; ++j) {
            serial_write_char((char)mode_lookup.value[j]);
        }
    } else {
        serial_write_string("miss");
    }
    serial_write_string("\n");

    return 1;
}

static size_t render_runtime_handoff(size_t start_row) {
    const orca_runtime_handoff* handoff = orca_get_runtime_handoff();
    size_t i = 0;
    size_t rows_used = 1;

    write_string_at("Runtime handoff table:", start_row, 2, 0x1E);
    write_uint_hex(handoff->module_start, start_row, 26, 0x1F);
    write_uint_decimal(handoff->archive_entries, start_row, 38, 0x1F);
    write_string_at(handoff->archive_valid != 0u ? "valid" : "invalid", start_row, 46, handoff->archive_valid != 0u ? 0x1A : 0x4F);
    serial_write_string("runtime handoff files=");
    serial_write_decimal(ORCA_MAX_HANDOFF_FILES);
    serial_write_string("\n");
    serial_write_string("runtime handoff module=");
    serial_write_hex(handoff->module_start);
    serial_write_string(" entries=");
    serial_write_decimal(handoff->archive_entries);
    serial_write_string(" state=");
    serial_write_string(handoff->archive_valid != 0u ? "valid" : "invalid");
    serial_write_string("\n");

    for (i = 0; i < ORCA_MAX_HANDOFF_FILES && start_row + 1 + i < VGA_HEIGHT; ++i) {
        const orca_handoff_file_record* record = &handoff->files[i];
        write_string_at(record->path, start_row + 1 + i, 4, 0x1F);
        write_string_at(record->available != 0u ? "ready" : "miss", start_row + 1 + i, 42, record->available != 0u ? 0x1A : 0x4F);
        write_uint_decimal(record->size, start_row + 1 + i, 50, 0x1F);

        serial_write_string("handoff ");
        serial_write_string(orca_handoff_file_token(record->id));
        serial_write_string(" state=");
        serial_write_string(record->available != 0u ? "ready" : "miss");
        serial_write_string(" size=");
        serial_write_decimal(record->size);
        serial_write_string("\n");
        rows_used += 1;
    }

    return rows_used;
}

static void write_module_string(uint32_t address, size_t row, size_t col, uint8_t color) {
    const char* module_string = (const char*)(uintptr_t)address;

    if (address == 0) {
        write_string_at("(no-cmdline)", row, col, color);
        return;
    }

    write_string_at(module_string, row, col, color);
}

static size_t render_multiboot_modules(uint32_t info_ptr, size_t start_row) {
    const multiboot_info* info = (const multiboot_info*)(uintptr_t)info_ptr;
    const multiboot_module* modules = 0;
    initramfs_scan_result scan_result;
    size_t count = 0;
    size_t i = 0;
    size_t rows_used = 0;

    if (info_ptr == 0 || (info->flags & MULTIBOOT_INFO_FLAG_MODULES) == 0 || info->mods_count == 0) {
        write_string_at("Initramfs handoff: no multiboot modules", start_row, 2, 0x4E);
        serial_write_line("initramfs handoff: no multiboot modules");
        return 1;
    }

    modules = (const multiboot_module*)(uintptr_t)info->mods_addr;
    count = info->mods_count;
    rows_used = count + 1;

    write_string_at("Initramfs handoff: multiboot modules detected", start_row, 2, 0x1A);
    serial_write_line("initramfs handoff: multiboot modules detected");
    for (i = 0; i < count && start_row + 1 + i < VGA_HEIGHT; ++i) {
        write_string_at("mod", start_row + 1 + i, 4, 0x1E);
        write_uint_hex(modules[i].mod_start, start_row + 1 + i, 10, 0x1F);
        write_uint_hex(modules[i].mod_end, start_row + 1 + i, 22, 0x1F);
        write_module_string(modules[i].string, start_row + 1 + i, 34, 0x1F);

        serial_write_string("module ");
        serial_write_hex((uint32_t)i);
        serial_write_string(" start=");
        serial_write_hex(modules[i].mod_start);
        serial_write_string(" end=");
        serial_write_hex(modules[i].mod_end);
        serial_write_string(" cmd=");
        if (modules[i].string == 0) {
            serial_write_line("(no-cmdline)");
        } else {
            serial_write_line((const char*)(uintptr_t)modules[i].string);
        }
    }

    scan_result = inspect_initramfs_module(modules[0].mod_start, modules[0].mod_end);
    if (start_row + rows_used < VGA_HEIGHT) {
        write_string_at("Initramfs scan:", start_row + rows_used, 2, 0x1E);
        write_string_at(scan_result.valid != 0 ? "newc-ok" : "invalid", start_row + rows_used, 18, scan_result.valid != 0 ? 0x1A : 0x4F);
    }
    if (start_row + rows_used + 1 < VGA_HEIGHT) {
        write_string_at("entries", start_row + rows_used + 1, 2, 0x1F);
        write_uint_hex(scan_result.entry_count, start_row + rows_used + 1, 10, 0x1F);
        write_string_at(scan_result.found_init != 0 ? "init:yes" : "init:no", start_row + rows_used + 1, 24, scan_result.found_init != 0 ? 0x1A : 0x4F);
        write_string_at(scan_result.found_manifest != 0 ? "manifest:yes" : "manifest:no", start_row + rows_used + 1, 36, scan_result.found_manifest != 0 ? 0x1A : 0x4F);
        write_string_at("captured", start_row + rows_used + 1, 52, 0x1F);
        write_uint_decimal(scan_result.captured_files, start_row + rows_used + 1, 62, 0x1F);
        rows_used += 2;
    }

    serial_write_string("initramfs scan valid=");
    serial_write_line(scan_result.valid != 0 ? "yes" : "no");
    serial_write_string("initramfs scan entries=");
    serial_write_hex(scan_result.entry_count);
    serial_write_string(" init=");
    serial_write_string(scan_result.found_init != 0 ? "yes" : "no");
    serial_write_string(" manifest=");
    serial_write_line(scan_result.found_manifest != 0 ? "yes" : "no");
    serial_write_string("initramfs captured files=");
    serial_write_decimal(scan_result.captured_files);
    serial_write_string("\n");

    return rows_used;
}

void kernel_main(uint32_t multiboot_magic, uint32_t multiboot_info_ptr) {
    size_t driver_count = 0;
    size_t layer_count = 0;
    size_t booted_services = 0;
    size_t phase_count = 0;
    size_t module_rows = 0;
    size_t policy_rows = 0;
    size_t handoff_rows = 0;
    size_t lookup_rows = 0;
    const orca_driver_descriptor* drivers = orca_get_registered_drivers(&driver_count);
    const orca_layer_descriptor* layers = orca_get_platform_layers(&layer_count);
    orca_service_boot_record service_records[ORCA_MAX_SYSTEM_SERVICES];
    orca_boot_phase_record phase_records[ORCA_BOOT_PHASE_COMPLETE];

    serial_initialize();
    clear_screen(0x1F);
    write_string_at("ORCA OS Boot Checkpoint", 1, 2, 0x1F);
    serial_write_line("ORCA OS Boot Checkpoint");

    if (multiboot_magic == MULTIBOOT_BOOTLOADER_MAGIC) {
        write_string_at("Multiboot magic validated.", 3, 2, 0x1A);
        serial_write_line("multiboot magic validated");
    } else {
        write_string_at("Multiboot magic invalid.", 3, 2, 0x4F);
        serial_write_line("multiboot magic invalid");
    }
    write_uint_hex(multiboot_magic, 3, 30, 0x1F);
    serial_write_string("multiboot magic value=");
    serial_write_hex(multiboot_magic);
    serial_write_string("\n");

    module_rows = render_multiboot_modules(multiboot_info_ptr, 4);
    policy_rows = render_boot_policy(5 + module_rows);
    handoff_rows = render_runtime_handoff(6 + module_rows + policy_rows);
    lookup_rows = render_initramfs_lookup(7 + module_rows + policy_rows + handoff_rows);

    write_string_at("3-layer ORCA OS scaffold loaded:", 8 + module_rows + policy_rows + handoff_rows + lookup_rows, 2, 0x1E);

    if (layer_count > 0) {
        write_layer_row(&layers[0], 9 + module_rows + policy_rows + handoff_rows + lookup_rows, 0x1E);
    }
    if (layer_count > 1) {
        write_layer_row(&layers[1], 10 + module_rows + policy_rows + handoff_rows + lookup_rows, 0x1E);
    }
    if (layer_count > 2) {
        write_layer_row(&layers[2], 11 + module_rows + policy_rows + handoff_rows + lookup_rows, 0x1E);
    }

    write_string_at("Layer 1 driver registry:", 13 + module_rows + policy_rows + handoff_rows + lookup_rows, 2, 0x1E);
    for (size_t i = 0; i < driver_count && 14 + module_rows + policy_rows + handoff_rows + lookup_rows + i < VGA_HEIGHT; ++i) {
        write_driver_row(&drivers[i], 14 + module_rows + policy_rows + handoff_rows + lookup_rows + i);
    }

    booted_services = orca_boot_system_services(
        service_records,
        ORCA_MAX_SYSTEM_SERVICES,
        phase_records,
        ORCA_BOOT_PHASE_COMPLETE,
        &phase_count
    );

    render_network_policy(service_records, booted_services, 23);

    write_string_at("Boot phases:", 19 + module_rows + policy_rows + handoff_rows + lookup_rows, 2, 0x1E);
    for (size_t i = 0; i < phase_count && 20 + module_rows + policy_rows + handoff_rows + lookup_rows + i < VGA_HEIGHT; ++i) {
        write_phase_row(&phase_records[i], 20 + module_rows + policy_rows + handoff_rows + lookup_rows + i);
    }

    write_string_at("Layer 2 service table:", 19 + module_rows + policy_rows + handoff_rows + lookup_rows, 44, 0x1E);
    write_string_at("svc           stage       drv         dep       ph   status", 20 + module_rows + policy_rows + handoff_rows + lookup_rows, 20, 0x1F);
    for (size_t i = 0; i < booted_services && 21 + module_rows + policy_rows + handoff_rows + lookup_rows + i < VGA_HEIGHT; ++i) {
        write_service_row(&service_records[i], 21 + module_rows + policy_rows + handoff_rows + lookup_rows + i);
    }

    if (booted_services > 0 && 21 + module_rows + policy_rows + handoff_rows + lookup_rows + booted_services < VGA_HEIGHT) {
        write_service_note_row(&service_records[booted_services - 1], 21 + module_rows + policy_rows + handoff_rows + lookup_rows + booted_services);
    }

    write_string_at("Next: interrupts, memory, scheduler, user-mode runtime.", 24, 2, 0x1E);
    serial_write_line("boot checkpoint complete");

    for (;;) {
        __asm__ __volatile__("hlt");
    }
}
