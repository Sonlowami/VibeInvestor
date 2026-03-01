#!/usr/bin/env python3
"""
Dependency checker for VibeInvestor Gradio UI
Tests that all required packages are installed and importable
"""

import sys

def check_module(module_name, package_name=None):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✓ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"✗ {package_name or module_name}: {e}")
        return False

print("Checking VibeInvestor Dependencies...\n")

# Core dependencies
core_deps = [
    ("gradio", "gradio"),
    ("plotly", "plotly"),
    ("pandas", "pandas"),
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
    ("lxml", "lxml"),
    ("dotenv", "python-dotenv"),
    ("fpdf", "fpdf"),
]

print("Core Dependencies:")
core_ok = all(check_module(mod, pkg) for mod, pkg in core_deps)

# Langchain dependencies
print("\nLangchain Dependencies:")
langchain_deps = [
    ("langchain", "langchain"),
    ("langchain_community", "langchain-community"),
    ("langchain_google_genai", "langchain-google-genai"),
    ("langchain_text_splitters", "langchain-text-splitters"),
]
langchain_ok = all(check_module(mod, pkg) for mod, pkg in langchain_deps)

# Data dependencies
print("\nData Dependencies:")
data_deps = [
    ("faiss", "faiss-cpu"),
    ("yfinance", "yfinance"),
]
data_ok = all(check_module(mod, pkg) for mod, pkg in data_deps)

# Built-in modules
print("\nBuilt-in Modules:")
builtin_deps = ["asyncio", "json", "os", "datetime", "re", "typing"]
builtin_ok = all(check_module(mod) for mod in builtin_deps)

print("\n" + "="*60)
if core_ok and langchain_ok and data_ok and builtin_ok:
    print("✅ All dependencies installed successfully!")
    print("\nTo start the Gradio UI:")
    print("  cd src && python3 gradio_app.py")
    print("\nThen open: http://localhost:7860")
    sys.exit(0)
else:
    print("❌ Some dependencies are missing.")
    print("\nTo install missing packages:")
    print("  pip install gradio plotly pandas requests beautifulsoup4 lxml \\")
    print("              python-dotenv fpdf langchain langchain-community \\")
    print("              langchain-google-genai langchain-text-splitters \\")
    print("              faiss-cpu yfinance")
    sys.exit(1)
