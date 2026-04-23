# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

CorpLink-AI extracts inter-organizational relationships (partnerships, acquisitions, collaborations, etc.) from English-language news articles. It processes DOCX (Lexis) or RTF (Factiva) document archives, runs NER and fuzzy matching locally, optionally calls OpenAI GPT-4o-mini for unknown companies, and outputs network-analysis-ready CSVs. Core design goal: keep cost near zero by doing ~99% of work locally and calling the API only for genuinely ambiguous cases, with results cached in MySQL so every run improves future runs.

## Running the Project

**Web API (primary interface):**
```bash
uvicorn WebApp.app:app --reload
```

**CLI pipeline (direct, no web server):**
```bash
python Corplink/main.py   # interactive prompts for MySQL + config
```

No test suite exists. Runtime validation covers DB connectivity and required file presence.

## Architecture & Data Flow

```
Input (DOCX/RTF)
  → step_extract.py     keyword or semantic sentence filtering
  → step_company.py     spaCy NER + RapidFuzz fuzzy match + Sentence-Transformer fallback
  → step_ai_autofill.py (optional) GPT-4o-mini cleans unknown names, cached in MySQL
  → step_standardize.py alias resolution, writes canonical names to MySQL
  → step_network.py     builds adjacency list + pivot/co-occurrence table

Outputs: result.csv · result_adjacency_list.csv · pivot_table.csv
```

`Corplink/main.py` orchestrates the steps and supports three **AI levels**:
- **MANUAL (0)**: runs Steps 1–2, pauses so the user can edit `result_mapping_todo.csv` manually
- **ASSIST (1)**: adds AI suggestion columns (`AI_Suggested_Canonical`, etc.) without overwriting user data
- **AUTO (2)**: full unattended run including GPT-4o-mini autofill

## Module Reference

| File | Role |
|------|------|
| `Corplink/options.py` | Enums (`KeywordMode`, `AILevel`, `ExtractMode`) and `RunOptions` dataclass |
| `Corplink/state.py` | Global mutable state shared across modules (`KEYWORD_ROOTS`, `SENTENCE_RECORDS`, `USE_SEMANTIC_FILTER`, `EXTRACT_MODE`) |
| `Corplink/constants.py` | Pre-compiled regex patterns; `PRESET_KEYWORDS_2025` (36 relationship terms); `MAX_COMP_COLS = 50`; `ANCHOR_TEXT` and `NOISE_CONCEPTS` for semantic filtering |
| `Corplink/env_bootstrap.py` | Auto-installs missing pip packages and spaCy models; calls `os.execv()` to restart the process after installing |
| `Corplink/config.py` | CLI wizard + web-mode silent config (reads `config.json`); calls `apply_options_to_state()` to mutate global state |
| `Corplink/text_utils.py` | Text normalization and token validation helpers used by step_company |
| `Corplink/model_utils.py` | Loads spaCy `en_core_web_sm` (parser/lemmatizer disabled for speed) and `all-MiniLM-L6-v2`; pre-computes `noise_vecs` at import time; exposes `calc_Bad_Score()` |
| `Corplink/factiva_rtf.py` | Parses Factiva RTF exports: splits by `(END)` markers, extracts title/publisher/date/body with 4-format date fallback |
| `Corplink/step_extract.py` | Detects Lexis (TOC-based docx) vs Factiva (RTF); filters sentences by keyword presence or cosine similarity ≥ 0.45 to `ANCHOR_TEXT`; caches anchor embedding as function attribute |
| `Corplink/step_company.py` | spaCy NER → `token_sort_ratio` fuzzy match (RapidFuzz, threshold 90) → embedding dot-product (threshold 0.82); rows with <2 companies are dropped |
| `Corplink/step_ai_autofill.py` | Batches 30 items/call to GPT-4o-mini; maps products to parent companies (e.g., ChatGPT→OpenAI); excludes press wires (Reuters, Bloomberg); saves API key to `.openai_key` |
| `Corplink/step_standardize.py` | Writes to MySQL (`ban_list`, `company_alias`, `company_canonical`); uses INSERT IGNORE + SELECT fallback for race-condition safety |
| `Corplink/step_network.py` | Generates directed permutation pairs from each sentence's company list; outputs long-format adjacency list + pivot matrix |
| `WebApp/app.py` | FastAPI server; single `server_state` dict prevents concurrent runs; re-downloads the full repo ZIP per request for sandbox isolation; streams stdout to `run.log` |
| `WebApp/index.html` | Two-tab UI: Main (extract) and Filter (industry classification); polls `/status` to update button state |

## Configuration

`config.json` is generated at runtime in the working directory and controls: MySQL URL, keyword mode, AI level, extract mode, and OpenAI key. The file's presence switches all interactive prompts off (web silent mode). The OpenAI key is also cached in `.openai_key` for CLI reuse.

## Non-obvious Design Decisions

**Global state over function arguments** — `Corplink/state.py` holds pipeline-wide data. Modifying pipeline behavior means mutating state variables, not changing function signatures.

**Embedding caching as function attributes** — `step_extract.py` stores the anchor embedding on the function object after first computation so it is not recomputed per article.

**Bad-score heuristic** — `calc_Bad_Score()` in `model_utils.py` assigns penalty points (time quantities +30, financial report terms +30, 1–2 word tokens +10, high lowercase ratio +10, semantic similarity to noise concepts +20 to +100). Zero or organic suffix → keep; high score → likely junk.

**WebApp sandbox isolation** — `app.py` re-downloads the entire repo ZIP from GitHub on every `/upload` request and runs the pipeline inside a temp directory. This ensures the web server always runs the latest code without a redeploy.

**MySQL as learning cache** — every resolved company alias and ban-list entry persists in MySQL, so repeated runs on similar corpora get cheaper and more accurate over time.

## Dependencies (must be present)

- spaCy model: `python -m spacy download en_core_web_sm`
- Sentence Transformers `all-MiniLM-L6-v2` — auto-downloaded on first use
- MySQL server reachable at the configured URL
- OpenAI API key (only required for AI level ≥ 1)

`env_bootstrap.py` handles pip packages automatically and restarts the process after installation.
