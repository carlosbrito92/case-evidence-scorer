# 🔍 Case Evidence Scorer

> OSINT Investigation Assistant for Software Compliance Cases  
> Built with Python · Streamlit · Claude API

---

## What This Does

A browser-based investigation assistant that helps analysts determine whether a machine case should be **APPROVED** or **REJECTED** in software piracy investigations.

Instead of manually searching multiple databases and trying to mentally connect the dots, the tool:

1. **Auto-queries WHOIS** for the actionable domain (via public API — no auth needed)
2. **Auto-verifies CNPJ** against Brazil's ReceitaWS public database
3. **Searches the web autonomously** (via Claude's web search) for social media handles, email addresses, and public presence tied to the domain and usernames
4. **Generates Google Dork queries** based on machine data (hostname, username, domain, emails)
5. **Generates direct links** to Receita Federal, Casa dos Dados, Cadastro Empresa, Wayback Machine
6. **Sends all evidence to Claude** for structured analysis
7. **Returns a verdict** (APPROVED / REJECTED / INCONCLUSIVE) with confidence score and reasons
8. **Logs every source** with its URL so any finding can be independently replicated
9. **Exports a structured .txt report** ready to be pasted into Gemini for dossier generation

---

## Why Source Transparency Matters

All evidence produced by this tool is traceable to a public, verifiable URL.  
No AI-generated CNPJs. No hallucinated domains. No invented data.

This is critical for legal defensibility: any finding can be reproduced by a third party (QA, legal team, client) without access to any internal system.

---

## Features

### 🔐 API Key Login Screen
Each user enters their own Anthropic API key on first access. The key is used only for that session and never stored. A quick validation call confirms the key works before granting access.

### 📊 Real-Time Usage Counter
A live counter in the sidebar tracks — per session:
- Number of investigations run
- Input and output tokens consumed
- Estimated cost in USD (based on Claude Sonnet pricing)

Each individual investigation also shows its token count and cost in the status bar after completing.

### ☑️ "Mark as Absent" Fields
Fields that may not always be available (IP location, Wi-Fi location, hostname, username, additional emails) each have a **Mark as absent** checkbox. When checked, the field is replaced with an "Information Absent" indicator and Claude is instructed not to penalize the case for missing data.

### 🔢 Multiple Values per Field
Machine IDs, Hostnames, and Usernames now accept multiple values separated by a comma and space. Claude evaluates each Machine ID individually when event classifications differ across machines.

### 📍 IP and Wi-Fi Location as Coordinates
IP Location and Wi-Fi Location fields accept **latitude, longitude coordinates** (e.g. `-18.9186, -48.2772`) instead of city names, allowing for more precise geolocation matching against the entity's registered address.

### 🤖 Claude Searches Autonomously
Claude has web search enabled during each investigation. Before issuing a verdict, it actively searches for:
- Social media profiles tied to the actionable domain
- Public profiles for listed usernames
- Contact or company info tied to additional email addresses

Results appear in a dedicated **Social Media Found by Claude** section and are automatically included in the exported .txt.

### 💾 Structured .txt Export
The exported report follows a fixed format ready for Gemini dossier generation:

```
the new investigation is [domain]

here's the whois results: [source URL]
Titular Name    : ...
Titular Contact : ...

company social media links:
  [links found manually + by Claude, deduplicated]

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

### 🗑️ New Case Button
Clears all form fields instantly without reloading the page, ready for the next investigation.

---

## Stack

| Component | Technology |
|---|---|
| Interface | Streamlit |
| AI Analysis | Anthropic Claude API (claude-sonnet) |
| Web Search | Claude web_search tool (built-in) |
| CNPJ Verification | ReceitaWS public API |
| WHOIS Lookup | WhoisJSON public API |
| Language | Python 3.10+ |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/carlosbrito92/case-evidence-scorer.git
cd case-evidence-scorer
pip install -r requirements.txt
```

### 2. Run

```bash
streamlit run app.py
```

The login screen will prompt for your Anthropic API key. No `.env` file needed.

---

## Workflow

```
Enter machine data (domain, IPs, hostnames, usernames, emails)
  ↓ mark unavailable fields as "absent"
Auto-runs: WHOIS + CNPJ lookup
  ↓
Claude searches the web for social media + public presence
  ↓
Generates: Google Dork queries + verification links
  ↓
You investigate manually using the generated queries
  ↓
Paste additional findings into the form
  ↓
Claude analyzes all evidence
  ↓
Output: APPROVED / REJECTED / INCONCLUSIVE
        + Confidence + Reasons + Social media found + Source log
  ↓
Download .txt → paste into Gemini → generate final dossier
```

---

## Approval / Rejection Criteria

**APPROVED** when:
- Valid actionable domain associated with a real, identifiable entity
- Recent events classified as "Unlicensed" (post-2022)
- Geolocation coordinates consistent with the entity's registered address
- Hostname or username directly linked to the company

**REJECTED** when (any one is sufficient):
- Last event older than required (before 2022)
- Email domain / computer domain mismatch
- Last events classified as Commercial, Evaluation, or Personal

---

## Roadmap

- [ ] Auto-scrape LinkedIn company page (name, address, headcount)
- [ ] Hunter.io / Apollo.io free API integration for contact discovery
- [ ] Export verdict directly to dossier-ready `.docx`
- [ ] Batch processing: run multiple machine IDs at once
- [ ] Case history log (SQLite)

---

## Changelog

### v1.1.0
- Added real-time API usage counter (tokens + estimated cost) in sidebar
- Added "Mark as absent" checkbox for IP, Wi-Fi, hostname, username, and email fields
- IP and Wi-Fi location fields now accept coordinates (latitude, longitude)
- Machine IDs, hostnames, and usernames now support multiple comma-separated values
- Claude now searches the web autonomously for social media and public presence
- Social media found by Claude is merged (deduplicated) with manually entered links in the export
- .txt export now includes API usage stats per investigation
- "New Case" button clears all fields without page reload

### v1.0.0
- Initial release: WHOIS + CNPJ auto-lookup, Google Dork generation, Claude verdict, .txt export

---

## Author

Carlos Alberto · [LinkedIn](https://www.linkedin.com/in/carlos-albertobrito1992)

Built to solve a real problem in software compliance investigation.  
Part of an ongoing project documented publicly on LinkedIn.

---

## License

MIT — free to use, modify and distribute.
