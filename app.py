# Term Extraction Tool v3.7
# Bilingual Terminology Extractor with Gradio Interface
# Enhanced: Custom Prompt Mode - Follow user commands directly!
# Repository: https://github.com/digimarketingai

import gradio as gr
import openai
import json
import re
import time

def get_client(token=""):
    return openai.OpenAI(
        base_url="https://api.llm7.io/v1",
        api_key=token if token.strip() else "unused",
    )

MAX_CHARS = 20000
CHUNK_SIZE = 1500

def smart_chunk(text, size=1500):
    if not text or len(text) <= size:
        return [text] if text else []
    
    chunks = []
    paragraphs = re.split(r'\n\s*\n', text)
    current = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= size:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = para + "\n\n" if len(para) <= size else para[:size]
    
    if current:
        chunks.append(current.strip())
    
    return chunks if chunks else [text[:size]]

def align_chunks(source_chunks, target_chunks):
    if not target_chunks:
        return [(s, "") for s in source_chunks]
    
    if len(source_chunks) == len(target_chunks):
        return list(zip(source_chunks, target_chunks))
    
    full_target = "\n\n".join(target_chunks)
    target_len = len(full_target)
    source_lengths = [len(s) for s in source_chunks]
    total_source = sum(source_lengths)
    
    aligned = []
    pos = 0
    for i, src in enumerate(source_chunks):
        ratio = source_lengths[i] / total_source
        chunk_len = int(ratio * target_len)
        end_pos = min(pos + chunk_len, target_len)
        
        if end_pos < target_len:
            boundary = full_target.rfind('\n', pos, end_pos + 200)
            if boundary > pos:
                end_pos = boundary
        
        aligned.append((src, full_target[pos:end_pos].strip()))
        pos = end_pos
    
    return aligned

def parse_terms(content):
    terms = []
    
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r'^```\w*\n?', '', content)
        content = re.sub(r'\n?```$', '', content)
    
    try:
        match = re.search(r'\[[\s\S]*\]', content)
        if match:
            data = json.loads(match.group())
            for item in data:
                if isinstance(item, dict) and item.get('source'):
                    src = str(item.get('source', '')).strip()
                    tgt = str(item.get('target', item.get('translation', ''))).strip()
                    cat = str(item.get('category', 'general')).strip().lower()
                    
                    if src == tgt and re.match(r'^[A-Za-z\s]+$', src):
                        continue
                    if any(x in src.lower() for x in ['extract', 'priority', 'category', 'include', 'skip', 'rules']):
                        continue
                    
                    if src and len(src) >= 2:
                        terms.append({'source': src, 'target': tgt, 'category': cat})
            return terms
    except:
        pass
    
    for obj_str in re.findall(r'\{[^{}]+\}', content):
        try:
            obj = json.loads(obj_str)
            if obj.get('source'):
                src = str(obj.get('source', '')).strip()
                tgt = str(obj.get('target', '')).strip()
                
                if src == tgt and re.match(r'^[A-Za-z\s]+$', src):
                    continue
                    
                terms.append({
                    'source': src,
                    'target': tgt,
                    'category': str(obj.get('category', 'general')).strip().lower()
                })
        except:
            pass
    
    return terms

def is_custom_command(focus_text):
    """
    Detect if the focus field contains a custom command/prompt.
    Returns True if user wants to use custom extraction logic.
    """
    if not focus_text or not focus_text.strip():
        return False
    
    focus_lower = focus_text.lower().strip()
    
    # Command indicators - words that suggest a custom instruction
    command_indicators = [
        # English command words
        'extract', 'find', 'get', 'list', 'identify', 'locate', 'search',
        'only', 'just', 'specifically', 'exclusively',
        'please', 'i want', 'i need', 'give me', 'show me',
        'focus on', 'look for', 'pull out', 'pick out',
        'include', 'exclude', 'ignore', 'skip',
        'all', 'every', 'any', 'must', 'should',
        # Chinese command words
        '提取', '找', '找出', '列出', '識別', '搜尋', '搜索',
        '只要', '僅', '專門', '特別',
        '請', '我要', '我需要', '給我', '顯示',
        '專注', '尋找', '挑出',
        '包含', '排除', '忽略', '跳過',
        '所有', '每個', '任何', '必須', '應該',
        # Pattern indicators
        'term', 'terms', 'word', 'words', 'phrase', 'phrases',
        'name', 'names', 'entity', 'entities',
        '術語', '詞', '詞彙', '名稱', '實體',
    ]
    
    # Check for command indicators
    for indicator in command_indicators:
        if indicator in focus_lower:
            return True
    
    # Check for sentence-like structure (has verb-like patterns)
    # If it's longer than typical keywords and has spaces, likely a command
    if len(focus_text.strip()) > 20 and ' ' in focus_text:
        return True
    
    # Check for punctuation that suggests a sentence/command
    if any(p in focus_text for p in ['。', '，', '.', ',', '!', '！', '?', '？']):
        return True
    
    return False

