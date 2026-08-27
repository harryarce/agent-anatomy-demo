#!/usr/bin/env bash
set -euo pipefail

# Honest command script for toolbox setup; this does not fabricate SDK calls.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Creating baseline toolbox from toolbox.before.yaml"
azd ai toolbox create anatomy-toolbox --from-file ./toolbox.before.yaml

echo "Listing current toolbox config"
cat ./toolbox.before.yaml

echo "Applying add-tool version from toolbox.add-tool.yaml"
azd ai toolbox create anatomy-toolbox --from-file ./toolbox.add-tool.yaml

echo "Toolbox setup complete"