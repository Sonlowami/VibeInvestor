#!/bin/bash
# Launch script for VibeInvestor Gradio UI

set -e

echo "🚀 Starting VibeInvestor Gradio Interface..."
echo ""
echo "Prerequisites check:"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 found"

# Check if running from correct directory
if [ ! -f "src/gradio_app.py" ]; then
    echo "❌ Must run from VibeInvestor root directory"
    exit 1
fi
echo "✓ Project structure found"

# Check for required environment variables
if [ -z "$GOOGLE_API_KEY" ]; then
    echo ""
    echo "⚠️  WARNING: GOOGLE_API_KEY environment variable not set"
    echo "   Make sure you have a .env file with your API keys before running"
    echo ""
fi

if [ -z "$SEARCHAPI_KEY" ]; then
    echo "⚠️  WARNING: SEARCHAPI_KEY environment variable not set"
    echo "   Make sure you have a .env file with your API keys before running"
    echo ""
fi

# Install dependencies if needed
echo ""
echo "Checking dependencies..."
python3 -c "import gradio; import plotly" 2>/dev/null || {
    echo "Installing required packages..."
    pip install gradio plotly pandas requests beautifulsoup4 lxml python-dotenv fpdf \
                langchain langchain-community langchain-google-genai langchain-text-splitters \
                faiss-cpu yfinance
}
echo "✓ Dependencies ready"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "        VibeInvestor UI is starting..."
echo "════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Open your browser to: http://localhost:7860"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the app
cd src && python3 gradio_app.py
