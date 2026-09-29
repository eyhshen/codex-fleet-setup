# Model menu — 国产模型 + Codex

Checked 2026-09-29. Prices and model IDs move every few months: before writing a config, open
the provider's pricing link below and confirm the model ID still exists. Tell the user the
date these numbers are from.

## The one rule that decides everything

Codex (0.147+) only talks to providers that speak the **OpenAI Responses API**
(`wire_api = "responses"`; the old `"chat"` option was removed). So there are two lanes:

- **Inside Codex (crew members):** DeepSeek, Qwen (Alibaba Bailian 百炼), GLM via Z.ai.
- **Bulk lane only (`extract.py`, plain chat API):** Kimi, MiniMax, and GLM via BigModel
  (mainland) — no verified Responses endpoint, so never assign them to a Codex crew member.

Each crew member can use its own provider: add `model_provider = "<id>"` to its agent file.
Tested 2026-09-29 on Codex 0.147 — the main session stayed on OpenAI while the crew member's
request went to its own provider.

## Prices (per 1M tokens)

| Provider | Model ID | Input (cache hit / miss) | Output | Good for | Codex crew? |
|---|---|---|---|---|---|
| DeepSeek | `deepseek-flash` | $0.003 / $0.15 | $0.60 | scout, checker, bulk extraction | yes |
| DeepSeek | `deepseek-v4-pro` | $0.022 / $0.66 | $1.98 | builder, reviewer | yes |
| Qwen 百炼 | `qwen3-coder-flash` | ¥1 (≤32K input) | ¥4 | builder (mainland) | yes |
| Qwen 百炼 | `qwen3.8-2.4t-a95b` | ¥12 | ¥36 | hard reasoning | yes |
| GLM (Z.ai) | `glm-5.3` / `glm-5.3-flash` | check page | check page | builder / cheap coding | yes (Z.ai only) |
| MiniMax | `MiniMax-M2.7` | $0.06 / $0.30 | $1.20 | bulk extraction alternative | no → extract.py |
| Kimi | `kimi-k3` | $0.30 / $3 | $15 | strong but NOT a token saver | no → extract.py |

DeepSeek prices above are **off-peak**. Peak (2×) is 01:00–04:00 and 06:00–10:00 UTC on
weekdays (= 09:00–12:00 and 14:00–18:00 Beijing time). Everything else — nights, weekends,
Chinese public holidays — is half price. Schedule big runs there.

Flat-rate plans (worth it if the user codes all day): GLM Coding Plan (from ~$18/mo; off-peak
and weekends use half the plan points), MiniMax Token Plan ($20 / $50 / $120 per month). These
plans are built for tools like Claude Code and Kimi Code, not for Codex — mention them, don't
wire them into Codex.

Sources: [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/) ·
[Bailian](https://help.aliyun.com/en/model-studio/model-pricing) ·
[GLM-5.3](https://docs.z.ai/guides/llm/glm-5.3) ·
[MiniMax](https://platform.minimax.io/subscribe/token-plan) ·
[Kimi K3](https://forum.moonshot.ai/t/kimi-k3-is-here-our-most-capable-model/480) ·
[Codex config reference](https://developers.openai.com/codex/config-reference)

## Tier table — which model for which crew member

"Plan model" = whatever model the user's Codex / ChatGPT plan already uses (read `model` from
their `config.toml`; don't invent an OpenAI model name). For that, write no `model_provider` line.

| Crew member | Balanced (recommended) | Cheapest | Best quality |
|---|---|---|---|
| boss (main session) | plan model | plan model, low effort (see below) | plan model, high effort |
| scout | `deepseek-flash` | `deepseek-flash` | `deepseek-v4-pro` |
| builder | `deepseek-v4-pro` or `glm-5.3` | `deepseek-v4-pro` / `qwen3-coder-flash` | plan model |
| checker | `deepseek-flash` | `deepseek-flash` | `deepseek-v4-pro` |
| reviewer | plan model | `glm-5.3-flash` or `qwen3-coder-flash` | plan model, high effort |
| bulk lane | `deepseek-flash` off-peak | `deepseek-flash` off-peak | `deepseek-v4-pro` |

Why the reviewer differs from the builder: a second vendor catches mistakes the first one is
blind to. If builder is DeepSeek, reviewer should not be DeepSeek.

**Boss-move rule:** only move the boss to `deepseek-v4-pro` if the user said the plan limit is
what runs out (not the API bill), picked Cheapest, accepts a weaker boss, **and** approved DeepSeek in the sensitive-data check
(Step 5) — the boss sees everything the user pastes in. Otherwise the
boss stays on the plan model in every tier. The boss is where quality matters most.

## Codex provider blocks (append to `~/.codex/config.toml`)

Keys live in environment variables only — never in this file.

```toml
[model_providers.deepseek]
name = "DeepSeek"
base_url = "https://api.deepseek.com"
env_key = "DEEPSEEK_API_KEY"
wire_api = "responses"

[model_providers.qwen]
name = "Qwen (Bailian)"
# Mainland: your workspace URL from the Bailian console, e.g.
# https://<WorkspaceId>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
# Outside China: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
base_url = "<ask the user / copy from Bailian console>"
env_key = "DASHSCOPE_API_KEY"
wire_api = "responses"

[model_providers.zai]
name = "GLM (Z.ai)"
base_url = "https://api.z.ai/api/v1"
env_key = "ZAI_API_KEY"
wire_api = "responses"
```

Then in an agent file: `model_provider = "deepseek"` and `model = "deepseek-flash"`.

## Smoke test — run one per provider you configured

```
codex exec -c model_provider=deepseek -m deepseek-flash "Reply with just OK" < /dev/null
```

`OK` back = key, endpoint and Responses support all work. An error = fix it before handing
over. Routing is proven; how well each Chinese model drives Codex's tools (editing files,
running commands) is not — have the checker do one tiny real task on each crew member's model
before trusting it with a big job.

## Where the user is

- **Mainland China:** DeepSeek and Bailian (mainland endpoints) work directly. Z.ai is the
  international GLM site; mainland users with a BigModel (bigmodel.cn) key should use GLM on the
  bulk lane only.
- **Outside China:** DeepSeek, Qwen international, Z.ai all work. Signing up for mainland-only
  consoles may need a Chinese phone number.
