# Installation Troubleshooting Guide

## PyMuPDF Installation Issues on Python 3.13

If you encounter build errors when installing PyMuPDF on Python 3.13, try these solutions:

### Solution 1: Install Latest PyMuPDF (Recommended)

```bash
# Upgrade pip first
pip install --upgrade pip

# Install latest PyMuPDF (has Python 3.13 wheels)
pip install --upgrade pymupdf

# Then install other requirements
pip install -r requirements.txt --no-deps
pip install fastapi uvicorn python-multipart qdrant-client pillow open-clip-torch torch python-dotenv
```

### Solution 2: Install PyMuPDF Separately

```bash
# Install PyMuPDF first (latest version)
pip install pymupdf

# Then install remaining dependencies
pip install fastapi==0.109.0 uvicorn==0.27.0 python-multipart==0.0.6
pip install qdrant-client==1.7.3
pip install Pillow==10.2.0 open-clip-torch==2.24.0 torch==2.1.2
pip install python-dotenv==1.0.0
```

### Solution 3: Use Python 3.11 or 3.12 (If Available)

PyMuPDF has better support for Python 3.11 and 3.12:

```bash
# Create venv with Python 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Solution 4: Install System Dependencies (macOS)

If building from source, you may need:

```bash
# Install Xcode command line tools
xcode-select --install

# Install cmake (if needed)
brew install cmake
```

### Solution 5: Use Pre-built Wheel (If Available)

```bash
# Try installing from wheel
pip install --only-binary :all: pymupdf
```

## Verify Installation

After installation, verify PyMuPDF works:

```python
python -c "import fitz; print(fitz.__doc__)"
```

## Alternative: Use pdfplumber (If PyMuPDF Still Fails)

If PyMuPDF continues to fail, you can modify the extractor to use pdfplumber:

```bash
pip install pdfplumber
```

Then update `app/ingestion/extractor.py` to use pdfplumber instead of PyMuPDF.

## Common Error Messages

### "metadata-generation-failed"
- **Cause**: PyMuPDF trying to build from source
- **Solution**: Install latest version with pre-built wheels (Solution 1)

### "c++ compilation failed"
- **Cause**: Missing build tools or incompatible compiler
- **Solution**: Use Python 3.11/3.12 or install latest PyMuPDF with wheels

### "No module named 'fitz'"
- **Cause**: PyMuPDF not installed correctly
- **Solution**: Reinstall using Solution 1 or 2

## Still Having Issues?

1. Check Python version: `python --version` (should be 3.8-3.13)
2. Check pip version: `pip --version` (upgrade if needed)
3. Try clean install:
   ```bash
   pip uninstall pymupdf -y
   pip cache purge
   pip install pymupdf --no-cache-dir
   ```

