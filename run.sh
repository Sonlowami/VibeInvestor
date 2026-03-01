#!/bin/bash
# Quick startup script for VibeInvestor Gradio UI

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project directory
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Please create .env with your API keys:"
    echo ""
    echo "   GOOGLE_API_KEY=your_key_here"
    echo "   SEARCHAPI_KEY=your_key_here"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🚀 VibeInvestor Gradio UI"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Starting server..."
echo ""

# Run the app from the project root
python3 src/gradio_app.py