def get_focus_instruction(focus):
    """Get predefined focus instruction for simple keywords."""
    if not focus or not focus.strip():
        return ""
    
    focus_lower = focus.lower().strip()
    
    focus_map = {
        "social media": "Pay special attention to social media platforms, Facebook pages, Instagram accounts, YouTube channels, websites.",
        "medical": "Pay special attention to diseases, symptoms, medical procedures, health terms.",
        "organization": "Pay special attention to government departments, agencies, official bodies.",
        "place": "Pay special attention to locations, districts, trails, parks, countries.",
        "technical": "Pay special attention to equipment, devices, machinery, technical procedures.",
        "chemical": "Pay special attention to chemical compounds, pesticides, larvicides, active ingredients.",
        "date": "Pay special attention to dates, times, years, months, days, periods."
    }
    
    for key, instruction in focus_map.items():
        if key in focus_lower:
            return instruction
    
    return f"Pay special attention to terms related to: {focus}"

def extract_chunk_custom(source, target, custom_prompt, client):
    """
    Extract terms using custom user prompt - follows user instructions directly!
    """
    if target:
        max_target = min(len(target), 3000 - len(source))
        target_truncated = target[:max_target]
        
        prompt = f"""You are a bilingual terminology extractor. Follow the user's specific instructions.

<source_text>
{source}
</source_text>

<target_text>
{target_truncated}
</target_text>

USER INSTRUCTION: {custom_prompt}

Based on the user's instruction above, extract the requested terms from the texts.
Output ONLY a JSON array in this format:
[{{"source":"來源術語","target":"target term","category":"type"}}]

Important:
- Follow the user's instruction precisely
- If user asks for specific types of terms, only extract those
- Match source terms with their translations from the target text
- Use appropriate categories: medical, organization, place, social, technical, chemical, date, name, general"""

    else:
        prompt = f"""You are a bilingual terminology extractor. Follow the user's specific instructions.

<text>
{source}
</text>

USER INSTRUCTION: {custom_prompt}

Based on the user's instruction above, extract the requested terms from the text.
Output ONLY a JSON array in this format:
[{{"source":"來源術語","target":"English translation","category":"type"}}]

Important:
- Follow the user's instruction precisely
- If user asks for specific types of terms, only extract those
- Provide accurate translations for extracted terms
- Use appropriate categories: medical, organization, place, social, technical, chemical, date, name, general"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": "You are a precise terminology extractor. Follow user instructions exactly. Output only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2500,
        )
        
        content = resp.choices[0].message.content.strip()
        terms = parse_terms(content)
        return terms, content
        
    except Exception as e:
        return [], str(e)

def extract_chunk(source, target, focus, term_filter, client):
    """Standard extraction with predefined logic."""
    focus_instruction = get_focus_instruction(focus)
    extract_all = (term_filter == "all")
    
    term_target = "40-60" if extract_all else "25-40"
    
    if target:
        max_target = min(len(target), 3000 - len(source))
        target_truncated = target[:max_target]
        
        prompt = f"""You are a bilingual terminology extractor. Extract Chinese-English term pairs from the parallel texts below.

<source_chinese>
{source}
</source_chinese>

<target_english>
{target_truncated}
</target_english>

Instructions:
- Extract {term_target} terminology pairs
- Match Chinese terms with their English translations from the texts
- Include: proper nouns, technical terms, organizations, places, dates/times, chemicals, medical terms
- {focus_instruction if focus_instruction else "Extract all types of terminology"}
- Use categories: medical, organization, place, social, technical, chemical, date, general

Output ONLY a JSON array like this:
[{{"source":"中文術語","target":"English term","category":"type"}}]"""

    else:
        prompt = f"""You are a bilingual terminology extractor. Extract key Chinese terms with English translations from the text below.

<chinese_text>
{source}
</chinese_text>

Instructions:
- Extract {term_target} terms with accurate English translations
- Include: proper nouns, technical terms, organizations, places, dates/times, chemicals, medical terms
- {focus_instruction if focus_instruction else "Extract all types of terminology"}
- Use categories: medical, organization, place, social, technical, chemical, date, general

