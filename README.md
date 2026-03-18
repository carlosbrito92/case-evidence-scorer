# 🔍 Case Evidence Scorer

> OSINT Investigation Assistant for Software Compliance Cases  
> Built with Python · Streamlit · Claude API

---

## What This Does

A local investigation assistant that helps analysts determine whether a machine case should be **APPROVED** or **REJECTED** in software piracy investigations.

Instead of manually searching multiple databases and trying to mentally connect the dots, the tool:

1. **Auto-queries WHOIS** for the actionable domain (via public API — no auth needed)
2. **Auto-verifies CNPJ** against Brazil's ReceitaWS public database
3. **Generates Google Dork queries** based on machine data (hostname, username, domain, emails)
4. **Generates direct links** to Receita Federal, Casa dos Dados, Cadastro Empresa, Wayback Machine
5. **Sends all evidence to Claude** for structured analysis
6. **Returns a verdict** (APPROVED / REJECTED / INCONCLUSIVE) with confidence score and reasons
7. **Logs every source** with its URL so any finding can be independently replicated

---

## Why Source Transparency Matters

All evidence produced by this tool is traceable to a public, verifiable URL.  
No AI-generated CNPJs. No hallucinated domains. No invented data.

This is critical for legal defensibility: any finding can be reproduced by a third party (QA, legal team, client) without access to any internal system.

---

## Stack

| Component | Technology |
|---|---|
| Interface | Streamlit |
| AI Analysis | Anthropic Claude API (claude-sonnet) |
| CNPJ Verification | ReceitaWS public API |
| WHOIS Lookup | WhoisJSON public API |
| Language | Python 3.10+ |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/case-evidence-scorer.git
cd case-evidence-scorer
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Or create a `.env` file (and add it to `.gitignore`):

```
ANTHROPIC_API_KEY=your-key-here
```

### 3. Run

```bash
streamlit run app.py
```

---

## Workflow

```
Input machine data (domain, IP, hostname, username, emails)
          ↓
Auto-runs: WHOIS + CNPJ lookup
          ↓
Generates: Google Dork queries + verification links
          ↓
You investigate manually using the generated queries
          ↓
Paste your findings into "Additional Findings"
          ↓
Claude analyzes all evidence
          ↓
Output: APPROVED / REJECTED / INCONCLUSIVE
        + Confidence level + Reasons + Source log
```

---

## Approval / Rejection Criteria

**APPROVED** when:
- Valid actionable domain associated with a real, identifiable entity
- Recent events based on the current year
- Geolocation / IP / Wi-Fi consistent with entity address
- Hostname or username directly linked to the company or partner/employee

**REJECTED** when:
- Email domain / computer domain mismatch


---

## Roadmap

- [ ] Auto-scrape LinkedIn company page (name, address, headcount)
- [ ] Hunter.io / Apollo.io free API integration for contact discovery
- [ ] Export verdict directly to dossier-ready `.txt`
- [ ] Batch processing: run multiple machine IDs at once
- [ ] Case history log (SQLite)

---

## Author

Carlos Alberto · [LinkedIn](https://www.linkedin.com/in/carlos-albertobrito1992)

Built to solve a real problem in software compliance investigation.  
Part of an ongoing project documented publicly on LinkedIn.

---

## License

MIT — free to use, modify and distribute.
