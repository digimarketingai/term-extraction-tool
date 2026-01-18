# Term Extraction Tool v3.6
# Bilingual Terminology Extractor with Gradio Interface
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

def get_focus_instruction(focus):
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

def extract_chunk(source, target, focus, term_filter, client):
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
        return "❌ Please enter source text.", "", gr.update(visible=False), ""
    
    client = get_client(api_token)
    
    source_text = source_text.strip()[:MAX_CHARS]
    target_text = target_text.strip()[:MAX_CHARS] if target_text else ""
    focus = focus.strip() if focus else ""
    
    progress(0.05, desc="📝 Preparing...")
    
    source_chunks = smart_chunk(source_text, CHUNK_SIZE)
    target_chunks = smart_chunk(target_text, CHUNK_SIZE) if target_text else []
    aligned_pairs = align_chunks(source_chunks, target_chunks)
    
    progress(0.1, desc=f"🔄 Processing {len(aligned_pairs)} segment(s)...")
    
    all_terms = []
    debug_logs = []
    start_time = time.time()
    
    for i, (src, tgt) in enumerate(aligned_pairs):
        progress(0.1 + 0.7 * ((i + 1) / len(aligned_pairs)), 
                desc=f"🤖 Segment {i+1}/{len(aligned_pairs)}...")
        
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
    
    filtered_terms = apply_filter(unique_terms, term_filter)
    filtered_count = len(filtered_terms)
    
    final_terms = filtered_terms[:max_terms]
    
    elapsed = time.time() - start_time
    
    debug_log = f"""=== EXTRACTION SUMMARY ===
Token: {'Provided' if api_token.strip() else 'Anonymous'}
Focus: {focus if focus else 'None'}
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
        if term_filter != "all":
            msg += f" matching filter '{term_filter}'.\n💡 Try setting Filter to **'all'**."
        return msg, "", gr.update(visible=False), debug_log
    
    progress(0.95, desc="📊 Formatting...")
    
    table = "| # | Source | Target | Category |\n|:---:|:---|:---|:---:|\n"
    for i, t in enumerate(final_terms, 1):
        src = t['source'].replace('|', '∣')
        tgt = t['target'].replace('|', '∣')
        cat = t.get('category', 'general')
        table += f"| {i} | {src} | {tgt} | {cat} |\n"
    
    csv_lines = ["Source,Target,Category"]
    for t in final_terms:
        src_csv = t["source"].replace('"', '""')
        tgt_csv = t["target"].replace('"', '""')
        csv_lines.append(f'"{src_csv}","{tgt_csv}","{t.get("category", "general")}"')
    csv_content = "\n".join(csv_lines)
    
    progress(1.0, desc="✅ Done!")
    
    filter_note = ""
    if filtered_count < raw_count:
        filter_note = f" (filtered from {raw_count})"
    
    result = f"✅ **{len(final_terms)} terms** extracted in {elapsed:.1f}s{filter_note}\n\n{table}"
    
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
    return "", "", "", "all", 150, "", "📋 Ready", "", gr.update(visible=False)

# ========== UI ==========
with gr.Blocks(title="Term Extractor", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("# 🔤 Terminology Extraction Tool v3.6")
    gr.Markdown("Extract bilingual terminology from parallel texts. | 從平行文本中提取雙語術語。")
    gr.Markdown("*By [digimarketingai](https://github.com/digimarketingai)*")
    
    with gr.Row():
        with gr.Column():
            source_box = gr.Textbox(label="📄 Source Text (Required) | 來源文本（必填）", lines=10, placeholder="Paste Chinese source text... | 貼上中文來源文本...")
        with gr.Column():
            target_box = gr.Textbox(label="📝 Target Text (Optional) | 目標文本（選填）", lines=10, placeholder="Paste English translation for better accuracy... | 貼上英文翻譯以提高準確性...")
    
    with gr.Row():
        focus_box = gr.Textbox(
            label="🎯 Extraction Focus (optional) | 提取重點（選填）", 
            placeholder="e.g., social media, medical, organization, place, chemical, date",
            info="Prioritize specific term types | 優先提取特定類型的術語",
            scale=2
        )
        filter_dd = gr.Dropdown(
            label="📁 Filter | 篩選", 
            choices=["all", "social", "medical", "organizations", "places", "dates", "technical", "general"], 
            value="all",
            info="Filter results by category | 按類別篩選結果",
            scale=1
        )
        max_slider = gr.Slider(label="Max Terms | 最大術語數", minimum=20, maximum=300, value=150, step=10, scale=1)
    
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
    
    with gr.Accordion("💡 Tips | 使用提示", open=False):
        gr.Markdown("""
**English:**
- **Filter = 'all'**: Extracts maximum terms across all categories
- **Focus**: Tells AI what to prioritize (e.g., "date" for dates/times)
- **With target text**: More accurate translations from parallel alignment

**繁體中文：**
- **篩選 = 'all'**：提取所有類別的最大術語數
- **提取重點**：告訴 AI 優先提取什麼（例如，「date」用於日期/時間）
- **有目標文本**：透過平行對齊獲得更準確的翻譯
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
    demo.launch()
