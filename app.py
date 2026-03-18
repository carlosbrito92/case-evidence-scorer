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
    font-size: 2.2rem; font-weight: 800;
    letter-spacing: -1px; color: #58a6ff;
}
.header-sub {
    font-size: 0.9rem; color: #6e7681;
    font-family: 'Share Tech Mono', monospace; margin-top: -8px;
}
.source-tag {
    display: inline-block; background: #161b22;
    border: 1px solid #30363d; border-radius: 4px;
    padding: 2px 8px; font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem; color: #58a6ff; margin: 2px;
}
.verdict-approved {
    background: #0d4429; border: 1px solid #2ea043;
    border-radius: 8px; padding: 16px; color: #56d364;
    font-weight: 700; font-size: 1.1rem;
}
.verdict-rejected {
    background: #3d1d1d; border: 1px solid #da3633;
    border-radius: 8px; padding: 16px; color: #f85149;
    font-weight: 700; font-size: 1.1rem;
}
.verdict-inconclusive {
    background: #2d2000; border: 1px solid #d29922;
    border-radius: 8px; padding: 16px; color: #e3b341;
    font-weight: 700; font-size: 1.1rem;
}
.info-block {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 16px; margin: 8px 0;
    font-family: 'Share Tech Mono', monospace; font-size: 0.85rem;
}
.dork-box {
    background: #0d1117; border: 1px solid #30363d;
    border-left: 3px solid #58a6ff; border-radius: 4px;
    padding: 10px 14px; font-family: 'Share Tech Mono', monospace;
    font-size: 0.82rem; color: #79c0ff; margin: 4px 0; word-break: break-all;
}
.section-title {
    font-size: 0.75rem; font-family: 'Share Tech Mono', monospace;
    color: #6e7681; text-transform: uppercase; letter-spacing: 2px;
    margin-bottom: 8px; border-bottom: 1px solid #21262d; padding-bottom: 6px;
}
.pill-link {
    display: inline-block; background: #1f2937; border: 1px solid #374151;
    border-radius: 20px; padding: 4px 12px; font-size: 0.78rem;
    color: #58a6ff; text-decoration: none; margin: 3px;
    font-family: 'Share Tech Mono', monospace;
}
.usage-box {
    background: #0d1117; border: 1px solid #21262d; border-radius: 6px;
    padding: 10px 14px; font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem; color: #6e7681; margin-top: 8px;
}
.absent-note {
    font-family: 'Share Tech Mono', monospace; font-size: 0.78rem;
    color: #d29922; padding: 6px 10px; background: #2d2000;
    border-radius: 4px; margin: 4px 0;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────
for key, default in {
    "api_key_validated": False,
    "anthropic_api_key": "",
    "form_version": 0,
    "session_input_tokens": 0,
    "session_output_tokens": 0,
    "session_investigations": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────
#  API KEY GATE
# ─────────────────────────────────────────

def validate_api_key(key: str) -> bool:
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

if not st.session_state.api_key_validated:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div style='text-align:center; padding:60px 0 20px 0;'>
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
        key_input = st.text_input("API Key", type="password", placeholder="sk-ant-...", label_visibility="collapsed")
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
#  HEADER + SIDEBAR
# ─────────────────────────────────────────
st.markdown('<div class="header-title">🔍 Case Evidence Scorer</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">OSINT Investigation Assistant · All sources verifiable · No hallucinated data</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("---")
    st.caption(f"🔑 Key: `...{st.session_state.anthropic_api_key[-6:]}`")

    # ── API Usage Counter ──
    st.markdown('<div class="section-title" style="margin-top:12px;">📊 Session Usage</div>', unsafe_allow_html=True)
    i_tok = st.session_state.session_input_tokens
    o_tok = st.session_state.session_output_tokens
    n_inv = st.session_state.session_investigations
    cost_usd = (i_tok * 3 + o_tok * 15) / 1_000_000
    st.markdown(f"""
<div class="usage-box">
Investigations : <b style='color:#c9d1d9'>{n_inv}</b><br>
Input tokens   : <b style='color:#c9d1d9'>{i_tok:,}</b><br>
Output tokens  : <b style='color:#c9d1d9'>{o_tok:,}</b><br>
Est. cost      : <b style='color:#56d364'>${cost_usd:.4f} USD</b>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚪 Logout / Change Key", use_container_width=True):
        st.session_state.api_key_validated = False
        st.session_state.anthropic_api_key = ""
        st.session_state.session_input_tokens = 0
        st.session_state.session_output_tokens = 0
        st.session_state.session_investigations = 0
        st.rerun()
    st.markdown("---")

st.markdown("---")

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def absent_input(label: str, key: str, placeholder: str = "", help_text: str = "") -> str:
    """Text input with an 'Information Absent' checkbox."""
    absent = st.checkbox("Mark as absent", key=f"absent_{key}", help="Check if this data is unavailable for this case")
    if absent:
        st.markdown('<div class="absent-note">⚠ Information Absent</div>', unsafe_allow_html=True)
        return "Information Absent"
    return st.text_input(label, label_visibility="collapsed", placeholder=placeholder, key=key, help=help_text)

def absent_textarea(label: str, key: str, placeholder: str = "", height: int = 70) -> str:
    """Text area with an 'Information Absent' checkbox."""
    absent = st.checkbox("Mark as absent", key=f"absent_{key}", help="Check if this data is unavailable for this case")
    if absent:
        st.markdown('<div class="absent-note">⚠ Information Absent</div>', unsafe_allow_html=True)
        return "Information Absent"
    return st.text_area(label, label_visibility="collapsed", placeholder=placeholder, key=key, height=height)

def clean_cnpj(raw: str) -> str:
    return re.sub(r'\D', '', raw)

def lookup_cnpj(cnpj_raw: str) -> dict:
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
        return {"error": f"HTTP {resp.status_code}", "_source_url": url, "_verified": False}
    except Exception as e:
        return {"error": str(e), "_source_url": url, "_verified": False}

def lookup_whois(domain: str) -> dict:
    url = f"https://whoisjson.com/api/v1/whois?domain={domain}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            data["_source_url"] = url
            data["_verified"] = True
            return data
        return {"error": f"HTTP {resp.status_code}", "_source_url": url, "_verified": False}
    except Exception as e:
        return {"error": str(e), "_source_url": url, "_verified": False}

def generate_dorks(domain: str, company_name: str, hostnames: str, usernames: str, additional_emails: str) -> list:
    dorks = []
    absent = "Information Absent"
    if domain and domain != absent:
        dorks.append((f'site:{domain}', f"https://www.google.com/search?q=site:{quote(domain)}"))
        dorks.append((f'"{domain}" filetype:pdf OR filetype:docx', f"https://www.google.com/search?q=%22{quote(domain)}%22+filetype%3Apdf"))
    if company_name:
        dorks.append((f'"{company_name}" CNPJ', f"https://www.google.com/search?q=%22{quote(company_name)}%22+CNPJ"))
        dorks.append((f'"{company_name}" site:linkedin.com', f"https://www.google.com/search?q=%22{quote(company_name)}%22+site%3Alinkedin.com"))
        dorks.append((f'"{company_name}" site:instagram.com OR site:facebook.com', f"https://www.google.com/search?q=%22{quote(company_name)}%22+site%3Ainstagram.com+OR+site%3Afacebook.com"))
    if hostnames and hostnames != absent:
        for h in [x.strip() for x in hostnames.split(",") if x.strip()]:
            dorks.append((f'"{h}"', f"https://www.google.com/search?q=%22{quote(h)}%22"))
    if usernames and usernames != absent:
        for u in [x.strip() for x in usernames.split(",") if x.strip()]:
            dorks.append((f'"{u}" site:linkedin.com', f"https://www.google.com/search?q=%22{quote(u)}%22+site%3Alinkedin.com"))
    if additional_emails and additional_emails != absent:
        for email in additional_emails.split('\n'):
            email = email.strip()
            if email:
                dorks.append((f'"{email}"', f"https://www.google.com/search?q=%22{quote(email)}%22"))
    return dorks

def build_quick_links(domain: str, cnpj_raw: str) -> list:
    links = []
    absent = "Information Absent"
    if domain and domain != absent:
        links.append(("WhoIs Registro.br", f"https://registro.br/tecnologia/ferramentas/whois/?search={domain}"))
        links.append(("Wayback Machine", f"https://web.archive.org/web/*/{domain}"))
        links.append(("DNS Lookup", f"https://dnschecker.org/#A/{domain}"))
    if cnpj_raw and cnpj_raw != absent:
        cnpj = clean_cnpj(cnpj_raw)
        if len(cnpj) == 14:
            links.append(("Cadastro Empresa", f"https://www.cadastroempresa.com.br/empresa/{cnpj}"))
            links.append(("Casa dos Dados", f"https://casadosdados.com.br/solucao/cnpj?q={cnpj}"))
    return links

def score_with_claude(machine_data: dict, whois_data: dict, cnpj_data: dict, additional_findings: str) -> tuple:
    """
    Send all evidence to Claude with web_search enabled.
    Claude will search for social media handles, email addresses, and domain info.
    Returns (text_response, usage_dict).
    """
    client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)

    domain    = machine_data.get("email_domain", "")
    usernames = machine_data.get("usernames", "")
    add_emails = machine_data.get("additional_emails", "")

    system_prompt = """You are a Case Investigation Analyst specializing in software piracy (unlicensed software usage) investigations.

Your job has two phases:
1. SEARCH PHASE — Use web search to find the entity's social media handles, email addresses, and public web presence for the actionable domain. Look for Instagram, Facebook, LinkedIn, and any other relevant profiles.
2. ANALYSIS PHASE — Analyze all gathered evidence to determine APPROVED / REJECTED / INCONCLUSIVE.

CRITICAL RULES:
- Only report information you can verify. NEVER invent CNPJs, domains, emails, or identifiers.
- Every claim must be traceable to a real, public source.
- If evidence is insufficient, say INCONCLUSIVE — do not guess.
- Respond in English.
- Fields marked "Information Absent" mean the data was not available — do not penalize the case for this.

FIELD NOTES:
- Hostname may be a generic label like "desktop-abc123" — this is normal and not inherently suspicious.
- Username often reflects the entity name, a partner, architect, or engineer. Multiple usernames may be listed.
- Multiple Machine IDs may be listed — evaluate each one's classification individually.
- IP and Wi-Fi locations are provided as coordinates (latitude, longitude).

APPROVAL CRITERIA:
- Valid "Actionable Domain" clearly associated with a real, identifiable entity
- Recent events classified as "Unlicensed" (post-2022)
- Geolocation coordinates consistent with the entity's known address
- Corporate Hostname or Username directly linked to the company

REJECTION CRITERIA (any one is sufficient):
- Last event timestamp before 2022
- Email domain / Computer domain mismatch
- Last events classified as Commercial, Evaluation, or Personal

RESPONSE FORMAT (use this exact structure):
---VERDICT---
[APPROVED / REJECTED / INCONCLUSIVE]

---CONFIDENCE---
[HIGH / MEDIUM / LOW]

---REASONS---
[Bullet points in standard dossier format]

---SOCIAL_MEDIA_FOUND---
[List social media profiles found via web search with full URLs. Write N/A if none found.]

---MISSING_EVIDENCE---
[What would be needed to move from INCONCLUSIVE to APPROVED]

---ANALYST_NOTES---
[Observations, inconsistencies, or flags for QA]
---"""

    user_message = f"""Investigate this case. Begin by searching the web for the entity's social media presence and public information tied to the domain, usernames, and email addresses below.

## MACHINE DATA:
{json.dumps(machine_data, indent=2, ensure_ascii=False)}

## WHOIS (source: {whois_data.get('_source_url','N/A')} | verified: {whois_data.get('_verified',False)}):
{json.dumps({k: v for k, v in whois_data.items() if not k.startswith('_')}, indent=2, ensure_ascii=False)}

## CNPJ (source: {cnpj_data.get('_source_url','N/A')} | verified: {cnpj_data.get('_verified',False)}):
{json.dumps({k: v for k, v in cnpj_data.items() if not k.startswith('_')}, indent=2, ensure_ascii=False)}

## ADDITIONAL FINDINGS (investigator notes):
{additional_findings if additional_findings else "None provided."}

Please search for:
- Social media handles for domain: {domain}
- Public profiles for usernames: {usernames}
- Contact info for additional emails: {add_emails}

Then provide your full verdict using the required format."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=system_prompt,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": user_message}]
    )

    # Extract all text blocks (Claude interleaves tool_use and text blocks)
    text_parts = [block.text for block in response.content if hasattr(block, "text")]
    full_text = "\n".join(text_parts)

    usage = {
        "input_tokens":  response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return full_text, usage

def parse_verdict(raw: str) -> dict:
    sections = {}
    patterns = {
        "verdict":    r"---VERDICT---\s*(.*?)\s*(?=---|$)",
        "confidence": r"---CONFIDENCE---\s*(.*?)\s*(?=---|$)",
        "reasons":    r"---REASONS---\s*(.*?)\s*(?=---|$)",
        "social":     r"---SOCIAL_MEDIA_FOUND---\s*(.*?)\s*(?=---|$)",
        "missing":    r"---MISSING_EVIDENCE---\s*(.*?)\s*(?=---|$)",
        "notes":      r"---ANALYST_NOTES---\s*(.*?)\s*(?=---|$)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, raw, re.DOTALL)
        sections[key] = match.group(1).strip() if match else ""
    return sections

# ─────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")
v = st.session_state.form_version

with col_left:
    st.markdown('<div class="section-title">📥 Machine Data Input</div>', unsafe_allow_html=True)

    with st.expander("**Machine IDs & Status**", expanded=True):
        machine_ids = st.text_input(
            "Machine ID(s)",
            placeholder="e.g. 81300160, 38890918",
            key=f"machine_id_{v}",
            help="Separate multiple IDs with a comma and space"
        )
        event_classification = st.selectbox(
            "Last Event Classification",
            ["Unlicensed", "Commercial", "Evaluation", "Personal", "Unknown"],
            key=f"event_class_{v}"
        )
        last_event_date = st.date_input("Last Event Date", key=f"last_event_{v}")

    with st.expander("**Network & Identity Data**", expanded=True):
        email_domain = st.text_input(
            "Email / Actionable Domain",
            placeholder="e.g. palaciopontoalto.com.br",
            key=f"domain_{v}"
        )

        st.markdown("**IP Location (coordinates)**")
        ip_location = absent_input(
            "IP Location", key=f"ip_{v}",
            placeholder="-18.9186, -48.2772",
            help_text="Enter as latitude, longitude (e.g. -18.9186, -48.2772)"
        )

        st.markdown("**Wi-Fi Location (coordinates)**")
        wifi_location = absent_input(
            "Wi-Fi Location", key=f"wifi_{v}",
            placeholder="-18.9186, -48.2772",
            help_text="Enter as latitude, longitude coordinates"
        )

        st.markdown("**Hostname(s)**")
        hostname = absent_input(
            "Hostname(s)", key=f"hostname_{v}",
            placeholder="e.g. PALACIO-PC01, desktop-k3x82b",
            help_text="Can be generic (desktop-abc123) or corporate. Separate multiple with comma and space."
        )

        st.markdown("**Username(s)**")
        username = absent_input(
            "Username(s)", key=f"username_{v}",
            placeholder="e.g. giseli.lima, bruna_carvalho",
            help_text="Usually the entity name, partner, architect, or engineer. Separate multiple with comma and space."
        )

        st.markdown("**Additional Email Addresses**")
        additional_emails = absent_textarea(
            "Additional Emails", key=f"add_emails_{v}",
            placeholder="bruna@palaciopontoalto.com.br\ncontato@example.com.br",
            height=70
        )

    with st.expander("**Entity Identifiers (optional, for auto-lookup)**"):
        cnpj_input = st.text_input(
            "CNPJ (auto-verified via ReceitaWS)",
            placeholder="00.000.000/0001-00",
            key=f"cnpj_{v}"
        )
        company_name_hint = st.text_input(
            "Company name hint (for Google Dorks)",
            placeholder="Palácio Ponto Alto Eventos",
            key=f"company_{v}"
        )

    st.markdown('<div class="section-title" style="margin-top:16px;">📝 Additional Findings</div>', unsafe_allow_html=True)

    social_media_links = st.text_area(
        "Social Media Links found manually (one per line)",
        height=70,
        placeholder="https://www.instagram.com/palaciopontoaltoeventos/\nhttps://www.facebook.com/palaciopontoaltoeventos/",
        key=f"social_{v}"
    )

    additional_findings = st.text_area(
        "Other OSINT Findings (Wayback, LinkedIn notes, etc.)",
        height=90,
        placeholder="- Wayback confirms site active since 2018\n- Facebook page matches CNPJ address...",
        key=f"findings_{v}"
    )

    col_run, col_new = st.columns([3, 1])
    with col_run:
        run_btn = st.button("🔎 Run Investigation", type="primary", use_container_width=True)
    with col_new:
        if st.button("🗑️ New Case", use_container_width=True):
            st.session_state.form_version += 1
            st.rerun()

# ─────────────────────────────────────────
#  RIGHT PANEL
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
    dorks = generate_dorks(
        email_domain,
        company_name_hint if 'company_name_hint' in dir() else "",
        hostname if 'hostname' in dir() else "",
        username if 'username' in dir() else "",
        additional_emails if 'additional_emails' in dir() else ""
    )
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
                whois_status.update(label="✅ WHOIS lookup complete", state="complete")
            else:
                whois_status.update(label=f"⚠️ WHOIS failed: {whois_data.get('error')}", state="error")

            # 2. CNPJ
            if cnpj_input and cnpj_input != "Information Absent":
                cnpj_status = st.status("Verifying CNPJ via ReceitaWS...", expanded=False)
                cnpj_data = lookup_cnpj(cnpj_input)
                if cnpj_data.get("_verified"):
                    cnpj_status.update(label=f"✅ CNPJ verified: {cnpj_data.get('nome','OK')}", state="complete")
                else:
                    cnpj_status.update(label=f"⚠️ CNPJ not found: {cnpj_data.get('error')}", state="error")
            else:
                cnpj_data = {"_verified": False, "_source_url": "N/A", "note": "No CNPJ provided"}

            # 3. Machine data dict
            machine_data = {
                "machine_ids":              machine_ids,
                "event_classification":     event_classification,
                "last_event_date":          str(last_event_date),
                "email_domain":             email_domain,
                "ip_location_coordinates":  ip_location,
                "wifi_location_coordinates": wifi_location,
                "hostnames":                hostname,
                "usernames":                username,
                "additional_emails":        additional_emails,
            }

            # 4. Claude (with web search)
            claude_status = st.status("🔍 Claude is investigating (web search enabled)...", expanded=False)
            try:
                raw_verdict, usage = score_with_claude(machine_data, whois_data, cnpj_data, additional_findings)
                parsed = parse_verdict(raw_verdict)

                # Update session counters
                st.session_state.session_input_tokens  += usage["input_tokens"]
                st.session_state.session_output_tokens += usage["output_tokens"]
                st.session_state.session_investigations += 1
                this_cost = (usage["input_tokens"] * 3 + usage["output_tokens"] * 15) / 1_000_000

                claude_status.update(
                    label=f"✅ Done · {usage['input_tokens']:,} in / {usage['output_tokens']:,} out · ${this_cost:.4f}",
                    state="complete"
                )

                verdict    = parsed.get("verdict", "INCONCLUSIVE").strip().upper()
                confidence = parsed.get("confidence", "LOW").strip().upper()

                st.markdown("---")
                st.markdown('<div class="section-title">📋 Investigation Result</div>', unsafe_allow_html=True)

                css_class = {"APPROVED": "verdict-approved", "REJECTED": "verdict-rejected"}.get(verdict, "verdict-inconclusive")
                icon = {"APPROVED": "✅", "REJECTED": "❌"}.get(verdict, "⚠️")
                st.markdown(f'<div class="{css_class}">{icon} {verdict} &nbsp;|&nbsp; Confidence: {confidence}</div>', unsafe_allow_html=True)

                if parsed.get("reasons"):
                    st.markdown("**Reasons:**")
                    st.markdown(parsed["reasons"])

                if parsed.get("social") and parsed["social"].upper() != "N/A":
                    st.markdown("**🔗 Social Media Found by Claude:**")
                    st.info(parsed["social"])

                if parsed.get("missing") and verdict == "INCONCLUSIVE":
                    st.markdown("**Missing Evidence:**")
                    st.warning(parsed["missing"])

                if parsed.get("notes"):
                    with st.expander("🔍 Analyst Notes (for QA)"):
                        st.markdown(parsed["notes"])

                st.markdown("---")
                st.markdown('<div class="section-title">🔐 Source Transparency Log</div>', unsafe_allow_html=True)
                st.markdown(f"""
<div class="info-block">
<span class="source-tag">WHOIS</span> <a href="{whois_data.get('_source_url','#')}" target="_blank" style="color:#58a6ff">{whois_data.get('_source_url','N/A')}</a> | Verified: {whois_data.get('_verified',False)}<br>
<span class="source-tag">CNPJ</span> <a href="{cnpj_data.get('_source_url','#')}" target="_blank" style="color:#58a6ff">{cnpj_data.get('_source_url','N/A')}</a> | Verified: {cnpj_data.get('_verified',False)}<br>
<span class="source-tag">Web Search</span> Enabled · Claude searched autonomously<br>
<span class="source-tag">Generated</span> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
</div>
""", unsafe_allow_html=True)

                with st.expander("📄 Raw Claude Output (for Gemini dossier generation)"):
                    st.code(raw_verdict, language="markdown")

                # ── TXT Export ──
                st.markdown("---")
                st.markdown('<div class="section-title">💾 Export</div>', unsafe_allow_html=True)

                cnpj_legal_name   = cnpj_data.get("nome", "N/A")
                cnpj_fantasy_name = cnpj_data.get("fantasia", "N/A")
                cnpj_address      = ", ".join(filter(None, [
                    cnpj_data.get("logradouro"), cnpj_data.get("numero"),
                    cnpj_data.get("bairro"),     cnpj_data.get("municipio"),
                    cnpj_data.get("uf"),          cnpj_data.get("cep")
                ])) or "N/A"
                cnpj_email       = cnpj_data.get("email", "N/A")
                cnpj_phone       = cnpj_data.get("telefone", "N/A")
                cnpj_status_val  = cnpj_data.get("situacao", "N/A")
                cnpj_partners    = cnpj_data.get("qsa", [])
                cnpj_partner_str = ", ".join([p.get("nome","") for p in cnpj_partners]) if cnpj_partners else "N/A"
                cnpj_source_url  = cnpj_data.get("_source_url", "N/A")

                whois_registrant = (
                    whois_data.get("registrant_name") or
                    whois_data.get("owner") or
                    (whois_data.get("registrant", {}).get("name","N/A")
                     if isinstance(whois_data.get("registrant"), dict)
                     else whois_data.get("registrant","N/A"))
                )
                whois_contact = whois_data.get("registrant_email") or whois_data.get("emails") or "N/A"
                if isinstance(whois_contact, list):
                    whois_contact = ", ".join(whois_contact)
                whois_source_url = whois_data.get("_source_url","N/A")

                # Merge manual + Claude-found social media (deduplicated)
                all_social = []
                if social_media_links.strip():
                    all_social += [l.strip() for l in social_media_links.strip().split("\n") if l.strip()]
                if parsed.get("social") and parsed["social"].upper() != "N/A":
                    for line in parsed["social"].split("\n"):
                        line = line.strip("- ").strip()
                        if line and line not in all_social:
                            all_social.append(line)

                export_lines = [
                    f"the new investigation is {email_domain}",
                    "",
                    f"here's the whois results: {whois_source_url}",
                    f"Titular Name    : {whois_registrant}",
                    f"Titular Contact : {whois_contact}",
                    "",
                    "company social media links:",
                ]
                for link in (all_social or ["N/A"]):
                    export_lines.append(f"  {link}")

                export_lines += [
                    "",
                    f"corporate taxpayer ID information: {cnpj_source_url}",
                    f"Legal Name      : {cnpj_legal_name}",
                    f"Fantasy Name    : {cnpj_fantasy_name}",
                    f"Address         : {cnpj_address}",
                    f"Email           : {cnpj_email}",
                    f"Contact Phone   : {cnpj_phone}",
                    f"Managing Partner: {cnpj_partner_str}",
                    f"Status          : {cnpj_status_val}",
                    "",
                ]

                if additional_findings.strip():
                    export_lines += ["additional findings:", additional_findings.strip(), ""]

                export_lines += [
                    "--- VERDICT ---",
                    f"{verdict} | Confidence: {confidence}",
                    "",
                    "--- REASONS ---",
                    parsed.get("reasons","N/A"),
                ]

                if parsed.get("notes"):
                    export_lines += ["", "--- ANALYST NOTES ---", parsed["notes"]]

                export_lines += [
                    "",
                    "--- API USAGE (this investigation) ---",
                    f"Input tokens : {usage['input_tokens']:,}",
                    f"Output tokens: {usage['output_tokens']:,}",
                    f"Est. cost    : ${this_cost:.4f} USD",
                ]

                export_txt = "\n".join(export_lines)
                first_id   = machine_ids.split(",")[0].strip() if machine_ids else "unknown"
                filename   = f"case_{first_id}_{email_domain}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"

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
