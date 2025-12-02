#!/bin/bash
# Quick Build Script - Creates executable with debugging enabled

echo "🔧 DEBUG BUILD - Building with console output..."
echo "================================================"

pyinstaller \
  --onefile \
  --console \
  --name "Sendora-Debug" \
  --icon=auto.ico \
  --add-data "platforms:platforms" \
  --add-data "utils:utils" \
  --clean \
  app.py

echo ""
echo "✅ Debug build complete!"
echo "📁 Run: ./dist/Sendora-Debug"
echo "💡 This version shows console output for debugging"
