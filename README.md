# codex-fleet-setup

**Save tokens in Codex by turning it into a small team.** Your main Codex session becomes the
**boss**: it plans, decides, and gives you one answer. A crew of helpers does the reading, coding
and checking on cheap Chinese models (DeepSeek, Qwen, GLM), and each one reports back to the boss
in a short fixed format with proof.

It starts with an interview about how you actually use AI, tells you honestly where your tokens
are going, then writes the team into `~/.codex/` (backing up anything it changes first).

**用 Codex 搭一个省 token 的智能体团队。** 主会话当"老板"，负责规划和拍板；侦察、写代码、验收、审查交给
便宜的国产模型（DeepSeek、通义千问、智谱 GLM），每个成员干完活只交一份带证据的简短汇报。开始前会先做一次
访谈，了解你平时怎么用 AI，直接告诉你 token 花在了哪里。

## Install · 安装

**Option 1 — in Codex (easiest):** paste this into Codex:

> Install the skill from https://github.com/eyhshen/codex-fleet-setup

**Option 2 — in a terminal:**

```
git clone https://github.com/eyhshen/codex-fleet-setup.git ~/.codex/skills/codex-fleet-setup
```

Then start a new Codex session and type `$codex-fleet-setup`. Answer in Chinese or English —
it follows your language. 装好后新开一个 Codex 会话，输入 `$codex-fleet-setup`，用中文回答即可。

## What you get · 你会得到

| Member | Job | Typical model |
|---|---|---|
| **boss** (your normal Codex session) | plans, delegates, gives you one answer | your Codex plan model |
| **scout** | "how is this site / code built?" — returns the answer, not file dumps | `deepseek-flash` |
| **builder** | writes and fixes scrapers and scripts | `deepseek-v4-pro` / `glm-5.3` |
| **checker** | runs it on 5–20 pages; counts rows, gaps, duplicates | `deepseek-flash` |
| **reviewer** | catches real bugs and runaway-cost loops | a different vendor from the builder |
| **`extract.py`** (for scraping) | sends cleaned page text to the cheapest model directly | `deepseek-flash`, off-peak |

`extract.py` estimates the cost before spending anything (`--dry-run`), never pays twice for the
same page, and writes a CSV that opens correctly in Excel, Chinese text included.

The interview picks the exact models from the API keys you have, where you live, and whether your
data includes personal information.

## Before you start · 准备

- Codex CLI (tested on 0.147) with a ChatGPT plan.
- At least one API key, as an environment variable — **DeepSeek is the best first key** for most
  people: `export DEEPSEEK_API_KEY="..."`. The skill never writes keys into files.

## Good to know · 注意

- Prices and model names were checked on 2026-09-29 and change often. The skill runs a live test
  on each provider during setup and drops any that fail.
- Codex only works with providers that support OpenAI's Responses API: DeepSeek, Qwen (Bailian)
  and GLM (Z.ai). Kimi and MiniMax can still be used by `extract.py`.
- If you use a proxy app (Clash, V2Ray…), Codex's sandbox may block the helpers from going
  online. Setup tests this and tells you what to do.
- The biggest saving isn't the team, it's habits: never paste page source into the chat, start
  fresh sessions per task, and test on 5 pages before 5,000.

## Update · 更新

```
git -C ~/.codex/skills/codex-fleet-setup pull
```

Run `$codex-fleet-setup` again anytime to re-tune. It only replaces its own section of your
`AGENTS.md`.

## License

MIT
