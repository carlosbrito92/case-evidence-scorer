import streamlit as st
import anthropic
import requests
import json
import re
from datetime import datetime
from urllib.parse import quote

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Case Evidence Scorer",
    page_icon="🔍",
    layout="wide",
)

# ─────────────────────────────────────────
#  STYLING
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0d0f14;
    color: #c9d1d9;
}
.stApp { background-color: #0d0f14; }

h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }

.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    color: #58a6ff;
}
.header-sub {
    font-size: 0.9rem;
    color: #6e7681;
    font-family: 'Share Tech Mono', monospace;
    margin-top: -8px;
}

.source-tag {
    display: inline-block;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: #58a6ff;
    margin: 2px;
}

.verdict-approved {
    background: #0d4429;
    border: 1px solid #2ea043;
    border-radius: 8px;
    padding: 16px;
    color: #56d364;
    font-weight: 700;
    font-size: 1.1rem;
}
.verdict-rejected {
    background: #3d1d1d;
    border: 1px solid #da3633;
    border-radius: 8px;
    padding: 16px;
    color: #f85149;
    font-weight: 700;
    font-size: 1.1rem;
}
.verdict-inconclusive {
    background: #2d2000;
    border: 1px solid #d29922;
    border-radius: 8px;
    padding: 16px;
    color: #e3b341;
    font-weight: 700;
    font-size: 1.1rem;
}

.info-block {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85rem;
}

.dork-box {
    background: #0d1117;
    border: 1px solid #30363d;
    border-left: 3px solid #58a6ff;
    border-radius: 4px;
    padding: 10px 14px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.82rem;
    color: #79c0ff;
    margin: 4px 0;
    word-break: break-all;
}

.section-title {
    font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 8px;
    border-bottom: 1px solid #21262d;
    padding-bottom: 6px;
}

.pill-link {
    display: inline-block;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #58a6ff;
    text-decoration: none;
    margin: 3px;
    font-family: 'Share Tech Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  API KEY GATE
# ─────────────────────────────────────────

def validate_api_key(key: str) -> bool:
    """Quick test call to verify the key works."""
    try:
        client = anthropic.Anthropic(api_key=key)
        client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}]
        )
        return True
    except Exception:
        return False

if "api_key_validated" not in st.session_state:
    st.session_state.api_key_validated = False
if "anthropic_api_key" not in st.session_state:
    st.session_state.anthropic_api_key = ""
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

if not st.session_state.api_key_validated:
    # Centered login screen
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div style='text-align:center; padding: 60px 0 20px 0;'>
            <div style='font-size:3rem;'>🔍</div>
            <div style='font-size:1.8rem; font-weight:800; color:#58a6ff; letter-spacing:-1px;'>Case Evidence Scorer</div>
            <div style='font-size:0.85rem; color:#6e7681; font-family:"Share Tech Mono",monospace; margin-top:6px;'>
                OSINT Investigation Assistant · Software Compliance
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("#### Enter your Anthropic API Key")
        st.caption("Your key is used only during this session and is never stored or shared.")

        key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-ant-...",
            label_visibility="collapsed"
        )

        col_btn, col_link = st.columns([2, 1])
        with col_btn:
            login_btn = st.button("🔐 Access Tool", type="primary", use_container_width=True)
        with col_link:
            st.markdown(
                "<div style='padding-top:8px; text-align:right;'>"
                "<a href='https://console.anthropic.com/settings/keys' target='_blank' "
                "style='color:#58a6ff; font-size:0.8rem;'>Get a key ↗</a></div>",
                unsafe_allow_html=True
            )

        if login_btn:
            if not key_input.startswith("sk-ant-"):
                st.error("That doesn't look like a valid Anthropic key. It should start with `sk-ant-`.")
            else:
                with st.spinner("Validating key..."):
                    if validate_api_key(key_input):
                        st.session_state.api_key_validated = True
                        st.session_state.anthropic_api_key = key_input
                        st.success("✅ Key validated! Loading tool...")
                        st.rerun()
                    else:
                        st.error("❌ Key invalid or expired. Please check and try again.")

        st.markdown("---")
        st.markdown(
            "<div style='text-align:center; font-size:0.75rem; color:#6e7681;'>"
            "Each investigation uses approx. <b style='color:#c9d1d9'>$0.01</b> of API credits · "
            "All OSINT sources are public and verifiable</div>",
            unsafe_allow_html=True
        )
    st.stop()

# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
st.markdown('<div class="header-title">🔍 Case Evidence Scorer</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">OSINT Investigation Assistant · All sources verifiable · No hallucinated data</div>', unsafe_allow_html=True)

# Logout option in sidebar
with st.sidebar:
    st.markdown("---")
    st.caption(f"🔑 Key: `...{st.session_state.anthropic_api_key[-6:]}`")
    if st.button("🚪 Logout / Change Key", use_container_width=True):
        st.session_state.api_key_validated = False
        st.session_state.anthropic_api_key = ""
        st.rerun()
    st.markdown("---")

st.markdown("---")

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def clean_cnpj(raw: str) -> str:
    """Strip formatting from CNPJ string."""
    return re.sub(r'\D', '', raw)

def lookup_cnpj(cnpj_raw: str) -> dict:
    """
    Query ReceitaWS public API (no auth required).
    Returns dict with company data or error.
    Source: https://receitaws.com.br/v1/cnpj/{cnpj}
    """
    cnpj = clean_cnpj(cnpj_raw)
    if len(cnpj) != 14:
        return {"error": "CNPJ must have 14 digits."}
    url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
    try:
        resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        if resp.status_code == 200:
            data = resp.json()
            data["_source_url"] = url
            data["_verified"] = True
            return data
        else:
            return {"error": f"HTTP {resp.status_code}", "_source_url": url, "_verified": False}
    except Exception as e:
        return {"error": str(e), "_source_url": url, "_verified": False}

def lookup_whois(domain: str) -> dict:
    """
    Query WHOIS data via whoisjson.com public API (no auth required).
    Source: https://whoisjson.com/api/v1/whois?domain={domain}
    """
    url = f"https://whoisjson.com/api/v1/whois?domain={domain}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            data["_source_url"] = url
            data["_verified"] = True
            return data
        else:
            return {"error": f"HTTP {resp.status_code}", "_source_url": url, "_verified": False}
    except Exception as e:
        return {"error": str(e), "_source_url": url, "_verified": False}

def generate_dorks(domain: str, company_name: str, hostname: str, username: str, additional_emails: str) -> list:
    """Generate Google Dork queries based on machine data."""
    dorks = []
    if domain:
        dorks.append((f'site:{domain}', f"https://www.google.com/search?q=site:{quote(domain)}"))
        dorks.append((f'"{domain}" filetype:pdf OR filetype:docx', f"https://www.google.com/search?q=%22{quote(domain)}%22+filetype%3Apdf+OR+filetype%3Adocx"))
    if company_name:
        dorks.append((f'"{company_name}" CNPJ', f"https://www.google.com/search?q=%22{quote(company_name)}%22+CNPJ"))
        dorks.append((f'"{company_name}" site:linkedin.com', f"https://www.google.com/search?q=%22{quote(company_name)}%22+site%3Alinkedin.com"))
        dorks.append((f'"{company_name}" site:facebook.com OR site:instagram.com', f"https://www.google.com/search?q=%22{quote(company_name)}%22+site%3Afacebook.com+OR+site%3Ainstagram.com"))
    if hostname:
        dorks.append((f'"{hostname}"', f"https://www.google.com/search?q=%22{quote(hostname)}%22"))
    if username:
        dorks.append((f'"{username}" site:linkedin.com', f"https://www.google.com/search?q=%22{quote(username)}%22+site%3Alinkedin.com"))
    if additional_emails:
        for email in additional_emails.split('\n'):
            email = email.strip()
            if email:
                dorks.append((f'"{email}"', f"https://www.google.com/search?q=%22{quote(email)}%22"))
    return dorks

