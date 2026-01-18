# 🔤 Term Extraction Tool v3.6

A bilingual terminology extraction tool that uses AI to extract Chinese-English term pairs from parallel texts. Built with Gradio and powered by the LLM7 API.

[![GitHub](https://img.shields.io/badge/GitHub-digimarketingai-blue?logo=github)](https://github.com/digimarketingai)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://python.org)
[![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange?logo=gradio)](https://gradio.app)

## ✨ Features

- **Bilingual Extraction**: Extract Chinese-English terminology pairs from parallel texts
- **Smart Chunking**: Handles long documents by intelligently splitting and aligning text segments
- **Category Classification**: Automatically categorizes terms (medical, organization, place, social, technical, chemical, date, general)
- **Focus Mode**: Prioritize specific term types during extraction
- **Multiple Export Formats**: Download results as CSV, JSON, TSV, or TBX
- **Free API**: Uses LLM7's free API (optional token for higher limits)

## 🚀 Quick Start

### Option 1: Run Locally

```bash
# Clone the repository
git clone https://github.com/digimarketingai/term-extraction-tool.git
cd term-extraction-tool

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

The application will start and provide a local URL (typically `http://127.0.0.1:7860`).

### Option 2: Run on Google Colab

1. Open [Google Colab](https://colab.research.google.com/)
2. Create a new notebook
3. Run:

```python
!pip install gradio openai -q
```

4. Copy and paste the contents of `app.py` into a new cell
5. Run the cell

## 📖 Usage

1. **Source Text (Required)**: Paste your Chinese source text
2. **Target Text (Optional)**: Paste the English translation for better accuracy
3. **Extraction Focus**: Specify what types of terms to prioritize (e.g., "medical", "social media", "organization")
4. **Filter**: Filter results by category
5. **Max Terms**: Set the maximum number of terms to extract
6. **API Token**: Optional - get a free token at [token.llm7.io](https://token.llm7.io) for higher character limits

### Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| CSV | Comma-separated values | Excel, Google Sheets |
| JSON | Structured data format | Programming, APIs |
| TSV | Tab-separated values | CAT tools (memoQ, Trados) |
| TBX | TermBase eXchange | Translation memory systems |

## 🔧 Configuration

### Character Limits

| Mode | Limit |
|------|-------|
| Without token | 8,000 characters |
| With free token | 20,000 characters |

### Supported Categories

- `medical` - Diseases, symptoms, medical procedures
- `organization` - Government departments, agencies, companies
- `place` - Locations, districts, parks, countries
- `social` - Social media platforms, websites
- `technical` - Equipment, devices, technical procedures
- `chemical` - Chemical compounds, pesticides, ingredients
- `date` - Dates, times, periods
- `general` - Other terminology

