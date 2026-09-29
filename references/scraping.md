# Scraping without burning tokens

Read this during setup if the user scrapes. Pass the rules that apply into the fleet rules block.

The honest headline: **a fleet saves some tokens, but for scraping the big saving is keeping raw
pages out of the model entirely.** A 200 KB HTML page is ~50,000 tokens. The same page as clean
text is ~2,000. The same page parsed by a CSS selector is 0.

## The ladder — always use the lowest rung that works

1. **Plain code, zero tokens.** The model looks at 2–3 sample pages *once*, writes selectors /
   a parser, and from then on the script runs without any model. This handles most sites.
2. **Cheap model on cleaned text.** Only for pages the parser can't handle (messy layouts,
   free-text fields). Strip the page to readable text or markdown first (drop `<script>`,
   `<style>`, nav, footer, SVG), then send it to the cheapest capable model via a script
   (`extract.py`), not an agent chat. An agent session re-sends its whole system prompt and
   tool list every turn; a direct API call sends only the page.
3. **Agent session.** Only for *writing and fixing* the scraper — never for processing pages
   one by one.

## Rules the fleet follows

- **Never paste raw HTML into a chat.** Save it to a file; let code read it.
- **Sample before scale.** Run on 5 pages, check the output, then run on 5,000.
- **Cache every fetch** (file per URL hash). A re-run after a bug fix should cost zero fetches
  and zero tokens for pages already done.
- **Cache every extraction** too — same key idea. Never pay twice for the same page.
- **Small outputs.** Ask for JSON with fixed fields. No explanations in the output.
- **Batch and go off-peak.** DeepSeek's off-peak window is roughly half price (see
  `models.md`); a big overnight run should be scheduled there.
- **Reports, not logs.** The checker reports counts (rows, empty fields, duplicates, errors)
  and 3 example rows — never the whole dataset — back to the boss.
- **When a site breaks, fix the parser, don't fall back to the model.** A silent switch from
  rung 1 to rung 2 on 10,000 pages is how a bill explodes.

## Sensitive data

If the scraped data includes personal information (names, phone numbers, student or customer
records), every model provider that sees it now holds a copy. Ask the user which providers they
are comfortable with before routing that data anywhere, and keep it in rung 1 (plain code) when
possible.