Output ONLY a JSON array like this:
[{{"source":"中文術語","target":"English term","category":"type"}}]"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": "You extract terminology from texts. Output only valid JSON arrays. Never include instruction text in your output."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2500,
        )
        
        content = resp.choices[0].message.content.strip()
        terms = parse_terms(content)
        return terms, content
        
    except Exception as e:
        return [], str(e)

def dedupe(terms):
    seen = {}
    for t in terms:
        key = t['source'].lower()
        if key not in seen:
            seen[key] = t
        elif len(t['target']) > len(seen[key]['target']):
            seen[key] = t
    return list(seen.values())

def validate_terms(terms):
    valid = []
    
    garbage_patterns = [
        r'^[A-Za-z\s]{2,}$',
        r'extract|priority|category|include|skip|rules|instructions',
        r'^[\d\.\s]+$',
    ]
    
    for t in terms:
        src = t['source'].strip()
        tgt = t['target'].strip()
        
        if not src or not tgt:
            continue
        
        if src.lower() == tgt.lower() and re.match(r'^[A-Za-z0-9\s\-]+$', src):
            if len(src) <= 6 or src.upper() == src:
                pass
            else:
                continue
        
        if any(re.search(p, src.lower()) for p in garbage_patterns[1:2]):
            continue
        
        if re.match(r'^[A-Za-z\s]{10,}$', src):
            continue
            
        valid.append(t)
    
    return valid

def apply_filter(terms, term_filter):
    if term_filter == "all":
        terms.sort(key=lambda t: (t.get('category', 'zzz'), t['source']))
        return terms
    
    filter_cats = {
        "names": ["name", "organization", "place", "social", "website"],
        "social": ["social", "website"],
        "medical": ["medical", "chemical"],
        "technical": ["technical", "equipment"],
        "organizations": ["organization"],
        "places": ["place", "location"],
        "dates": ["date", "time"],
        "general": ["general"]
    }
    
    allowed = filter_cats.get(term_filter, [term_filter])
    filtered = [t for t in terms if t.get('category', 'general') in allowed]
    filtered.sort(key=lambda t: (t.get('category', 'zzz'), t['source']))
    
    return filtered