def build_quick_links(domain: str, cnpj_raw: str) -> list:
    """Generate direct verification links for external databases."""
    links = []
    if domain:
        links.append(("WhoIs Registro.br", f"https://registro.br/tecnologia/ferramentas/whois/?search={domain}"))
        links.append(("Wayback Machine", f"https://web.archive.org/web/*/{domain}"))
        links.append(("DNS Lookup", f"https://dnschecker.org/#A/{domain}"))
    if cnpj_raw:
        cnpj = clean_cnpj(cnpj_raw)
        if len(cnpj) == 14:
            links.append(("Receita Federal", f"https://www.receita.fazenda.gov.br/pessoajuridica/cnpj/cnpjreva/cnpjreva_solicitacao2.asp"))
            links.append(("Cadastro Empresa", f"https://www.cadastroempresa.com.br/empresa/{cnpj}"))
            links.append(("Casa dos Dados", f"https://casadosdados.com.br/solucao/cnpj?q={cnpj}"))
    return links

def score_with_claude(machine_data: dict, whois_data: dict, cnpj_data: dict, additional_findings: str) -> str:
    """Send all evidence to Claude and get structured verdict."""
    client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)

    system_prompt = """You are a Case Investigation Analyst specializing in software piracy (unlicensed software usage) investigations. 
Your job is to analyze OSINT evidence and determine whether a machine/entity should be APPROVED or REJECTED as a valid unlicensed software case.

IMPORTANT RULES:
1. Only use information explicitly provided to you. NEVER invent CNPJs, domains, emails, or any identifiers.
2. Every claim you make must be traceable to a provided source.
3. If evidence is insufficient, say INCONCLUSIVE — do not guess.
4. Respond in English (the dossier language).

APPROVAL CRITERIA (a case is APPROVED when):
- Valid "Actionable Domain" (email domain) is clearly associated with a real, identifiable entity
- Recent events exist classified as "Unlicensed" (post-2022)
- Geolocation/IP/Wi-Fi signal is consistent with the entity's known address
- Corporate Hostname or Username is directly related to the company (employee/owner)

REJECTION CRITERIA (a case is REJECTED when any of these apply):
- Last event timestamp is older than required (before 2022)
- Email domain / Computer domain do not match the entity
- Last events are classified as Commercial, Evaluation, or Personal (not Unlicensed)

RESPONSE FORMAT (always use this exact structure):
---VERDICT---
[APPROVED / REJECTED / INCONCLUSIVE]

---CONFIDENCE---
[HIGH / MEDIUM / LOW]

---REASONS---
[List each reason in bullet points, matching the standard format used in dossiers]

---MISSING_EVIDENCE---
[What specific information would be needed to move from INCONCLUSIVE to APPROVED, if applicable]

---ANALYST_NOTES---
[Additional observations, inconsistencies, or flags for the QA team]
---"""

    user_message = f"""Please analyze the following case evidence:

## MACHINE DATA (from platform):
{json.dumps(machine_data, indent=2, ensure_ascii=False)}

## WHOIS LOOKUP RESULT (source: {whois_data.get('_source_url', 'N/A')} | verified: {whois_data.get('_verified', False)}):
{json.dumps({k: v for k, v in whois_data.items() if not k.startswith('_')}, indent=2, ensure_ascii=False)}

## CNPJ LOOKUP RESULT (source: {cnpj_data.get('_source_url', 'ReceitaWS')} | verified: {cnpj_data.get('_verified', False)}):
{json.dumps({k: v for k, v in cnpj_data.items() if not k.startswith('_')}, indent=2, ensure_ascii=False)}

## ADDITIONAL FINDINGS (manually gathered by investigator):
{additional_findings if additional_findings else "No additional findings provided."}

Analyze the evidence and provide your verdict following the exact format specified.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text

def parse_verdict(raw: str) -> dict:
    """Parse Claude's structured response into components."""
    sections = {}
    patterns = {
        "verdict": r"---VERDICT---\s*(.*?)\s*(?=---|$)",
        "confidence": r"---CONFIDENCE---\s*(.*?)\s*(?=---|$)",
        "reasons": r"---REASONS---\s*(.*?)\s*(?=---|$)",
        "missing": r"---MISSING_EVIDENCE---\s*(.*?)\s*(?=---|$)",
        "notes": r"---ANALYST_NOTES---\s*(.*?)\s*(?=---|$)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, raw, re.DOTALL)
        sections[key] = match.group(1).strip() if match else ""
    return sections

# ─────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-title">📥 Machine Data Input</div>', unsafe_allow_html=True)

    v = st.session_state.form_version  # shorthand for keying widgets

    with st.expander("**Machine IDs & Status**", expanded=True):
        machine_id = st.text_input("Machine ID", placeholder="e.g. 81300160", key=f"machine_id_{v}")
        event_classification = st.selectbox(
            "Last Event Classification",
            ["Unlicensed", "Commercial", "Evaluation", "Personal", "Unknown"],
            key=f"event_class_{v}"
        )
        last_event_date = st.date_input("Last Event Date", key=f"last_event_{v}")

    with st.expander("**Network & Identity Data**", expanded=True):
        email_domain = st.text_input("Email / Actionable Domain", placeholder="e.g. palaciopontoalto.com.br", key=f"domain_{v}")
        ip_location = st.text_input("IP Location (city, state)", placeholder="e.g. Ituiutaba, MG", key=f"ip_{v}")
        wifi_location = st.text_input("Wi-Fi Location (city, state)", placeholder="e.g. Ituiutaba, MG", key=f"wifi_{v}")
        hostname = st.text_input("Hostname", placeholder="e.g. PALACIO-PC01", key=f"hostname_{v}")
        username = st.text_input("Username", placeholder="e.g. giseli.lima", key=f"username_{v}")
        additional_emails = st.text_area("Additional Email Addresses (one per line)", height=80,
                                          placeholder="bruna@palaciopontoalto.com.br\ncontato@example.com.br",
                                          key=f"add_emails_{v}")

    with st.expander("**Entity Identifiers (optional, for auto-lookup)**"):
        cnpj_input = st.text_input("CNPJ (will be auto-verified via ReceitaWS)", placeholder="00.000.000/0001-00", key=f"cnpj_{v}")
        company_name_hint = st.text_input("Company name hint (for Google Dorks)", placeholder="Palácio Ponto Alto Eventos", key=f"company_{v}")

    st.markdown('<div class="section-title" style="margin-top:20px;">📝 Additional Findings</div>', unsafe_allow_html=True)

    # Social media links field (new — feeds into .txt export)
    social_media_links = st.text_area(
        "Social Media Links (one per line)",
        height=80,
        placeholder="https://www.instagram.com/palaciopontoaltoeventos/\nhttps://www.facebook.com/palaciopontoaltoeventos/",
        key=f"social_{v}"
    )

    additional_findings = st.text_area(
        "Additional OSINT Findings (LinkedIn, Wayback, notes, etc.)",
        height=120,
        placeholder="e.g.\n- Wayback confirms site active since 2018\n- Facebook page shows same address as CNPJ registry...",
        key=f"findings_{v}"
    )

    col_run, col_new = st.columns([3, 1])
    with col_run:
        run_btn = st.button("🔎 Run Investigation", type="primary", use_container_width=True)
    with col_new:
        new_case_btn = st.button("🗑️ New Case", use_container_width=True)

    if new_case_btn:
        st.session_state.form_version += 1
        st.rerun()

# ─────────────────────────────────────────
#  RESULTS PANEL
# ─────────────────────────────────────────

with col_right:
    st.markdown('<div class="section-title">🔗 Quick Verification Links</div>', unsafe_allow_html=True)

    quick_links = build_quick_links(email_domain, cnpj_input)
    if quick_links:
        links_html = "".join([f'<a class="pill-link" href="{url}" target="_blank">↗ {label}</a>' for label, url in quick_links])
        st.markdown(links_html, unsafe_allow_html=True)
    else:
        st.caption("Enter a domain or CNPJ above to generate verification links.")

    st.markdown('<div class="section-title" style="margin-top:20px;">🕵️ Google Dork Queries</div>', unsafe_allow_html=True)
    dorks = generate_dorks(email_domain, company_name_hint, hostname, username, additional_emails)
    if dorks:
        for query, url in dorks:
            st.markdown(f'<div class="dork-box"><a href="{url}" target="_blank" style="color:#79c0ff;text-decoration:none;">{query} ↗</a></div>', unsafe_allow_html=True)
    else:
        st.caption("Fill in machine data to generate dork queries.")

    st.markdown("---")
    results_placeholder = st.empty()

# ─────────────────────────────────────────
#  RUN INVESTIGATION
# ─────────────────────────────────────────

if run_btn:
    if not email_domain:
        st.error("Please enter at least the Email / Actionable Domain.")
    else:
        with results_placeholder.container():
            st.markdown('<div class="section-title">⏳ Running Lookups...</div>', unsafe_allow_html=True)

            # 1. WHOIS
            whois_status = st.status("Looking up WHOIS...", expanded=False)
            whois_data = lookup_whois(email_domain)
            if whois_data.get("_verified"):
                whois_status.update(label=f"✅ WHOIS lookup complete", state="complete")
            else:
                whois_status.update(label=f"⚠️ WHOIS lookup failed: {whois_data.get('error')}", state="error")

            # 2. CNPJ
            cnpj_data = {}
            if cnpj_input:
                cnpj_status = st.status("Looking up CNPJ via ReceitaWS...", expanded=False)
                cnpj_data = lookup_cnpj(cnpj_input)
                if cnpj_data.get("_verified"):
                    cnpj_status.update(label=f"✅ CNPJ verified: {cnpj_data.get('nome', 'OK')}", state="complete")
                else:
                    cnpj_status.update(label=f"⚠️ CNPJ not found or invalid: {cnpj_data.get('error')}", state="error")
            else:
                cnpj_data = {"_verified": False, "_source_url": "N/A", "note": "No CNPJ provided"}

            # 3. Build machine data dict
            machine_data = {
                "machine_id": machine_id,
                "event_classification": event_classification,
                "last_event_date": str(last_event_date),
                "email_domain": email_domain,
                "ip_location": ip_location,
                "wifi_location": wifi_location,
                "hostname": hostname,
                "username": username,
                "additional_emails": additional_emails,
            }

            # 4. Claude Analysis
            claude_status = st.status("Analyzing evidence with Claude...", expanded=False)
            try:
                raw_verdict = score_with_claude(machine_data, whois_data, cnpj_data, additional_findings)
                parsed = parse_verdict(raw_verdict)
                claude_status.update(label="✅ Analysis complete", state="complete")

                verdict = parsed.get("verdict", "INCONCLUSIVE").strip().upper()
                confidence = parsed.get("confidence", "LOW").strip().upper()

                st.markdown("---")
                st.markdown('<div class="section-title">📋 Investigation Result</div>', unsafe_allow_html=True)

                # Verdict badge
                css_class = {
                    "APPROVED": "verdict-approved",
                    "REJECTED": "verdict-rejected",
                }.get(verdict, "verdict-inconclusive")
                icon = {"APPROVED": "✅", "REJECTED": "❌"}.get(verdict, "⚠️")
                st.markdown(f'<div class="{css_class}">{icon} {verdict} &nbsp;|&nbsp; Confidence: {confidence}</div>', unsafe_allow_html=True)

                # Reasons
                if parsed.get("reasons"):
                    st.markdown("**Reasons:**")
                    st.markdown(parsed["reasons"])

                # Missing evidence
                if parsed.get("missing") and verdict == "INCONCLUSIVE":
                    st.markdown("**Missing Evidence:**")
                    st.info(parsed["missing"])

                # Analyst notes
                if parsed.get("notes"):
                    with st.expander("🔍 Analyst Notes (for QA)"):
                        st.markdown(parsed["notes"])

                # Source transparency
                st.markdown("---")
                st.markdown('<div class="section-title">🔐 Source Transparency Log</div>', unsafe_allow_html=True)
                st.markdown(f"""
<div class="info-block">
<span class="source-tag">WHOIS</span> <a href="{whois_data.get('_source_url', '#')}" target="_blank" style="color:#58a6ff">{whois_data.get('_source_url', 'N/A')}</a> | Verified: {whois_data.get('_verified', False)}<br>
<span class="source-tag">CNPJ</span> <a href="{cnpj_data.get('_source_url', '#')}" target="_blank" style="color:#58a6ff">{cnpj_data.get('_source_url', 'N/A')}</a> | Verified: {cnpj_data.get('_verified', False)}<br>
<span class="source-tag">Generated</span> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
</div>
""", unsafe_allow_html=True)

                # Raw output for Gemini handoff
                with st.expander("📄 Raw Claude Output (for Gemini dossier generation)"):
                    st.code(raw_verdict, language="markdown")

                # TXT Export
                st.markdown("---")
                st.markdown('<div class="section-title">💾 Export</div>', unsafe_allow_html=True)

                # Extract CNPJ fields from verified data
                cnpj_legal_name   = cnpj_data.get("nome", "N/A")
                cnpj_fantasy_name = cnpj_data.get("fantasia", "N/A")
                cnpj_address      = ", ".join(filter(None, [
                    cnpj_data.get("logradouro"), cnpj_data.get("numero"),
                    cnpj_data.get("bairro"), cnpj_data.get("municipio"),
                    cnpj_data.get("uf"), cnpj_data.get("cep")
                ])) or "N/A"
                cnpj_email        = cnpj_data.get("email", "N/A")
                cnpj_phone        = cnpj_data.get("telefone", "N/A")
                cnpj_status       = cnpj_data.get("situacao", "N/A")
                cnpj_partners     = cnpj_data.get("qsa", [])
                cnpj_partner_str  = ", ".join(
                    [p.get("nome", "") for p in cnpj_partners]
                ) if cnpj_partners else "N/A"
                cnpj_source_url   = cnpj_data.get("_source_url", "N/A")

                # Extract WHOIS fields
                whois_registrant  = (
                    whois_data.get("registrant_name") or
                    whois_data.get("owner") or
                    whois_data.get("registrant", {}).get("name", "N/A")
                    if isinstance(whois_data.get("registrant"), dict)
                    else whois_data.get("registrant", "N/A")
                )
                whois_contact     = (
                    whois_data.get("registrant_email") or
                    whois_data.get("emails") or
                    "N/A"
                )
                if isinstance(whois_contact, list):
                    whois_contact = ", ".join(whois_contact)
                whois_source_url  = whois_data.get("_source_url", "N/A")

                export_lines = [
                    f"the new investigation is {email_domain}",
                    "",
                    f"here's the whois results: {whois_source_url}",
                    f"Titular Name    : {whois_registrant}",
                    f"Titular Contact : {whois_contact}",
                    "",
                    "company social media links:",
                ]

                if social_media_links.strip():
                    for link in social_media_links.strip().split("\n"):
                        export_lines.append(f"  {link.strip()}")
                else:
                    export_lines.append("  N/A")

                export_lines += [
                    "",
                    f"corporate taxpayer ID information: {cnpj_source_url}",
                    f"Legal Name      : {cnpj_legal_name}",
                    f"Fantasy Name    : {cnpj_fantasy_name}",
                    f"Address         : {cnpj_address}",
                    f"Email           : {cnpj_email}",
                    f"Contact Phone   : {cnpj_phone}",
                    f"Managing Partner: {cnpj_partner_str}",
                    f"Status          : {cnpj_status}",
                    "",
                ]

                if additional_findings.strip():
                    export_lines += [
                        "additional findings:",
                        additional_findings.strip(),
                        "",
                    ]

                export_lines += [
                    "--- VERDICT ---",
                    f"{verdict} | Confidence: {confidence}",
                    "",
                    "--- REASONS ---",
                    parsed.get("reasons", "N/A"),
                ]

                if parsed.get("notes"):
                    export_lines += [
                        "",
                        "--- ANALYST NOTES ---",
                        parsed["notes"],
                    ]

                export_txt = "\n".join(export_lines)
                filename = f"case_{machine_id or 'unknown'}_{email_domain}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"

                st.download_button(
                    label="⬇️ Download .txt report",
                    data=export_txt,
                    file_name=filename,
                    mime="text/plain",
                    use_container_width=True,
                )

            except Exception as e:
                claude_status.update(label=f"❌ Claude error: {e}", state="error")
                st.error(f"Claude API error: {e}")
