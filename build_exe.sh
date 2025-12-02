#!/bin/bash

echo "🚀 Building Sendora executable for Linux..."
echo "============================================"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

echo ""
echo "🔨 Building executable..."

# Build the executable
pyinstaller \
  --onefile \
  --windowed \
  --name "Sendora" \
  --icon=auto.ico \
  --add-data "platforms:platforms" \
  --add-data "utils:utils" \
  --hidden-import selenium \
  --hidden-import pandas \
  --hidden-import ppadb.client \
  --hidden-import webdriver_manager \
  --clean \
  --noconfirm \
  app.py

echo ""
echo "✅ BUILD COMPLETE!"
echo "📁 Find Sendora executable in 'dist' folder"
echo ""
echo "To run: ./dist/Sendora"
