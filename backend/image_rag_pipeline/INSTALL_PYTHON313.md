# Installation Guide for Python 3.13

Python 3.13 is very new, and some packages don't have pre-built wheels yet. Follow these steps:

## Quick Fix (Recommended)

Run these commands in order:

```bash
cd backend/image_rag_pipeline

# 1. Upgrade pip
pip install --upgrade pip

# 2. Install PyMuPDF first (latest version has Python 3.13 wheels)
pip install --upgrade pymupdf

# 3. Install Pillow (newer version has Python 3.13 wheels)
pip install --upgrade Pillow

# 4. Install remaining dependencies
pip install fastapi==0.109.0 uvicorn==0.27.0 python-multipart==0.0.6
pip install qdrant-client==1.7.3
pip install open-clip-torch==2.24.0 torch==2.1.2
pip install python-dotenv==1.0.0
```

## Alternative: Use Python 3.11 or 3.12

If you continue having issues, use Python 3.11 or 3.12:

```bash
# Install Python 3.12 via Homebrew (macOS)
brew install python@3.12

# Create new venv with Python 3.12
python3.12 -m venv venv312
source venv312/bin/activate

# Now install normally
pip install -r requirements.txt
```

## What's Happening?

- **Python 3.13** was released recently (October 2024)
- Older package versions (PyMuPDF 1.23.8, Pillow 10.2.0) don't have pre-built wheels for Python 3.13
- pip tries to build from source, which requires C++ compilers and often fails
- **Solution**: Install latest versions that have Python 3.13 wheels

## Verify Installation

After installation, verify everything works:

```bash
python -c "import fitz; print('PyMuPDF OK')"
python -c "from PIL import Image; print('Pillow OK')"
python -c "import fastapi; print('FastAPI OK')"
```

## If You Still Have Issues

1. **Check Python version**: `python --version` (should be 3.13.x)
2. **Try installing packages one by one** to identify which one fails
3. **Use Python 3.12** as a fallback (most packages have wheels for it)

