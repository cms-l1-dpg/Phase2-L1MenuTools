#!/bin/bash
# First-time environment setup for Phase2-L1MenuTools.
#
# Creates the venv `pyenv/` in the repository root (as expected by setup.sh),
# installs menu_tools into it in editable mode, and makes the venv's activate
# script put a complete TeX Live (from cvmfs) on PATH for rate_table_tex.
# Safe to re-run: an existing pyenv/ is reused and the TeX block is added once.
#
# Usage, from anywhere:   scripts/setup_pyenv.sh
#        other Python:    PYTHON=/path/to/python3.11 scripts/setup_pyenv.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PYTHON=${PYTHON:-python3.11}

if [ ! -d pyenv ]; then
    echo "Creating pyenv/ with $PYTHON"
    "$PYTHON" -m venv pyenv
else
    echo "Reusing existing pyenv/"
fi

# shellcheck disable=SC1091
source pyenv/bin/activate
pip install -e .

if ! grep -q "TEXLIVE_CVMFS" pyenv/bin/activate; then
    cat >> pyenv/bin/activate <<'EOF'

# Complete TeX Live for rate_table_tex (the lxplus system TeX Live lacks adjustbox).
# Added after the venv saved _OLD_VIRTUAL_PATH, so `deactivate` removes it again.
TEXLIVE_CVMFS=/cvmfs/cms.cern.ch/external/tex/texlive/2017/bin/x86_64-linux
if [ -d "$TEXLIVE_CVMFS" ]; then
    case ":$PATH:" in
        *":$TEXLIVE_CVMFS:"*) ;;
        *) export PATH="$TEXLIVE_CVMFS:$PATH" ;;
    esac
fi
EOF
    echo "Added the cvmfs TeX Live to pyenv/bin/activate"
fi

echo
echo "Done. Activate with:  source setup.sh   (or: source pyenv/bin/activate)"
