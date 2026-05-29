Param(
    [Parameter(Position=0)]
    [ValidateSet("build", "run", "docker-build", "container-build", "clean")]
    [string]$Command = "docker-build"
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OrcaOsDir = Join-Path $RootDir "OrcaOs"

function Resolve-ContainerRuntime {
    param([string]$ConfiguredRuntime)

    if ($ConfiguredRuntime) {
        if (Get-Command $ConfiguredRuntime -ErrorAction SilentlyContinue) {
            return $ConfiguredRuntime
        }
        throw "Configured CONTAINER_RUNTIME '$ConfiguredRuntime' was not found in PATH."
    }

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        return "docker"
    }

    if (Get-Command podman -ErrorAction SilentlyContinue) {
        return "podman"
    }

    throw "No container runtime found. Install Docker Desktop or Podman, or set CONTAINER_RUNTIME."
}

function Run-ContainerBuild {
    $runtime = Resolve-ContainerRuntime $env:CONTAINER_RUNTIME
    $imageTag = "orcos-toolchain:latest"

    Push-Location $OrcaOsDir
    try {
        & $runtime build -t $imageTag -f Dockerfile.toolchain .
        if ($LASTEXITCODE -ne 0) {
            throw "Container build failed."
        }

        $mountArg = "${OrcaOsDir}:/workspace"
        & $runtime run --rm -v $mountArg -w /workspace $imageTag make all
        if ($LASTEXITCODE -ne 0) {
            throw "Kernel compile failed in container."
        }
    }
    finally {
        Pop-Location
    }
}

switch ($Command) {
    "build" {
        Push-Location $OrcaOsDir
        try {
            & make all
            if ($LASTEXITCODE -ne 0) { throw "Host build failed." }
        }
        finally {
            Pop-Location
        }
    }
    "run" {
        Push-Location $OrcaOsDir
        try {
            & make run
            if ($LASTEXITCODE -ne 0) { throw "QEMU run failed." }
        }
        finally {
            Pop-Location
        }
    }
    "docker-build" { Run-ContainerBuild }
    "container-build" { Run-ContainerBuild }
    "clean" {
        Push-Location $OrcaOsDir
        try {
            & make clean
            if ($LASTEXITCODE -ne 0) { throw "Clean failed." }
        }
        finally {
            Pop-Location
        }
    }
}
