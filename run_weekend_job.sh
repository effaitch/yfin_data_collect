#!/bin/bash
# Cron job script for Yahoo Finance Data Collection
# This script activates the venv and runs the service
# Logs are saved to the logs directory with timestamps

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run the service
python3 "$SCRIPT_DIR/service.py"

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Exit with the service's exit code
exit $EXIT_CODE
