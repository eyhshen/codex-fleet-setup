---
name: codex-fleet-setup
description: Build a token-saving agent fleet for Codex — a boss session plus cheap specialist agents (scout, builder, checker, reviewer), with Chinese models (DeepSeek, Qwen, Kimi, GLM, MiniMax) where they fit — through a short interview about how the user actually uses AI. Use when the user asks to set up, build, or re-tune an agent fleet / crew / subagents in Codex, wants to save tokens, or runs $codex-fleet-setup. 适用于：搭建 Codex 智能体团队、省 token、用国产模型。
---

# Codex Fleet Setup — interview, then build

You are setting up an agent fleet for the user inside **Codex**. The shape:

- **Boss** = the user's main Codex session (strongest model). It plans, delegates, and gives
  the user one answer. Its rules go into `~/.codex/AGENTS.md`.
- **Crew** = custom agents in `~/.codex/agents/*.toml`, each on the cheapest model that does
  its job well, each ending its work with a short REPORT to the boss.
- **Bulk lane** (optional, for scraping) = `extract.py`, a plain script that sends cleaned pages
  to a cheap model directly — no agent session overhead per page.

Files next to this one:
- `references/models.md` — Chinese + OpenAI model menu, prices, how each plugs into Codex. Read it
  before Step 6.
- `references/scraping.md` — token rules for scraping. Read it if the user scrapes.
- `templates/fleet-rules.md` — the boss rules block. `templates/agents/*.toml` — the crew.
  `templates/extract.py` — the bulk lane.

**Talk like a person.** Match the user's language — if they write Chinese, run the whole
interview in Chinese. Ask ONE question at a time, give numbered options, put the recommended one
first and mark it "(recommended / 推荐)". Keep each question to a few lines. Never dump templates
or raw file contents at the user.

---

## Step 0 — Look around (silent)

Check, without reading contents yet:
- `~/.codex/config.toml`, `~/.codex/AGENTS.md`, `~/.codex/agents/` (existing fleet files?)
- env vars that are set (names only, never print values): `DEEPSEEK_API_KEY`,
  `DASHSCOPE_API_KEY`, `MOONSHOT_API_KEY`, `ZHIPUAI_API_KEY` / `ZAI_API_KEY`, `MINIMAX_API_KEY`,
  `OPENAI_API_KEY`
- `codex --version`

Use this to pre-fill answers. Say nothing about this step.

## Step 1 — Interview: how do you use AI?

This is the heart of the skill. The answers decide everything else. Ask in order; skip a
question when Step 0 or an earlier answer already settled it.

1. **Name.** "What should the crew call you?"
2. **What you use AI for** (multi-select): scraping / collecting data · building apps or tools ·
   research & reading · writing & content · automating chores.
