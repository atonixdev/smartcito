# Orca Domain Groups

This folder adds a grouping layer above the repository roots so contributors
can find all air, robotics, vision, sensor, platform, and AI surfaces from one
place.

Some Python roots now also have physical parent folders on disk:

- drone and surveillance packages live under `air/`
- camera services live under `vision/`
- robotics packages live under `robotics/`
- GPS services live under `sensors/`
- the security domain package lives under `services/`
- the GPU intelligence package lives under `ai/`
- the hardware domain package lives under `edge/`

Old import paths remain available through compatibility shims while callers are
updated.

Each domain folder ships a `manifest.json` file that lists the owned paths and a
short explanation of what belongs there.