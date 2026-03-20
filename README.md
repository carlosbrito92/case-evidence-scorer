# 🔍 Case Evidence Scorer

> OSINT Investigation Assistant for Software Compliance Cases  
> Built with Python · Streamlit · Claude API

---

## What This Does

A browser-based investigation assistant that helps analysts determine whether a case should be **APPROVED** or **REJECTED** in software compliance investigations.

The tool automates the most time-consuming parts of the process:

1. **Auto-queries WHOIS** for the actionable domain (public API — no auth needed)
2. **Auto-verifies corporate registration** against Brazil's ReceitaWS public database
3. **Cross-correlates all evidence internally** — a data point is only accepted if confirmed by at least one independent source
4. **Identifies probable identity matches** across partial names, email handles, and usernames
5. **Validates domain ownership** — flags generic/shared domains (Gmail, Outlook, etc.) that cannot be legally attributed to the entity
6. **Generates Google Dork queries** and direct verification links
7. **Returns a structured verdict** (APPROVED / REJECTED / INCONCLUSIVE) with confidence score, corroboration map, and reasons
8. **Exports a structured .txt report** ready for dossier generation

---

## Why Source Transparency Matters

All evidence is traceable to a public, verifiable URL. No AI-generated registration numbers, no hallucinated domains, no invented data.

This is critical for legal defensibility: any finding can be reproduced by a third party (QA, legal team, client) without access to any internal system.

---

## Features

### 🔐 API Key Login Screen
Each user enters their own Anthropic API key on first access. Used only during that session, never stored.

### 📊 Real-Time Usage Counter
Tracks per session: number of investigations, input/output tokens, and estimated cost in USD. Each investigation also shows its individual cost in the status bar.

### ⚙️ Web Search Toggle
A sidebar toggle switches between two analysis modes:
- **Internal only** (~$0.02/case) — Claude cross-correlates the provided data with no external calls
- **Web search on** (~$0.15–0.25/case) — Claude actively searches for social media profiles and public presence

### ☑️ "Mark as Absent" Fields
Fields that may not always be available (IP location, Wi-Fi location, hostname, username, emails) each have a **Mark as absent** checkbox. Claude is instructed not to penalize the case for unavailable data.

### 🔢 Multiple Values per Field
Entity IDs, hostnames, and usernames accept multiple comma-separated values. Claude evaluates each one individually when event classifications differ.

### 📍 Location as Coordinates
IP Location and Wi-Fi Location fields accept **latitude, longitude coordinates** for precise geolocation matching against the entity's registered address.

### 🧠 Internal Cross-Correlation Engine
Claude applies structured reasoning to every data point:

- **Name token matching** — splits names into individual tokens and compares them across all sources (WHOIS registrant, corporate registry partners, usernames, email handles, investigator notes)
- **Email handle decoding** — decodes compressed email handles into name fragments (e.g. `anamartenicodemos` → `[ana][marte][nicodemos]`) and cross-references each fragment against known names
- **Probable identity matching** — when 2+ tokens overlap across independent sources, flags as PROBABLE MATCH with full reasoning chain
- **Domain validation** — generic/shared email providers are flagged and rejected unless publicly corroborated
- **Email usage restriction** — additional case emails are used only for name corroboration, never as contact evidence

### 📋 Approval / Rejection Logic

**APPROVED** when all of:
- Actionable domain is proprietary (entity-owned), or generic domain publicly corroborated
- At least one verifiable contact method exists: phone number OR official email
- Recent unlicensed events (post-2022)
- Geolocation consistent with registered address
- Identity corroborated or probably matched

**Exception**: entity with no corporate registration but active, verifiable social media presence may still be approved if all other criteria are met.

**REJECTED** when any one of:
- Last event before 2022
- Domain/computer domain mismatch
- Events classified as Commercial, Evaluation, or Personal
- Generic domain with no public corroboration
- No verifiable phone number AND no verifiable official email

### 💾 Structured .txt Export

```
the new investigation is [domain]

here's the whois results: [source URL]
Titular Name    : ...
Titular Contact : ...

company website: [official URL or database link if no site found]

company social media links:
  ...

corporate taxpayer ID information: [source URL]
Legal Name      : ...
Fantasy Name    : ...
Address         : ...
Email           : ...
Contact Phone   : ...
Managing Partner: ...
Status          : ...

--- VERDICT ---
--- REASONS ---
--- ANALYST NOTES ---
--- API USAGE ---
```

If no official website or social media is found, the company website field defaults to the database source URL (Cadastro Empresa, Casa dos Dados, etc.) where the entity was located.

### 🗑️ New Case Button
Clears all fields instantly without reloading the page.

---

## Stack

| Component | Technology |
|---|---|
| Interface | Streamlit |
| AI Analysis | Anthropic Claude API (claude-sonnet) |
| Web Search (optional) | Claude web_search tool |
| Corporate Registry | ReceitaWS public API |
| WHOIS Lookup | WhoisJSON public API |
| Language | Python 3.10+ |

---

## Setup

```bash
git clone https://github.com/carlosbrito92/case-evidence-scorer.git
cd case-evidence-scorer
pip install -r requirements.txt
streamlit run app.py
```

The login screen will prompt for your Anthropic API key. No `.env` file needed.

---

## Workflow

```
Enter case data (domain, coordinates, hostnames, usernames, emails)
  ↓ mark unavailable fields as "absent"
Auto-runs: WHOIS + corporate registry lookup
  ↓
Choose analysis mode: internal only OR web search
  ↓
Claude cross-correlates all evidence, decodes names, validates domain
  ↓
Paste additional OSINT findings into the form
  ↓
Output: APPROVED / REJECTED / INCONCLUSIVE
        + Corroboration map + Reasons + Source log
  ↓
Download .txt → paste into Gemini → generate final dossier
```

---

## Roadmap

- [ ] ipinfo.io integration (IP address → real city coordinates)
- [ ] Hunter.io free tier for additional email validation
- [ ] Case history log (SQLite)
- [ ] Multi-user login with shared API key
- [ ] Export to `.docx` dossier format
- [ ] Batch processing for multiple cases

---

## Changelog

### v1.2.0
- Added web search On/Off toggle in sidebar (internal analysis vs. web-assisted)
- Added domain validation: generic/shared domains (Gmail, Outlook, etc.) flagged and lean toward rejection unless publicly corroborated
- Added rejection criterion: entity with no verifiable phone AND no verifiable email → REJECTED
- Added approval exception: no corporate registration but active verifiable social media → may still be APPROVED
- Added "Company Website" field; defaults to database source URL if no site or social media found
- Additional case emails now explicitly restricted to name corroboration only (documented in system prompt and analyst notes)
- Last event date field changed to year-only selector (only relevant granularity for investigators)
- Updated README: removed internal platform terminology, added full approval/rejection logic

### v1.1.0
- Added real-time API usage counter (tokens + estimated cost) in sidebar
- Added "Mark as absent" checkbox for optional fields
- IP and Wi-Fi location fields now accept coordinates (latitude, longitude)
- Entity IDs, hostnames, and usernames now support multiple comma-separated values
- Added name token correlation and email handle decoding to investigation logic
- "New Case" button clears all fields without page reload

### v1.0.0
- Initial release: WHOIS + corporate registry auto-lookup, Google Dork generation, Claude verdict, .txt export

---

## Author

Carlos Alberto · [LinkedIn](https://www.linkedin.com/in/carlos-albertobrito1992)

Built to solve a real problem in software compliance investigation.  
Part of an ongoing project documented publicly on LinkedIn.

---

## License

MIT — free to use, modify and distribute.
