# OrcOS

OrcOS Phase 1 is a bootable 32-bit freestanding kernel skeleton aligned with:

- The Little Book About OS Development
- Intel 64 and IA-32 Architectures SDM Volume 3A

## ORCA OS Build Model

ORCA OS should be built as a three-layer system, not as one large kernel blob.

### Layer 1 - Base OS

- Bootloader path (`GRUB` today, `ORCA-BOOT` later)
- Kernel core
- Drivers for network, storage, sensors, GPU, and edge hardware
- Init/bootstrap path for bringing up system services

This layer must stay minimal, deterministic, and stable.

### Layer 2 - ORCA System Services

- `ORCA-Net`
- `ORCA-Vision`
- `ORCA-Core`
- `ORCA-Security`
- `ORCA-Update`

These services define the ORCA platform and should be isolated from early boot code.

### Layer 3 - Workloads and Control Plane

- Operator control plane
- Mission and autonomy workloads
- Observability and incident-response surfaces

This layer sits on top of the platform and should consume stable service contracts from Layer 2.

## What Is Implemented

- Multiboot header and kernel entry in assembly
- Freestanding C kernel entry (`kernel_main`)
- VGA text output checkpoint proving boot flow
- Platform manifest for the three ORCA OS layers
- Minimal init/service manager for Layer 2 boot sequencing
- Dedicated service modules for `ORCA-Net`, `ORCA-Vision`, `ORCA-Core`, `ORCA-Security`, and `ORCA-Update`
- Layer 1 driver registry with explicit kernel capability flags
- Layer 2 service dependency model based on required drivers and prior service readiness
- Linker script loading kernel at 1 MiB
- GRUB ISO generation when host tooling is available
- QEMU run target
- Dockerized build environment for reproducibility
- Build fallback to a writable temp directory when `build/` is not writable
- Graceful skip of ISO packaging when `grub-mkrescue` or `xorriso` is unavailable

## Current Boot Contracts

Layer 1 exposes a tiny driver registry with capability tokens:

- `net`
- `sto`
- `sns`
- `cry`
- `dsp`

Layer 2 services declare both required driver capabilities and service-to-service dependencies.

Current dependency chain:

- `ORCA-Net` requires network capability
- `ORCA-Vision` requires sensor capability
- `ORCA-Core` waits on `ORCA-Net` and `ORCA-Vision`
- `ORCA-Security` requires crypto + network and waits on `ORCA-Net`
- `ORCA-Update` requires network + storage + crypto and waits on `ORCA-Net` + `ORCA-Security`

Because storage is intentionally marked unavailable in the current driver registry, `ORCA-Update` now defers for a concrete reason instead of returning a fixed stub status.

## Layout

- `src/boot.s`: Multiboot header, stack setup, jump to C
- `src/kernel.c`: Boot checkpoint rendering and text UI
- `src/orca_drivers.c`: Layer 1 driver registry and capability exposure
- `src/orca_drivers.h`: Driver capability types and registry contracts
- `src/orca_init.c`: Minimal init path and service boot sequencing
- `src/orca_init.h`: Init/service contracts and boot status types
- `src/orca_platform.c`: Layer and service descriptors for ORCA OS
- `src/orca_platform.h`: Shared contracts for the platform manifest
- `src/services/`: One module per ORCA system service
- `linker.ld`: Kernel link layout
- `grub/grub.cfg`: GRUB boot config
- `Makefile`: Build, ISO, and run commands
- `Dockerfile.toolchain`: Toolchain container
- `scripts/build-in-docker.sh`: Containerized build entry

## Build and Run (Host Tools Installed)

1. `cd OrcaOs`
2. `make all`
3. `make run`

If ISO tooling is missing, `make all` still produces the kernel binary and prints a skip notice instead of failing.

Use `make show-build-dir` to see whether the build is going to `build/` or a writable temp directory fallback.

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

- `ORCA OS Boot Checkpoint`
- `Multiboot magic validated.`
- The three ORCA OS layers with their first anchored component
- A Layer 1 driver registry with readiness state
- A Layer 2 service table showing stage, required drivers, dependencies, and status

## Next Chapter Checkpoints

- Phase 2: GDT, IDT, ISR, PIC remap, timer IRQ
- Phase 3: Physical memory manager + paging
- Phase 4: Minimal init path that can start ORCA system services
- Phase 5: Stable driver model for ORCA-Net, ORCA-Vision, and ORCA-Security hooks
- Phase 6: User-mode runtime for control-plane and mission workloads