3. **A normal session.** "When you work with Codex, what does it usually look like?"
   - one long conversation that runs for hours
   - short sessions, one task each
   - I start a big job and leave it running (overnight / while away)
   (Long single sessions are the #1 token drain — note it for Step 7.)
4. **Where the budget runs out.** "What runs out first?"
   - the Codex / ChatGPT plan limit (weekly or 5-hour cap)
   - API bill
   - both / not sure
5. **What you already have** (multi-select): ChatGPT plan with Codex (which tier?) · API key for
   DeepSeek · Qwen / Alibaba Bailian (百炼) · Kimi (Moonshot) · GLM (智谱 / z.ai) · MiniMax ·
   a coding plan subscription from one of them · none yet.
6. **Where you are.** Mainland China / outside China. (Decides `.cn` vs international endpoints
   and which sign-ups work.)
7. **If they scrape** (ask as one compact block, let them answer loosely):
   - roughly how many pages, how often (once / daily / weekly)?
   - plain pages, or pages that need login / JavaScript / clicking?
   - output: CSV, JSON, database, spreadsheet?
   - "Do you paste page content into the chat today?" (If yes, that is the fix — say so kindly.)
8. **Sensitive data.** "Does anything you process include personal info — names, phone
   numbers, customers, students?" If yes: "Which providers are you OK with seeing it?"
9. **Guardrails.** "Should the crew stop and ask before hard-to-undo actions?"
   - Always ask before commit, push, delete (recommended)
   - Only before push and delete
   - Never ask (only if you can undo mistakes yourself)
10. **Style.** non-coder who builds real things · somewhere in between · developer.

## Step 2 — Diagnose (say this back in 3–5 lines)

Before proposing anything, tell the user where their tokens are going, based on their answers.
Be honest, not flattering. Typical findings:
- One long session → "every message re-sends the whole conversation. Fresh session per task
  saves more than any model switch."
- Pasting pages into chat → "a page is ~50,000 tokens as HTML, 0 as parser code. Fix this first."
- Plan-limit bound → "move reading/searching/bulk work off the Codex plan onto cheap API models;
  keep the plan for the boss and hard coding."
- API-bill bound → "switch the bulk work to DeepSeek off-peak or a flat-rate coding plan."

## Step 3 — Pick the crew

Always: boss (the main session) + builder. Offer the rest with one line each:
- **scout** — cheap research: "where is X", "how is this site built", "what do the docs say"
- **checker** — proves the scraper works on a sample; counts rows, gaps, duplicates
- **reviewer** — catches real bugs and runaway-cost loops before you save or ship
- **bulk lane (`extract.py`)** — only if they scrape more than a few hundred pages and a plain
  parser won't cover every page

Recommended for a scraping user: all of it. For others: scout + builder + reviewer.

## Step 4 — Spend tier

"How should the crew spend?"
- **Balanced (recommended)** — strong model for the boss, cheap models for everyone else.
- **Cheapest** — Chinese models everywhere they can go; boss stays on the plan model at low effort.
- **Best quality** — strongest models everywhere; only bulk work goes cheap.

## Step 5 — Sensitive-data check

If Step 1.8 said yes: any provider the user did not approve is removed from the choices for
every crew member that may see that data (checker, bulk lane, and builder if it reads the data).
Say which ones you removed in one line.

## Step 6 — Match models (read `references/models.md` now)

Using tier + keys they have + location + data check, choose a model for each crew member and
for the bulk lane. Follow the "How it plugs into Codex" section of `models.md` exactly — some
providers work as a Codex model provider, some only work from `extract.py`. Never assign a
crew member to a provider Codex cannot drive; put that provider on the bulk lane instead.

If a needed key is missing, pick from what they have, and list "optional upgrades" (which key
to get, what it would save) at the end.

## Step 7 — Preview (short, then confirm)

Show a small table: crew member → model → provider → rough price. Then the 3–5 line diagnosis
from Step 2 as "the habits that save the most". Ask: "Write this?"

## Step 8 — Write

Only after they confirm. Only inside `~/.codex/` (and the project folder for `extract.py`).

1. **Back up first.** If any file you will change exists (`config.toml`, `AGENTS.md`, an agent
   with the same name), copy it to `~/.codex/fleet-backup-<YYYY-MM-DD-HHMMSS>/` (a new folder every run —
   never write into an existing backup) before touching it. Never delete anything.
2. **Providers** → append only the needed `[model_providers.<id>]` blocks to
   `~/.codex/config.toml` (skip ones that already exist). Never write an API key into a file —
   keys stay in environment variables; tell the user the exact `export` line to add to their
   shell profile. Only if the boss-move rule in `models.md` applies: set `model` and `model_provider`
   at the TOP of `config.toml`, above the first `[section]` — replace an existing `model =`
   and `model_provider =` lines rather than adding second ones.
3. **Crew** → for each chosen agent, fill `templates/agents/<name>.toml` and write to
   `~/.codex/agents/<name>.toml`. Placeholders:
   - `{{USER_NAME}}`, `{{GENERATED_DATE}}` (today), `{{MODEL}}`, `{{EFFORT}}`
     (`low` / `medium` / `high`)
   - `{{PROVIDER_LINE}}` → `model_provider = "<id>"` plus a newline when the agent uses a
     non-default provider; empty string otherwise. For "plan model", use the `model` value
     from their `config.toml`.
   - `{{NETWORK_BLOCK}}` (scout, builder, checker) → if they scrape, the two lines
     `[sandbox_workspace_write]` and `network_access = true` (it must stay the last thing in
     the file); empty otherwise. Without it Codex blocks internet for crew members.
   - `{{GATE_LINE}}` (builder) → e.g. `- Never git commit, git push, or delete files — leave that to <name>.`
     matching the guardrail answer; empty if they chose "never ask"
4. **Boss rules** → fill `templates/fleet-rules.md` and put it in `~/.codex/AGENTS.md`. If a
   `fleet-kit:start … fleet-kit:end` block is already there, replace only that block; otherwise
   append. Placeholders:
   - `{{WORK_CONTEXT}}` — one sentence from Step 1.2/1.7. `{{STYLE_LINE}}` — one sentence on how
     to explain things, from Step 1.10.
   - `{{CREW_LIST}}` — comma list.
   - `{{ROUTING_LINES}}` — one bullet per chosen crew member: "- <when> → `<agent>`", e.g.
     "- Need to know how a site or codebase works → `scout`".
     Add "- Processing many pages → run `extract.py`, never an agent" if the bulk lane is on.
   - `{{SCRAPING_RULES}}` — if they scrape: a `### Scraping` section with the rules from
     `references/scraping.md` "Rules the fleet follows" (as bullets); else empty.
   - `{{GUARDRAILS_BLOCK}}` — a `### Hard stops` section from Step 1.9, e.g.
     "Stop and ask {{USER_NAME}} before: `git commit`, `git push`, deleting files."
5. **Bulk lane** (if chosen) → copy `templates/extract.py` into the user's scraping project
   (ask which folder) and set its `PROVIDER` defaults from Step 6. Change nothing else in it —
   it already writes CSV (Excel-safe for Chinese) when the output name ends in `.csv`.
6. **Check your work.** Grep every written file for `{{` — zero must remain. Parse every TOML
   you wrote or edited, including `config.toml` (`python3 -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" <file>`).
   Then run the smoke test from `references/models.md` once per provider you configured (needs
   the key exported). Report each result honestly: working, or the error and the fix. A
   provider that fails the smoke test must not stay assigned to a crew member.
   If they scrape, also spawn `scout` with "fetch https://example.com with curl and report the
   HTTP status". If it can't connect: a local proxy app (Clash, V2Ray — common in China) is
   the usual cause, because the sandbox blocks `127.0.0.1`. Tell the user plainly, and suggest
   running the fetch step in their own terminal (`python scraper.py`) while the crew keeps
   writing and checking the code.

## Step 9 — Hand over

End with, in plain words:
- **Your crew** — the table from Step 7.
- **How to use it** — "Just talk to Codex as usual. It's now the boss: it sends research to
  scout, code to builder, and checks results with checker. You'll get one answer back."
  Show one example prompt fitted to their work, e.g. "Scrape the product list from <site>
  into products.csv — scout the site first, then build, then check on 10 pages."
- **Habits that save the most** — the 2–3 from Step 2.
- **Keys to add** — the exact `export` lines, if any.
- **Re-tune** — "Run `$codex-fleet-setup` again anytime; it replaces only its own block."
