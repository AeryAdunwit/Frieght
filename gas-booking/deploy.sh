#!/bin/bash
# Auto-push and deploy GAS project
# Usage: ./deploy.sh [description]

cd "$(dirname "$0")"

# Active deployment used for LINE webhook and production web app
ACTIVE_DEPLOY_ID="AKfycbyUzhb2Yo1_dWM3VgaSOVc1OGDlMvGMkQQuqB7QrcwnY-ci4d3yIC-lgCRZvPkeyGOahg"

echo "=== Pushing code to GAS ==="
clasp push --force

if [ $? -ne 0 ]; then
    echo "Push failed. Aborting."
    exit 1
fi

echo "Updating deployment: $ACTIVE_DEPLOY_ID"
clasp deploy -i "$ACTIVE_DEPLOY_ID" -d "${1:-Auto deployed $(date +%Y-%m-%d_%H:%M)}"

echo "=== Done ==="
