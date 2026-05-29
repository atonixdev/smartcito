# OrcOS

OrcOS Phase 1 is a bootable 32-bit freestanding kernel skeleton aligned with:

- The Little Book About OS Development
- Intel 64 and IA-32 Architectures SDM Volume 3A

## What Is Implemented

- Multiboot header and kernel entry in assembly
- Freestanding C kernel entry (`kernel_main`)
- VGA text output checkpoint proving boot flow
- Linker script loading kernel at 1 MiB
- GRUB ISO generation
- QEMU run target
- Dockerized build environment for reproducibility

## Layout

- `src/boot.s`: Multiboot header, stack setup, jump to C
- `src/kernel.c`: OrcOS Phase 1 checkpoint output
- `linker.ld`: Kernel link layout
- `grub/grub.cfg`: GRUB boot config
- `Makefile`: Build, ISO, and run commands
- `Dockerfile.toolchain`: Toolchain container
- `scripts/build-in-docker.sh`: Containerized build entry

## Build and Run (Host Tools Installed)

1. `cd OrcaOs`
2. `make all`
3. `make run`

## Build and Run (Docker Recommended)

1. `cd OrcaOs`
2. `bash scripts/build-in-docker.sh`
3. `qemu-system-i386 -cdrom build/orcos.iso -m 256M`

The containerized build script auto-detects `docker` or `podman`.

## Cross-Platform Host Commands

Linux/macOS:

1. `cd ..` (repo root)
2. `bash scripts/orcos.sh docker-build`

Windows (PowerShell):

1. `Set-Location <repo-root>`
2. `pwsh -File scripts/orcos.ps1 docker-build`

If you need a specific container runtime, set `CONTAINER_RUNTIME` to `docker` or `podman` before running the command.

If your host lacks `qemu-system-i386`, run QEMU from a separate container or install QEMU locally.

## Checkpoint Expectations

On boot you should see:

- `OrcOS Phase 1 Boot OK`
- `Multiboot magic validated.`

## Next Chapter Checkpoints

- Phase 2: GDT, IDT, ISR, PIC remap, timer IRQ
- Phase 3: Physical memory manager + paging
- Phase 4: Kernel heap + allocator
- Phase 5: Scheduler and syscall entry
- Phase 6: Ring 3 user mode and ELF loader
