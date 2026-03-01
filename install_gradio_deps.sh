#!/bin/bash
# Install dependencies for VibeInvestor Gradio UI
# Compatible with Python 3.10+

set -e

echo "════════════════════════════════════════════════════════════"
echo "  VibeInvestor Gradio UI - Dependency Installation"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Detected Python $PYTHON_VERSION"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements-gradio.txt" ]; then
    echo "❌ Error: requirements-gradio.txt not found"
    echo "   Please run this script from the VibeInvestor root directory"
    exit 1
fi

echo "Installing Gradio UI dependencies..."
echo "(This may take a few minutes)"
echo ""

pip install -r requirements-gradio.txt

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Dependencies installed successfully!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "To verify installation:"
echo "  python3 check_deps.py"
echo ""
echo "To start the Gradio UI:"
echo "  cd src && python3 gradio_app.py"
echo ""
echo "Then open: http://localhost:7860"
echo ""
