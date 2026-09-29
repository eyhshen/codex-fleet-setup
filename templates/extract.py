"""Usage: python extract.py INPUT_DIR OUT.jsonl|OUT.csv --fields "name,price,url" [options]."""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

PROVIDERS = {
    "deepseek": {"base_url": "https://api.deepseek.com", "key_env": "DEEPSEEK_API_KEY", "model": "deepseek-flash"},
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "key_env": "DASHSCOPE_API_KEY", "model": "qwen-flash"},
    "qwen-intl": {"base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "key_env": "DASHSCOPE_API_KEY", "model": "qwen-flash"},
    "kimi": {"base_url": "https://api.moonshot.cn/v1", "key_env": "MOONSHOT_API_KEY", "model": "kimi-k3"},
    "kimi-intl": {"base_url": "https://api.moonshot.ai/v1", "key_env": "MOONSHOT_API_KEY", "model": "kimi-k3"},
    "glm": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "key_env": "ZHIPUAI_API_KEY", "model": "glm-5.3-flash"},
    "glm-intl": {"base_url": "https://api.z.ai/api/paas/v4", "key_env": "ZAI_API_KEY", "model": "glm-5.3-flash"},
    "minimax": {"base_url": "https://api.minimaxi.com/v1", "key_env": "MINIMAX_API_KEY", "model": "MiniMax-M2.7"},
    "minimax-intl": {"base_url": "https://api.minimax.io/v1", "key_env": "MINIMAX_API_KEY", "model": "MiniMax-M2.7"},
}
PROVIDER = "deepseek"
# Model IDs change; check the provider's current model list before overriding this.
MODEL = None
MAX_CHARS = 24_000
DROP_TAGS = {"script", "style", "nav", "footer", "svg", "noscript"}

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in DROP_TAGS:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag.lower() in DROP_TAGS and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

def clean_text(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(raw, "html.parser")
            for node in soup.find_all(list(DROP_TAGS)):
                node.decompose()
            raw = soup.get_text(" ")
        except ImportError:
            parser = TextParser()
            parser.feed(raw)
            raw = " ".join(parser.parts)
    return re.sub(r"\s+", " ", raw).strip()

def cache_path(cache_dir, text, fields, model):
    key = hashlib.sha256((text + ",".join(fields) + model).encode()).hexdigest()
    return cache_dir / f"{key}.json"

def usage_total(response):
    usage = getattr(response, "usage", None)
    if not usage:
        return 0
    input_tokens = getattr(usage, "prompt_tokens", getattr(usage, "input_tokens", 0)) or 0
    output_tokens = getattr(usage, "completion_tokens", getattr(usage, "output_tokens", 0)) or 0
    return input_tokens + output_tokens

def request(client, model, prompt):
    formatted = True
    for attempt in range(3):
        try:
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            if formatted:
                kwargs["response_format"] = {"type": "json_object"}
            return client.chat.completions.create(**kwargs)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if formatted and status == 400:
                formatted = False
                continue
            retryable = status == 429 or (status is not None and 500 <= status < 600)
            retryable = retryable or exc.__class__.__name__ == "RateLimitError"
            if not retryable or attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("request failed")

def extract_one(item, client, model, fields, cache_dir):
    source, text, cache_file = item
    if cache_file.exists():
        try:
            return {"source": source, **json.loads(cache_file.read_text())}, True, 0
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    prompt = (
        "Extract one JSON object from the page text. Return JSON only, with exactly these "
        f"fields: {', '.join(fields)}. Use null when a value is absent.\n\nPAGE TEXT:\n{text}"
    )
    response = None
    try:
        response = request(client, model, prompt)
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content)
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("model returned JSON that is not an object")
        data = {field: parsed.get(field) for field in fields}
        cache_dir.mkdir(parents=True, exist_ok=True)
        suffix = hashlib.sha256(source.encode()).hexdigest()[:8]
        temp = cache_file.with_name(f"{cache_file.name}.{suffix}.tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, cache_file)
        return {"source": source, **data}, False, usage_total(response)
    except Exception as exc:
        return {"source": source, "error": str(exc)}, False, usage_total(response)

def parse_args():
    parser = argparse.ArgumentParser(description="Extract fixed JSON fields from saved pages.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fields", required=True)
    parser.add_argument("--provider", choices=PROVIDERS, default=PROVIDER)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()

def main():
    args = parse_args()
    if not args.input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {args.input_dir}")
    fields = [field.strip() for field in args.fields.split(",") if field.strip()]
    if not fields:
        raise SystemExit("--fields must contain at least one field")
    if {"source", "error"} & set(fields):
        raise SystemExit("--fields cannot include 'source' or 'error'; those columns are reserved")
    if args.workers < 1 or (args.limit is not None and args.limit < 0):
        raise SystemExit("--workers must be at least 1 and --limit cannot be negative")
    provider = PROVIDERS[args.provider]
    base_url, key_env = provider["base_url"], provider["key_env"]
    model = args.model or provider["model"]
    paths = sorted(p for p in args.input_dir.rglob("*") if p.suffix.lower() in {".html", ".htm", ".txt", ".md"})
    if args.limit is not None:
        paths = paths[: args.limit]
    cache_dir = args.output.resolve().parent / ".extract-cache"
    items = []
    truncated = 0
    total_chars = 0
    for path in paths:
        text = clean_text(path)
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
            truncated += 1
        total_chars += len(text)
        source = str(path.relative_to(args.input_dir))
        items.append((source, text, cache_path(cache_dir, text, fields, model)))
    hits = sum(cache_file.exists() for _, _, cache_file in items)
    if truncated:
        print(f"warning: {truncated} file(s) capped at {MAX_CHARS} cleaned characters", file=sys.stderr)
    if args.dry_run:
        # Character-to-token ratios vary; /3 is only a rough mixed CJK/English estimate.
        print(f"files: {len(items)}; cleaned chars: {total_chars}; rough tokens: {total_chars // 3}; cache hits: {hits}")
        return 0
    if not items:
        raise SystemExit("No supported input files found")
    api_key = os.environ.get(key_env)
    if not api_key:
        print(f'Missing {key_env}. Add this line to your shell profile:\nexport {key_env}="your-key"', file=sys.stderr)
        return 2
    try:
        from openai import OpenAI
    except ImportError:
        raise SystemExit("Missing the openai package. Install it with:\n  python3 -m venv .venv && . .venv/bin/activate && pip install openai")
    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=0)
    work = lambda item: extract_one(item, client, model, fields, cache_dir)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(work, items))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.lower() == ".csv":
        with args.output.open("w", encoding="utf-8-sig", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=["source", *fields, "error"])
            writer.writeheader()
            # Excel runs cells starting with = + - @ as formulas; scraped text must stay text.
            safe = lambda v: "'" + v if isinstance(v, str) and v[:1] in "=+-@" else v
            writer.writerows({k: safe(v) for k, v in row.items()} for row, _, _ in results)
    else:
        with args.output.open("w", encoding="utf-8") as out:
            for row, _, _ in results:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
    cached = sum(was_cached for _, was_cached, _ in results)
    errors = sum("error" in row for row, _, _ in results)
    tokens = sum(tokens for _, _, tokens in results)
    print(f"processed: {len(results)} / from cache: {cached} / errors: {errors} / approx tokens in+out: {tokens}")
    if errors:
        print(f"{errors} pages failed; re-run to retry them (successful pages are cached).", file=sys.stderr)
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
