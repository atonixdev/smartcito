# Orca CLI

The repository now carries a first-class CLI package in `cli/orca_cli/`.

The root `./orca` entrypoint remains the stable launcher, but the package form
lets contributors extend the CLI without keeping all command logic in a single
root script.

Current command families:

- AI and dataset workflows: `ingest`, `train`, `deploy`, `dataset ...`
- API-backed operational queries and writes: `api health`, `api control-plane`, `api fleet`, `api cameras`
- Workspace inspection: `workspace domains`, `workspace templates`, `workspace template <name>`, `workspace template-write <name> --output path.json`, `workspace template-write-all --output-dir dir/`

Write-oriented helpers accept JSON payload files so operators can call the API
without writing ad-hoc curl commands.

## Installed Usage

After installing from the repository root:

```bash
python3 -m pip install .
```

the `orca` command is available directly:

```bash
orca --help
orca workspace templates
orca workspace template-write-all --output-dir ./orca-templates
```

If you also want the lightweight FastAPI service dependencies used by the moved
service roots, install with:

```bash
python3 -m pip install ".[services]"
```