#!/usr/bin/env bash
set -euo pipefail

docker build -f sandbox/Dockerfile -t ree-openclaw-sandbox .
docker run --rm ree-openclaw-sandbox

