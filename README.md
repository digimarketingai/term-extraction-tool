# 🔤 Term Extraction Tool v3.7

A bilingual terminology extraction tool that uses AI to extract Chinese-English term pairs from parallel texts. Built with Gradio and powered by the LLM7 API.

**🆕 NEW in v3.7: Custom Command Mode** - Enter natural language instructions to extract exactly what you need!

[[GitHub](https://img.shields.io/badge/GitHub-digimarketingai-blue?logo=github)](https://github.com/digimarketingai)
[[Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](https://python.org)
[[Gradio](https://img.shields.io/badge/Gradio-4.0+-orange?logo=gradio)](https://gradio.app)
[[License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

- **🎯 Custom Command Mode** (NEW!) - Enter natural language instructions like "Extract only person names" or "只提取機構名稱"
- **Bilingual Extraction**: Extract Chinese-English terminology pairs from parallel texts
- **Smart Chunking**: Handles long documents by intelligently splitting and aligning text segments
- **Category Classification**: Automatically categorizes terms (medical, organization, place, social, technical, chemical, date, general)
- **Focus Mode**: Prioritize specific term types during extraction
- **Multiple Export Formats**: Download results as CSV, JSON, TSV, or TBX
- **Free API**: Uses LLM7's free API (optional token for higher limits)

## 🆕 Custom Command Mode (v3.7)

The biggest update in v3.7! Instead of using predefined extraction rules, you can now enter natural language commands to extract exactly what you need.

### How to Use Custom Commands

1. Set **Filter** to `all`
2. Enter your command in the **Focus** field
3. Click **Extract**

### Example Commands

| English | 繁體中文 |
|---------|----------|
| `Extract only person names and job titles` | `只提取人名和職稱` |
| `Find all organization names` | `找出所有機構名稱` |
| `Get only dates and time expressions` | `只要日期和時間相關的詞彙` |
| `Extract medical terms related to dengue fever` | `提取與登革熱相關的醫學術語` |
| `List all social media accounts mentioned` | `列出所有提到的社群媒體帳號` |
| `Find chemical compound names only` | `只找化學化合物名稱` |

The AI will follow your instruction directly instead of using predefined extraction rules.

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
```

The app will launch and provide a local URL (typically `http://127.0.0.1:7860`) plus a public share link.

### Option 2: Run on Google Colab

1. Open [Google Colab](https://colab.research.google.com/)
2. Create a new notebook
3. Run:

```python
!pip install gradio openai -q
```

4. Copy and paste the contents of `app.py` into a new cell
5. Run the cell
6. Click the public Gradio link to access the interface

## 📖 Usage Guide

### Basic Usage

1. **Source Text (Required)**: Paste your Chinese source text
2. **Target Text (Optional)**: Paste the English translation for better accuracy
3. **Focus / Custom Command**: 
   - **Keywords**: `medical`, `social media`, `organization`, `place`, `date`
   - **Custom commands**: Full sentences like `Extract only person names`
4. **Filter**: 
   - Set to `all` for maximum extraction or custom commands
   - Set to specific category to filter results
5. **Max Terms**: Set the maximum number of terms to extract (20-300)
6. **API Token**: Optional - get a free token at [token.llm7.io](https://token.llm7.io) for higher limits

### Standard Mode vs Custom Command Mode

| Feature | Standard Mode | Custom Command Mode |
|---------|---------------|---------------------|
| **Trigger** | Simple keywords in Focus | Sentence-like commands in Focus + Filter = `all` |
| **Behavior** | Extracts all terms, prioritizes focus area | Follows your instruction exactly |
| **Example** | `medical` | `Extract only disease names and symptoms` |
| **Best for** | General extraction | Specific extraction needs |

### Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **CSV** | Comma-separated values with BOM | Excel, Google Sheets |
| **JSON** | Structured data format | Programming, APIs |
| **TSV** | Tab-separated values | CAT tools (memoQ, Trados, Memsource) |
| **TBX** | TermBase eXchange (XML) | Translation memory systems |

## 🔧 Configuration

### Character Limits

| Mode | Character Limit |
|------|-----------------|
| Without token | 8,000 characters |
| With free token | 20,000 characters |

Get your free token at [token.llm7.io](https://token.llm7.io)

### Supported Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `medical` | Health-related terms | Diseases, symptoms, procedures, body parts |
| `organization` | Institutional names | Government departments, agencies, companies, NGOs |
| `place` | Geographic locations | Districts, cities, parks, countries, addresses |
| `social` | Online platforms | Social media accounts, websites, apps |
| `technical` | Technical terminology | Equipment, devices, procedures, specifications |
| `chemical` | Chemical substances | Compounds, pesticides, ingredients, formulas |
| `date` | Temporal expressions | Dates, times, periods, seasons |
| `name` | Personal names | People, titles, positions |
| `general` | Other terminology | Miscellaneous terms |

## 📋 Requirements

```
gradio>=4.0.0
openai>=1.0.0
```

## 🛠️ API Information

This tool uses the [LLM7 API](https://api.llm7.io/v1) which provides:
- Free access to GPT-4.1-nano model
- OpenAI-compatible endpoints (`/models`, `/chat/completions`)
- Optional token authentication for higher rate limits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Gradio](https://gradio.app/) - For the amazing UI framework
- [LLM7](https://api.llm7.io/) - For providing free API access
- [OpenAI](https://openai.com/) - For the underlying language model

## 📬 Contact

**digimarketingai** - [GitHub Profile](https://github.com/digimarketingai)

Project Link: [https://github.com/digimarketingai/term-extraction-tool](https://github.com/digimarketingai/term-extraction-tool)

---

<p align="center">
  Made with ❤️ for translators and localization professionals
</p>
