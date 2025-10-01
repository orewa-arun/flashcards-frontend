# 🎴 AI-Powered Flashcard Generator

Generate beautiful, LaTeX-formatted flashcards from PDF lecture notes using AI (Google Gemini).

## ✨ Features

- 🤖 **AI-Powered**: Uses Google Gemini to intelligently extract and format content
- 📐 **LaTeX Support**: Beautiful mathematical equations and formulas
- 🎯 **Multiple Formats**: JSON, TXT, CSV, LaTeX, and Anki-compatible exports
- ⚙️ **Highly Configurable**: Easy customization via `.env` file
- 🎨 **Beautiful Output**: Professional LaTeX documents with custom styling
- 📚 **Batch Processing**: Process multiple PDFs at once

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download this repository
cd self-learning-ai

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your-api-key-here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Run

```bash
# Place your PDF files in the ./slides directory
python flashcard_generator_ai.py
```

## 📁 Project Structure

```
self-learning-ai/
├── flashcard_generator_ai.py    # Main application
├── config.py                     # Configuration management
├── latex_config.py               # LaTeX templates and settings
├── .env                          # Your configuration (don't commit!)
├── .env.example                  # Example configuration
├── requirements.txt              # Python dependencies
├── slides/                       # Input PDFs go here
├── prompts/                      # AI prompt templates
│   ├── flashcard_generation_prompt.txt
│   └── content_analysis_prompt.txt
└── flashcards_output/            # Generated flashcards
    ├── *_flashcards.json
    ├── *_flashcards.txt
    ├── *_flashcards.tex
    ├── *_anki.txt
    └── *_simple.csv
```

## ⚙️ Configuration Options

Edit `.env` to customize:

### API Settings
- `GEMINI_API_KEY` - Your Google Gemini API key (required)
- `GEMINI_MODEL` - AI model to use (default: gemini-2.0-flash-exp)

### Directories
- `INPUT_DIR` - Where to find PDF files (default: ./slides)
- `OUTPUT_DIR` - Where to save flashcards (default: ./flashcards_output)
- `PROMPTS_DIR` - Where prompt templates are stored (default: ./prompts)

### Processing
- `MAX_CHUNK_SIZE` - Maximum text chunk size (default: 4000 chars)

### Output Formats
- `GENERATE_JSON` - Generate JSON files (default: true)
- `GENERATE_TXT` - Generate text files (default: true)
- `GENERATE_CSV` - Generate CSV files (default: true)
- `GENERATE_TEX` - Generate LaTeX files (default: true)
- `GENERATE_ANKI` - Generate Anki files (default: true)

### LaTeX Settings
- `LATEX_ENABLED` - Enable LaTeX generation (default: true)
- `LATEX_COMPILE_COMMAND` - LaTeX compiler (default: pdflatex)

## 🎨 Customization

### Modify AI Prompts

Edit files in `prompts/` directory:
- `flashcard_generation_prompt.txt` - Main flashcard generation
- `content_analysis_prompt.txt` - Content analysis

### Modify LaTeX Styling

Edit `latex_config.py` to change:
- Document class and options
- Colors and themes
- Package imports
- Flashcard box styling

## 📐 Compiling LaTeX

To generate PDF from LaTeX files:

```bash
cd flashcards_output
pdflatex "lecture_name_flashcards.tex"
```

Requirements:
- LaTeX distribution (TeXLive, MiKTeX, or MacTeX)
- `tcolorbox` package (usually included)

## 🃏 Importing to Anki

1. Open Anki
2. Go to File → Import
3. Select the `*_anki.txt` file
4. Configure import settings:
   - Field separator: ` | `
   - Allow HTML in fields
5. Import!

Math formulas will render automatically in Anki.

## 🔧 Troubleshooting

### API Key Issues
```
Error: GEMINI_API_KEY is not set
```
**Solution**: Make sure you've created `.env` file with your API key.

### PDF Extraction Issues
```
Error: No text could be extracted from PDF
```
**Solution**: PDF might be scanned images. Try using OCR or a different PDF.

### LaTeX Compilation Errors
```
Error: Package tcolorbox not found
```
**Solution**: Install full LaTeX distribution with all packages.

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 🙏 Credits

- Google Gemini API for AI capabilities
- PyPDF2 for PDF processing
- LaTeX and tcolorbox for beautiful documents

