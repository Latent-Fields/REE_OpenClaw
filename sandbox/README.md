# Sandboxed Testing Environment

This directory provides a containerized environment for running REE_OpenClaw tests in isolation from the host workspace.

## Run

```bash
docker build -f sandbox/Dockerfile -t ree-openclaw-sandbox .
docker run --rm ree-openclaw-sandbox
```

## Purpose

- Keep safety probes reproducible.
- Avoid accidental host mutations while testing tool execution paths.
- Create a clear baseline for CI and external reproduction.

