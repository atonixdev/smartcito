SHELL := /bin/bash

DEFAULT_BUILD_DIR := $(shell if mkdir -p build >/dev/null 2>&1 && [ -w build ]; then printf '%s' build; else printf '%s' /tmp/orcaos-build; fi)
BUILD_DIR ?= $(DEFAULT_BUILD_DIR)
ISO_DIR := $(BUILD_DIR)/iso
BOOT_DIR := $(ISO_DIR)/boot
GRUB_DIR := $(BOOT_DIR)/grub

CC := gcc
LD := ld
CFLAGS := -Isrc -m32 -ffreestanding -fno-pie -fno-stack-protector -nostdlib -Wall -Wextra -Werror -O2
LDFLAGS := -m elf_i386 -T linker.ld -nostdlib

HAS_ISO_TOOLS := $(shell command -v grub-mkrescue >/dev/null 2>&1 && command -v xorriso >/dev/null 2>&1 && echo 1 || echo 0)

KERNEL_BIN := $(BUILD_DIR)/orcos.bin
ISO_FILE := $(BUILD_DIR)/orcos.iso

SRC_ASM := src/boot.s
SRC_C := \
	src/kernel.c \
	src/orca_drivers.c \
	src/orca_interrupts.c \
	src/orca_init.c \
	src/orca_memory.c \
	src/orca_platform.c \
	src/services/orca_core.c \
	src/services/orca_net.c \
	src/services/orca_security.c \
	src/services/orca_update.c \
	src/services/orca_vision.c
OBJ_ASM := $(patsubst src/%.s,$(BUILD_DIR)/%.o,$(SRC_ASM))
OBJ_C := $(patsubst src/%.c,$(BUILD_DIR)/%.o,$(SRC_C))
OBJS := $(OBJ_ASM) $(OBJ_C)

.PHONY: all clean run iso kernel maybe-iso check-tools check-iso-tools show-build-dir

all: check-tools kernel maybe-iso

check-tools:
	@command -v $(CC) >/dev/null || (echo "Missing gcc" && exit 1)
	@command -v $(LD) >/dev/null || (echo "Missing ld" && exit 1)

check-iso-tools:
	@command -v grub-mkrescue >/dev/null || (echo "Missing grub-mkrescue" && exit 1)
	@command -v xorriso >/dev/null || (echo "Missing xorriso" && exit 1)

show-build-dir:
	@echo $(BUILD_DIR)

$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/%.o: src/%.s | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	$(CC) -m32 -c $< -o $@


$(BUILD_DIR)/%.o: src/%.c | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(KERNEL_BIN): $(OBJS) linker.ld
	$(LD) $(LDFLAGS) -o $@ $(OBJS)

kernel: $(KERNEL_BIN)
	@echo "Built $(KERNEL_BIN)"

maybe-iso:
	@if [ "$(HAS_ISO_TOOLS)" = "1" ]; then \
		$(MAKE) iso; \
	else \
		echo "Skipping ISO image: grub-mkrescue/xorriso not available. Kernel binary: $(KERNEL_BIN)"; \
	fi

iso: check-iso-tools $(KERNEL_BIN)
	@mkdir -p $(GRUB_DIR)
	cp $(KERNEL_BIN) $(BOOT_DIR)/orcos.bin
	cp grub/grub.cfg $(GRUB_DIR)/grub.cfg
	grub-mkrescue -o $(ISO_FILE) $(ISO_DIR)
	@echo "Built $(ISO_FILE)"

run: iso
	@command -v qemu-system-i386 >/dev/null || (echo "Missing qemu-system-i386" && exit 1)
	qemu-system-i386 -cdrom $(ISO_FILE) -m 256M

clean:
	rm -rf $(BUILD_DIR)
