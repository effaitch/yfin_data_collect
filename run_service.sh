#!/bin/bash
# Simple script to run the data collection service
# Usage: ./run_service.sh

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Validate configuration first
echo "Validating configuration..."
python3 validate_config.py

# Run the service
echo ""
echo "Starting data collection service..."
echo "=========================================="
python3 service.py