def extract_terms(source_text, target_text, focus, term_filter, max_terms, api_token, progress=gr.Progress()):
    if not source_text or not source_text.strip():
        return "❌ Please enter source text. | 請輸入來源文本。", "", gr.update(visible=False), ""
    
    client = get_client(api_token)
    
    source_text = source_text.strip()[:MAX_CHARS]
    target_text = target_text.strip()[:MAX_CHARS] if target_text else ""
    focus = focus.strip() if focus else ""
    
    # Detect if using custom command mode
    use_custom_mode = is_custom_command(focus) and term_filter == "all"
    
    progress(0.05, desc="📝 Preparing...")
    
    if use_custom_mode:
        progress(0.1, desc="🎯 Custom command detected! Following your instructions...")
    
    source_chunks = smart_chunk(source_text, CHUNK_SIZE)
    target_chunks = smart_chunk(target_text, CHUNK_SIZE) if target_text else []
    aligned_pairs = align_chunks(source_chunks, target_chunks)
    
    progress(0.1, desc=f"🔄 Processing {len(aligned_pairs)} segment(s)...")
    
    all_terms = []
    debug_logs = []
    start_time = time.time()
    
    mode_label = "CUSTOM COMMAND" if use_custom_mode else "STANDARD"
    debug_logs.append(f"Mode: {mode_label}\n")
    if use_custom_mode:
        debug_logs.append(f"User Command: {focus}\n")
    
    for i, (src, tgt) in enumerate(aligned_pairs):
        progress(0.1 + 0.7 * ((i + 1) / len(aligned_pairs)), 
                desc=f"🤖 Segment {i+1}/{len(aligned_pairs)}...")
        
        # Use custom extraction if in custom mode
        if use_custom_mode:
            terms, raw = extract_chunk_custom(src, tgt, focus, client)
        else:
            terms, raw = extract_chunk(src, tgt, focus, term_filter, client)
        
        debug_logs.append(f"""
=== Segment {i+1} ===
Source: {len(src)} chars | Target: {len(tgt)} chars
Raw terms: {len(terms)}
Response preview: {raw[:600]}...
""")
        
        all_terms.extend(terms)
        
        if i < len(aligned_pairs) - 1:
            time.sleep(0.5)
    
    progress(0.85, desc="🔍 Cleaning results...")
    
    valid_terms = validate_terms(all_terms)
    unique_terms = dedupe(valid_terms)
    raw_count = len(unique_terms)
    
    # Skip category filtering in custom mode - respect user's instruction
    if use_custom_mode:
        filtered_terms = unique_terms
        filtered_terms.sort(key=lambda t: (t.get('category', 'zzz'), t['source']))
    else:
        filtered_terms = apply_filter(unique_terms, term_filter)
    
    filtered_count = len(filtered_terms)
    
    final_terms = filtered_terms[:max_terms]
    
    elapsed = time.time() - start_time
    
    debug_log = f"""=== EXTRACTION SUMMARY ===
Mode: {mode_label}
Token: {'Provided' if api_token.strip() else 'Anonymous'}
Focus/Command: {focus if focus else 'None'}
Filter: {term_filter}
Segments: {len(aligned_pairs)}
Time: {elapsed:.1f}s

Raw extracted: {len(all_terms)}
After validation: {len(valid_terms)}
After dedupe: {raw_count}
After filter: {filtered_count}
Final: {len(final_terms)}

{"".join(debug_logs)}
"""
    
    if not final_terms:
        msg = f"⚠️ No terms found"
        if use_custom_mode:
            msg += f" matching your command.\n💡 Try a different instruction or simpler request."
        elif term_filter != "all":
            msg += f" matching filter '{term_filter}'.\n💡 Try setting Filter to **'all'**."
        return msg, "", gr.update(visible=False), debug_log
    
    progress(0.95, desc="📊 Formatting...")
    
    # Build result table
    table = "| # | Source | Target | Category |\n|:---:|:---|:---|:---:|\n"
    for i, t in enumerate(final_terms, 1):
        src = t['source'].replace('|', '∣')
        tgt = t['target'].replace('|', '∣')
        cat = t.get('category', 'general')
        table += f"| {i} | {src} | {tgt} | {cat} |\n"
    
    # Build CSV
    csv_lines = ["Source,Target,Category"]
    for t in final_terms:
        src_csv = t["source"].replace('"', '""')
        tgt_csv = t["target"].replace('"', '""')
        csv_lines.append(f'"{src_csv}","{tgt_csv}","{t.get("category", "general")}"')
    csv_content = "\n".join(csv_lines)
    
    progress(1.0, desc="✅ Done!")
    
    # Build result message
    mode_note = "🎯 **Custom Mode**" if use_custom_mode else ""
    filter_note = ""
    if not use_custom_mode and filtered_count < raw_count:
        filter_note = f" (filtered from {raw_count})"
    
    result = f"✅ **{len(final_terms)} terms** extracted in {elapsed:.1f}s{filter_note}\n{mode_note}\n\n{table}"
    
    return result, csv_content, gr.update(visible=True), debug_log

def save_file(csv_content, fmt):
    if not csv_content:
        return None
    
    lines = csv_content.strip().split('\n')[1:]
    terms = []
    for line in lines:
        parts = line.split('","')
        if len(parts) >= 3:
            terms.append({
                'source': parts[0].strip('"'),
                'target': parts[1],
                'category': parts[2].strip('"')
            })
    
    paths = {"csv": "/tmp/terms.csv", "json": "/tmp/terms.json", 
             "tsv": "/tmp/glossary.tsv", "tbx": "/tmp/terms.tbx"}
    path = paths.get(fmt)
    
    if fmt == "csv":
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write(csv_content)
    elif fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"terms": terms}, f, indent=2, ensure_ascii=False)
    elif fmt == "tsv":
        with open(path, "w", encoding="utf-8") as f:
            for t in terms:
                f.write(f"{t['source']}\t{t['target']}\n")
    elif fmt == "tbx":
        tbx = '<?xml version="1.0"?>\n<martif type="TBX"><text><body>\n'
        for i, t in enumerate(terms):
            tbx += f'<termEntry id="t{i+1}"><langSet xml:lang="zh"><tig><term>{t["source"]}</term></tig></langSet><langSet xml:lang="en"><tig><term>{t["target"]}</term></tig></langSet></termEntry>\n'
        tbx += '</body></text></martif>'
        with open(path, "w", encoding="utf-8") as f:
            f.write(tbx)
    
    return path

def clear_all():
    return "", "", "", "all", 150, "", "📋 Ready | 準備就緒", "", gr.update(visible=False)

