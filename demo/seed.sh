#!/usr/bin/env bash
# ==============================================================================
# Seed script for Atelier Demo & Calibration Benchmark Dataset
# Usage: ./demo/seed.sh
# ==============================================================================
set -euo pipefail

echo "🎨 Seeding Atelier Calibration Dataset and Golden Cases..."

# Ensure Python virtual environment
if [ -d "atelier-agent/.venv" ]; then
    PYTHON_BIN="atelier-agent/.venv/Scripts/python"
    if [ ! -f "$PYTHON_BIN" ]; then
        PYTHON_BIN="atelier-agent/.venv/bin/python"
    fi
else
    PYTHON_BIN="python"
fi

# 1. Generate calibration drawings with deliberate errors
echo "📐 Generating calibration benchmark drawings (0° - 9° error)..."
$PYTHON_BIN demo/generate_calibration_dataset.py

echo "✅ Calibration drawings generated in demo/dataset/:"
ls -lh demo/dataset/

echo "🎉 Demo seed complete! Run 'dotnet run --project Atelier.Web' to explore in studio."
