import json
import streamlit as st
import pandas as pd
import plotly.express as px
from web3 import Web3

st.set_page_config(page_title="Kerdos Token Dashboard", page_icon="🏦", layout="wide")

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #f7f8fc; }
#MainMenu, footer, header { visibility: hidden; }

[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e8eaf0;
}
[data-testid="stSidebar"] .stMetric {
    background: #f0f4ff;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
[data-testid="stSidebar"] .stMetric label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6b7280;
    font-weight: 500;
}
[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace;
    font-size: 18px;
    color: #1a1f36;
    font-weight: 500;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e8eaf0;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
[data-testid="stMetric"] label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6b7280;
    font-weight: 500;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace;
    font-size: 24px;
    color: #1a1f36;
    font-weight: 500;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 2px solid #e8eaf0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: #6b7280;
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
}
.stTabs [aria-selected="true"] {
    color: #2563eb !important;
    border-bottom: 2px solid #2563eb !important;
    background: transparent !important;
}

.stButton > button {
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 13px;
    border-radius: 8px;
    border: 1px solid #e8eaf0;
    background: #ffffff;
    color: #1a1f36;
    padding: 8px 18px;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    border-color: #2563eb;
    color: #2563eb;
    background: #f0f4ff;
}
.stButton > button[kind="primary"] {
    background: #2563eb;
    color: #ffffff;
    border: none;
}
.stButton > button[kind="primary"]:hover {
    background: #1d4ed8;
    color: #ffffff;
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    font-family: 'DM Sans', sans-serif;
    border-radius: 8px;
    border: 1px solid #e8eaf0;
    font-size: 13px;
    color: #1a1f36;
}
.stTextInput > div > div > input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}

[data-testid="stDataFrame"] {
    border: 1px solid #e8eaf0;
    border-radius: 12px;
    overflow: hidden;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
}

[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #e8eaf0 !important;
    border-radius: 12px !important;
    margin-bottom: 12px;
}
[data-testid="stExpander"] summary {
    font-weight: 500;
    font-size: 14px;
    color: #1a1f36;
}

