SHELL := /bin/bash

BUILD_DIR := build
ISO_DIR := $(BUILD_DIR)/iso
BOOT_DIR := $(ISO_DIR)/boot
GRUB_DIR := $(BOOT_DIR)/grub

CC := gcc
LD := ld
CFLAGS := -m32 -ffreestanding -fno-pie -fno-stack-protector -nostdlib -Wall -Wextra -Werror -O2
LDFLAGS := -m elf_i386 -T linker.ld -nostdlib

KERNEL_BIN := $(BUILD_DIR)/orcos.bin
ISO_FILE := $(BUILD_DIR)/orcos.iso

SRC_BOOT := src/boot.s
SRC_KERNEL := src/kernel.c
OBJ_BOOT := $(BUILD_DIR)/boot.o
OBJ_KERNEL := $(BUILD_DIR)/kernel.o

.PHONY: all clean run iso check-tools

all: check-tools iso

check-tools:
	@command -v $(CC) >/dev/null || (echo "Missing gcc" && exit 1)
	@command -v $(LD) >/dev/null || (echo "Missing ld" && exit 1)
	@command -v grub-mkrescue >/dev/null || (echo "Missing grub-mkrescue" && exit 1)
	@command -v xorriso >/dev/null || (echo "Missing xorriso" && exit 1)

$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(OBJ_BOOT): $(SRC_BOOT) | $(BUILD_DIR)
	$(CC) -m32 -c $< -o $@

$(OBJ_KERNEL): $(SRC_KERNEL) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(KERNEL_BIN): $(OBJ_BOOT) $(OBJ_KERNEL) linker.ld
	$(LD) $(LDFLAGS) -o $@ $(OBJ_BOOT) $(OBJ_KERNEL)

iso: $(KERNEL_BIN)
	@mkdir -p $(GRUB_DIR)
	cp $(KERNEL_BIN) $(BOOT_DIR)/orcos.bin
	cp grub/grub.cfg $(GRUB_DIR)/grub.cfg
	grub-mkrescue -o $(ISO_FILE) $(ISO_DIR)
	@echo "Built $(ISO_FILE)"

run: iso
	qemu-system-i386 -cdrom $(ISO_FILE) -m 256M

clean:
	rm -rf $(BUILD_DIR)
