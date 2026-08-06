#!/bin/bash
cd "$(dirname "$0")"
exec bash scripts/setup_local.sh "$@"