# ========== UI ==========
with gr.Blocks(title="Term Extractor v3.7", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("# 🔤 Terminology Extraction Tool v3.7")
    gr.Markdown("Extract bilingual terminology from parallel texts. | 從平行文本中提取雙語術語。")
    gr.Markdown("*By [digimarketingai](https://github.com/digimarketingai)*")
    
    with gr.Row():
        with gr.Column():
            source_box = gr.Textbox(
                label="📄 Source Text (Required) | 來源文本（必填）", 
                lines=10, 
                placeholder="Paste Chinese source text... | 貼上中文來源文本..."
            )
        with gr.Column():
            target_box = gr.Textbox(
                label="📝 Target Text (Optional) | 目標文本（選填）", 
                lines=10, 
                placeholder="Paste English translation for better accuracy... | 貼上英文翻譯以提高準確性..."
            )
    
    with gr.Row():
        focus_box = gr.Textbox(
            label="🎯 Focus / Custom Command | 提取重點 / 自訂指令", 
            placeholder="Keywords: social media, medical, place | OR | Custom: 'Extract only person names' / '只提取人名'",
            info="💡 Enter keywords OR full commands! With Filter='all', commands are followed directly. | 輸入關鍵字或完整指令！篩選='all'時，會直接遵循指令。",
            scale=2
        )
        filter_dd = gr.Dropdown(
            label="📁 Filter | 篩選", 
            choices=["all", "social", "medical", "organizations", "places", "dates", "technical", "general"], 
            value="all",
            info="Set to 'all' for custom commands | 設為 'all' 以使用自訂指令",
            scale=1
        )
        max_slider = gr.Slider(
            label="Max Terms | 最大術語數", 
            minimum=20, 
            maximum=300, 
            value=150, 
            step=10, 
            scale=1
        )
    
    with gr.Accordion("🔑 API Token (Optional) | API 令牌（選填）", open=False):
        token_box = gr.Textbox(
            label="LLM7 Token", 
            placeholder="Get free token at token.llm7.io for higher limits | 在 token.llm7.io 獲取免費令牌以提高限制",
            type="password"
        )
        gr.Markdown("⚠️ Without token: 8000 char limit. [Get free token →](https://token.llm7.io) | 無令牌：8000 字元限制")
    
    with gr.Row():
        extract_btn = gr.Button("🚀 Extract | 提取", variant="primary", scale=2)
        clear_btn = gr.Button("🗑️ Clear | 清除", scale=1)
    
    result_box = gr.Markdown("📋 Ready | 準備就緒")
    csv_state = gr.State("")
    
    download_row = gr.Row(visible=False)
    with download_row:
        gr.Button("📥 CSV").click(lambda c: save_file(c, "csv"), [csv_state], [gr.File()])
        gr.Button("📥 JSON").click(lambda c: save_file(c, "json"), [csv_state], [gr.File()])
        gr.Button("📥 TSV").click(lambda c: save_file(c, "tsv"), [csv_state], [gr.File()])
        gr.Button("📥 TBX").click(lambda c: save_file(c, "tbx"), [csv_state], [gr.File()])
    
    with gr.Accordion("🔧 Debug Log | 除錯日誌", open=False):
        debug_box = gr.Textbox(lines=15, show_copy_button=True)
    
    with gr.Accordion("💡 Tips & Examples | 使用提示與範例", open=False):
        gr.Markdown("""
## 🆕 NEW: Custom Command Mode | 自訂指令模式

**When Filter = 'all'**, you can enter full commands in the Focus field:

### English Examples:
- `Extract only person names and titles`
- `Find all organization names`
- `Get only dates and time expressions`
- `Extract medical terms related to dengue fever`
- `List all social media accounts mentioned`
- `Find chemical compound names only`

### 繁體中文範例：
- `只提取人名和職稱`
- `找出所有機構名稱`
- `只要日期和時間相關的詞彙`
- `提取與登革熱相關的醫學術語`
- `列出所有提到的社群媒體帳號`
- `只找化學化合物名稱`

---

## Standard Mode | 標準模式

**Simple keywords** trigger standard extraction with focus:
- `social media` → Prioritizes social platforms
- `medical` → Prioritizes medical terms
- `place` → Prioritizes locations
- `date` → Prioritizes dates/times

---

## General Tips | 一般提示

- **Filter = 'all'**: Maximum extraction OR custom commands
- **With target text**: More accurate translations
- **Max Terms**: Limit results to top N terms
        """)
    
    extract_btn.click(
        extract_terms, 
        [source_box, target_box, focus_box, filter_dd, max_slider, token_box],
        [result_box, csv_state, download_row, debug_box]
    )
    
    clear_btn.click(clear_all, outputs=[
        source_box, target_box, focus_box, filter_dd, max_slider, 
        token_box, result_box, csv_state, download_row
    ])

if __name__ == "__main__":
    demo.launch(share=True)