hr { border: none; border-top: 1px solid #e8eaf0; margin: 16px 0; }

[data-testid="stAlert"] {
    border-radius: 10px;
    font-size: 13px;
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    color: #1a1f36;
    letter-spacing: -0.02em;
}
h1 { font-size: 24px; }
h2 { font-size: 18px; }
h3 { font-size: 15px; }

.stCaption, small { font-size: 11px; color: #9ca3af; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PASSWORD GATE
# ─────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("<br><br>", unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("## 🏦 Kerdos Token Dashboard")
        st.markdown("<p style='color:#6b7280;font-size:13px;margin-bottom:24px'>Institutional token management portal</p>", unsafe_allow_html=True)
        pwd = st.text_input("Password", type="password", placeholder="Enter password")
        if st.button("Login", type="primary", use_container_width=True):
            if pwd == st.secrets["auth"]["password"]:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

# ─────────────────────────────────────────────
#  WEB3 CONNECTION
# ─────────────────────────────────────────────
with open("abi.json") as f:
    ABI = json.load(f)

w3 = Web3(Web3.HTTPProvider(st.secrets["contract"]["rpc_url"]))
if not w3.is_connected():
    st.error("Cannot connect to network. Check your RPC URL.")
    st.stop()

contract = w3.eth.contract(
    address=Web3.to_checksum_address(st.secrets["contract"]["contract_addr"]),
    abi=ABI
)

OWNER    = Web3.to_checksum_address(st.secrets["contract"]["owner_address"])
PRIV_KEY = st.secrets["contract"]["private_key"]
DECIMALS = contract.functions.decimals().call()

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def to_human(raw):
    return raw / (10 ** DECIMALS)

def short_addr(addr):
    return f"{addr[:6]}…{addr[-4:]}"

def send_tx(fn):
    try:
        nonce    = w3.eth.get_transaction_count(OWNER)
        tx       = fn.build_transaction({
            "from":     OWNER,
            "nonce":    nonce,
            "gasPrice": w3.eth.gas_price,
            "gas":      300_000,
        })
        signed   = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash  = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt  = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return receipt
    except Exception as e:
        st.error(f"Transaction failed: {e}")
        return None

# ─────────────────────────────────────────────
#  FETCH STATE
# ─────────────────────────────────────────────
@st.cache_data(ttl=15)
def fetch_state():
    total_supply = to_human(contract.functions.totalSupply().call())
    token_name   = contract.functions.name().call()
    token_symbol = contract.functions.symbol().call()

    events = contract.events.Transfer.get_logs(from_block=0)
    wallets = set()
    for e in events:
        if e["args"]["from"] != "0x0000000000000000000000000000000000000000":
            wallets.add(e["args"]["from"])
        if e["args"]["to"] != "0x0000000000000000000000000000000000000000":
            wallets.add(e["args"]["to"])
    wallets.add(OWNER)

    balances    = {addr: to_human(contract.functions.balanceOf(addr).call()) for addr in wallets}
    allowlisted = [addr for addr in wallets if contract.functions.allowlist(addr).call()]

    return {
        "total_supply": total_supply,
        "token_name":   token_name,
        "token_symbol": token_symbol,
        "balances":     balances,
        "allowlisted":  allowlisted,
        "wallets":      list(wallets),
    }

@st.cache_data(ttl=30)
def fetch_transfers():
    events = contract.events.Transfer.get_logs(from_block=0)
    rows = []
    for e in events:
        rows.append({
            "block":  e["blockNumber"],
            "from":   e["args"]["from"],
            "to":     e["args"]["to"],
            "amount": to_human(e["args"]["value"]),
            "type":   "Mint"      if e["args"]["from"] == "0x0000000000000000000000000000000000000000"
                      else "Burn" if e["args"]["to"]   == "0x0000000000000000000000000000000000000000"
                      else "Transfer",
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["block","from","to","amount","type"])

@st.cache_data(ttl=30)
def fetch_blocked():
    events = contract.events.TransferBlocked.get_logs(from_block=0)
    rows = []
    for e in events:
        rows.append({
            "block":  e["blockNumber"],
            "from":   e["args"]["from"],
            "to":     e["args"]["to"],
            "amount": to_human(e["args"]["amount"]),
            "reason": e["args"]["reason"],
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["block","from","to","amount","reason"])

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
state = fetch_state()

with st.sidebar:
    st.markdown("### 🏦 Kerdos")
    st.markdown("<p style='color:#6b7280;font-size:11px;margin-top:-12px;margin-bottom:16px'>KRDS · Sepolia Testnet</p>", unsafe_allow_html=True)
    st.divider()
    st.metric("Total Supply", f"{state['total_supply']:,.0f} KRDS")
    st.metric("Allowlisted Wallets", len(state["allowlisted"]))
    st.divider()
    st.caption(f"Contract: {short_addr(st.secrets['contract']['contract_addr'])}")
    st.caption(f"Owner: {short_addr(OWNER)}")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────
tab_overview, tab_txns, tab_blocked, tab_actions, tab_admin = st.tabs([
    "📊 Overview", "📋 Transactions", "🚫 Blocked", "⚡ Actions", "⚙️ Admin"
])

# ── OVERVIEW ─────────────────────────────────
with tab_overview:
    st.markdown("### Token Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Supply", f"{state['total_supply']:,.0f}")
    c2.metric("Token", f"{state['token_name']} ({state['token_symbol']})")
    c3.metric("Allowlisted Wallets", len(state["allowlisted"]))

    st.divider()
    balances = {k: v for k, v in state["balances"].items() if v > 0}
    if balances:
        df = pd.DataFrame([{"Wallet": short_addr(k), "Balance": v} for k, v in balances.items()])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Distribution")
            fig = px.pie(df, values="Balance", names="Wallet", hole=0.5,
                         color_discrete_sequence=["#2563eb","#3b82f6","#60a5fa","#93c5fd","#bfdbfe"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_family="DM Sans", margin=dict(t=20,b=20,l=20,r=20),
                              legend=dict(font=dict(size=11)))
            fig.update_traces(textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("#### Balances")
            fig2 = px.bar(df, x="Wallet", y="Balance",
                          color_discrete_sequence=["#2563eb"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_family="DM Sans", margin=dict(t=20,b=20,l=20,r=20),
                               xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#f0f0f0"))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### All Wallets")
        df_full = pd.DataFrame([{
            "Address":     addr,
            "Balance (KRDS)": f"{state['balances'].get(addr, 0):,.0f}",
            "Allowlisted": "✅" if contract.functions.allowlist(addr).call() else "❌",
            "Blocked":     "🔴" if contract.functions.blockedlist(addr).call() else "—",
        } for addr in state["wallets"]])
        st.dataframe(df_full, use_container_width=True, hide_index=True)
    else:
        st.info("No token balances yet.")

# ── TRANSACTIONS ─────────────────────────────
with tab_txns:
    st.markdown("### Transaction History")
    df_tx = fetch_transfers()
    if df_tx.empty:
        st.info("No transactions yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Transactions", len(df_tx))
        c2.metric("Total Minted", f"{df_tx[df_tx['type']=='Mint']['amount'].sum():,.0f}")
        c3.metric("Total Burned",  f"{df_tx[df_tx['type']=='Burn']['amount'].sum():,.0f}")
        st.divider()
        df_show = df_tx.copy()
        df_show["from"] = df_show["from"].apply(short_addr)
        df_show["to"]   = df_show["to"].apply(short_addr)
        st.dataframe(df_show.sort_values("block", ascending=False), use_container_width=True, hide_index=True)

# ── BLOCKED ───────────────────────────────────
with tab_blocked:
    st.markdown("### Blocked Transactions")
    df_bl = fetch_blocked()
    if df_bl.empty:
        st.success("No blocked transactions recorded.")
    else:
        st.warning(f"⚠️ {len(df_bl)} blocked transaction(s) found")
        df_show = df_bl.copy()
        df_show["from"] = df_show["from"].apply(short_addr)
        df_show["to"]   = df_show["to"].apply(short_addr)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# ── ACTIONS ───────────────────────────────────
with tab_actions:
    st.markdown("### Token Actions")
    allowlisted = state["allowlisted"]

    with st.expander("🟢 Mint Tokens", expanded=True):
        mode     = st.radio("Recipient", ["Select from allowlist", "Enter manually"], key="mint_mode", horizontal=True)
        mint_to  = st.selectbox("Wallet", allowlisted, key="mint_sel") if mode == "Select from allowlist" \
                   else st.text_input("Address", placeholder="0x…", key="mint_manual")
        mint_amt = st.number_input("Amount (KRDS)", min_value=1, step=1, key="mint_amt")
        if st.button("Mint", type="primary", key="btn_mint"):
            if mint_to:
                with st.spinner("Broadcasting transaction…"):
                    receipt = send_tx(contract.functions.mint(Web3.to_checksum_address(mint_to), mint_amt))
                if receipt and receipt.status == 1:
                    st.success(f"✅ Minted {mint_amt:,} KRDS to {short_addr(mint_to)}")
                    st.cache_data.clear()

    with st.expander("🔴 Burn Tokens"):
        mode      = st.radio("From", ["Select from allowlist", "Enter manually"], key="burn_mode", horizontal=True)
        burn_from = st.selectbox("Wallet", allowlisted, key="burn_sel") if mode == "Select from allowlist" \
                    else st.text_input("Address", placeholder="0x…", key="burn_manual")
        burn_amt  = st.number_input("Amount (KRDS)", min_value=1, step=1, key="burn_amt")
        if st.button("Burn", type="primary", key="btn_burn"):
            if burn_from:
                with st.spinner("Broadcasting transaction…"):
                    receipt = send_tx(contract.functions.burn(Web3.to_checksum_address(burn_from), burn_amt))
                if receipt and receipt.status == 1:
                    st.success(f"✅ Burned {burn_amt:,} KRDS from {short_addr(burn_from)}")
                    st.cache_data.clear()

    with st.expander("🔵 Transfer Tokens"):
        mode   = st.radio("To", ["Select from allowlist", "Enter manually"], key="tf_mode", horizontal=True)
        tf_to  = st.selectbox("Recipient", allowlisted, key="tf_sel") if mode == "Select from allowlist" \
                 else st.text_input("Address", placeholder="0x…", key="tf_manual")
        tf_amt = st.number_input("Amount (KRDS)", min_value=1, step=1, key="tf_amt")
        st.caption("Transfers from the owner wallet. Receiver must be allowlisted.")
        if st.button("Transfer", type="primary", key="btn_tf"):
            if tf_to:
                with st.spinner("Broadcasting transaction…"):
                    receipt = send_tx(contract.functions.transfer(
                        Web3.to_checksum_address(tf_to), tf_amt * (10 ** DECIMALS)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ Transferred {tf_amt:,} KRDS to {short_addr(tf_to)}")
                    st.cache_data.clear()

# ── ADMIN ─────────────────────────────────────
with tab_admin:
    st.markdown("### Admin Controls")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Allowlist")
        add_addr = st.text_input("Add to allowlist", placeholder="0x…", key="add_wl")
        if st.button("Add to Allowlist", key="btn_add_wl", type="primary"):
            if add_addr:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.addToAllowlist(Web3.to_checksum_address(add_addr)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(add_addr)} allowlisted.")
                    st.cache_data.clear()
        st.divider()
        rm_addr = st.selectbox("Remove from allowlist", [""] + allowlisted, key="rm_wl")
        if st.button("Remove from Allowlist", key="btn_rm_wl"):
            if rm_addr:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.removeFromAllowlist(Web3.to_checksum_address(rm_addr)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(rm_addr)} removed.")
                    st.cache_data.clear()

    with col2:
        st.markdown("#### 🚫 Blockedlist")
        add_bl = st.text_input("Add to blockedlist", placeholder="0x…", key="add_bl")
        if st.button("Add to Blockedlist", key="btn_add_bl", type="primary"):
            if add_bl:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.addToBlockedlist(Web3.to_checksum_address(add_bl)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(add_bl)} blocked.")
                    st.cache_data.clear()
        st.divider()
        rm_bl = st.text_input("Remove from blockedlist", placeholder="0x…", key="rm_bl")
        if st.button("Remove from Blockedlist", key="btn_rm_bl"):
            if rm_bl:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.removeFromBlockedlist(Web3.to_checksum_address(rm_bl)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(rm_bl)} unblocked.")
                    st.cache_data.clear()
        st.divider()
        st.markdown("#### 🔍 Check Address")
        check = st.text_input("Address to inspect", placeholder="0x…", key="check")
        if check:
            try:
                addr = Web3.to_checksum_address(check)
                st.metric("Balance",     f"{to_human(contract.functions.balanceOf(addr).call()):,.0f} KRDS")
                st.metric("Allowlisted", "✅ Yes" if contract.functions.allowlist(addr).call() else "❌ No")
                st.metric("Blocked",     "🔴 Yes" if contract.functions.blockedlist(addr).call() else "— No")
            except Exception:
                st.error("Invalid address.")