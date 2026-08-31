#!/bin/bash
# Quick test script to verify FastAPI server is working

echo "🚀 Starting FastAPI server..."
cd "$(dirname "$0")"

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Installing dependencies first..."
    pip install -r requirements.txt
fi

# Start server
echo "Starting server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
python main.py
