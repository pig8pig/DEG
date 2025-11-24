#!/bin/bash
# Helper script to restart the backend with the ASI_API_KEY environment variable

# Check if ASI_API_KEY is set
if [ -z "$ASI_API_KEY" ]; then
    echo "❌ Error: ASI_API_KEY environment variable is not set"
    echo ""
    echo "Please set it first:"
    echo "  export ASI_API_KEY='your_api_key_here'"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✓ ASI_API_KEY is set"
echo "Starting backend server with LLM support..."
echo ""

cd "$(dirname "$0")/backend"
uvicorn main:app --reload --host 127.0.0.1 --port 8000
