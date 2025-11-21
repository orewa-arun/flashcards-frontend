#!/bin/bash
# Railway build script for image_rag_pipeline
# This installs PyTorch CPU-only version first to reduce memory usage

set -e

echo "🔧 Installing PyTorch CPU-only version (smaller footprint)..."
pip install --no-cache-dir torch==2.6.0+cpu torchvision==0.21.0+cpu --index-url https://download.pytorch.org/whl/cpu

echo "📦 Installing remaining dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "✅ Build complete!"

