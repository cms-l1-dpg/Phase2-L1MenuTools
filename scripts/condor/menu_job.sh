#!/bin/bash
# HTCondor job wrapper for the menu tools: cd to a checkout (clone or worktree), source the
# hlt-extension environment (LCG_109, thread caps, venv pyarrow, PYTHONPATH=checkout,
# MENU_TOOLS_CACHE) and run the given command there.
#   menu_job.sh <checkout dir> <command> [args...]
CHECKOUT="$1"; shift
cd "$CHECKOUT"
# before set -u: the LCG setup script uses unset variables
source /eos/home-a/alobanov/SWAN_projects/L1TML/topo-hackathon-2026/projects/hlt-extension/env.sh
set -euo pipefail
echo "$(date) on $(hostname) in $PWD (git $(git rev-parse --short HEAD 2>/dev/null || echo ?)): $*"
echo "MENU_TOOLS_CACHE=$MENU_TOOLS_CACHE"
"$@"
echo "$(date) done"
