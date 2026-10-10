#!/bin/bash
# Seed a one-file workspace: a dates.py with nothing in it yet.
set -euo pipefail
printf '"""Date helpers."""\n' > dates.py
