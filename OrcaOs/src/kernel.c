#include <stdint.h>
#include <stddef.h>

static volatile uint16_t* const VGA_BUFFER = (uint16_t*)0xB8000;
static const size_t VGA_WIDTH = 80;
static const size_t VGA_HEIGHT = 25;

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

void kernel_main(uint32_t multiboot_magic, uint32_t multiboot_info_ptr) {
    (void)multiboot_info_ptr;

    clear_screen(0x1F);
    write_string_at("OrcOS Phase 1 Boot OK", 1, 2, 0x1F);

    if (multiboot_magic == 0x2BADB002) {
        write_string_at("Multiboot magic validated.", 3, 2, 0x1A);
    } else {
        write_string_at("Multiboot magic invalid.", 3, 2, 0x4F);
    }

    write_string_at("Next: GDT/IDT, ISR, paging, scheduler.", 5, 2, 0x1E);

    for (;;) {
        __asm__ __volatile__("hlt");
    }
}
