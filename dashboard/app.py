import json
import streamlit as st
import pandas as pd
import plotly.express as px
from web3 import Web3

st.set_page_config(page_title="Kerdos Token Dashboard", page_icon="🏦", layout="wide")

def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.title("Kerdos Token Dashboard")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == st.secrets["auth"]["password"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

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

# Helpers
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
            "type":   "Mint"     if e["args"]["from"] == "0x0000000000000000000000000000000000000000"
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

# Sidebar
state = fetch_state()

with st.sidebar:
    st.title("🏦 Kerdos (KRDS)")
    st.divider()
    st.metric("Total Supply", f"{state['total_supply']:,.0f} KRDS")
    st.metric("Allowlisted Wallets", len(state["allowlisted"]))
    st.divider()
    st.caption(f"Contract: {short_addr(st.secrets['contract']['contract_addr'])}")
    st.caption("Network: Sepolia Testnet")
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# Tabs
tab_overview, tab_txns, tab_blocked, tab_actions, tab_admin = st.tabs([
    "📊 Overview", "📋 Transactions", "🚫 Blocked", "⚡ Actions", "⚙️ Admin"
])

# Overview
with tab_overview:
    st.header("Token Overview")
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
            st.subheader("Distribution")
            fig = px.pie(df, values="Balance", names="Wallet", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Balances")
            fig2 = px.bar(df, x="Wallet", y="Balance", color="Balance", color_continuous_scale="Blues")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("All Wallets")
        df_full = pd.DataFrame([{
            "Address":     addr,
            "Balance":     state["balances"].get(addr, 0),
            "Allowlisted": "✅" if contract.functions.allowlist(addr).call() else "❌",
            "Blocked":     "🔴" if contract.functions.blockedlist(addr).call() else "✅",
        } for addr in state["wallets"]])
        st.dataframe(df_full, use_container_width=True, hide_index=True)
    else:
        st.info("No token balances yet.")

# Transactions
with tab_txns:
    st.header("Transaction History")
    df_tx = fetch_transfers()
    if df_tx.empty:
        st.info("No transactions yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Transactions", len(df_tx))
        c2.metric("Total Minted", f"{df_tx[df_tx['type']=='Mint']['amount'].sum():,.0f}")
        c3.metric("Total Burned",  f"{df_tx[df_tx['type']=='Burn']['amount'].sum():,.0f}")

        df_show = df_tx.copy()
        df_show["from"] = df_show["from"].apply(short_addr)
        df_show["to"]   = df_show["to"].apply(short_addr)
        st.dataframe(df_show.sort_values("block", ascending=False), use_container_width=True, hide_index=True)

# Blocked
with tab_blocked:
    st.header("Blocked Transactions")
    df_bl = fetch_blocked()
    if df_bl.empty:
        st.success("No blocked transactions.")
    else:
        st.warning(f"⚠️ {len(df_bl)} blocked transaction(s)")
        df_show = df_bl.copy()
        df_show["from"] = df_show["from"].apply(short_addr)
        df_show["to"]   = df_show["to"].apply(short_addr)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# Actions
with tab_actions:
    st.header("Token Actions")
    allowlisted = state["allowlisted"]

    with st.expander("🟢 Mint", expanded=True):
        mode     = st.radio("Recipient", ["Select from allowlist", "Enter manually"], key="mint_mode")
        mint_to  = st.selectbox("Wallet", allowlisted, key="mint_sel") if mode == "Select from allowlist" \
                   else st.text_input("Address", placeholder="0x…", key="mint_manual")
        mint_amt = st.number_input("Amount (KRDS)", min_value=1, step=1, key="mint_amt")
        if st.button("Mint", type="primary"):
            if mint_to:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.mint(Web3.to_checksum_address(mint_to), mint_amt))
                if receipt and receipt.status == 1:
                    st.success(f"✅ Minted {mint_amt:,} KRDS to {short_addr(mint_to)}")
                    st.cache_data.clear()

    with st.expander("🔴 Burn"):
        mode      = st.radio("From", ["Select from allowlist", "Enter manually"], key="burn_mode")
        burn_from = st.selectbox("Wallet", allowlisted, key="burn_sel") if mode == "Select from allowlist" \
                    else st.text_input("Address", placeholder="0x…", key="burn_manual")
        burn_amt  = st.number_input("Amount (KRDS)", min_value=1, step=1, key="burn_amt")
        if st.button("Burn", type="primary"):
            if burn_from:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.burn(Web3.to_checksum_address(burn_from), burn_amt))
                if receipt and receipt.status == 1:
                    st.success(f"✅ Burned {burn_amt:,} KRDS from {short_addr(burn_from)}")
                    st.cache_data.clear()

    with st.expander("🔵 Transfer"):
        mode   = st.radio("To", ["Select from allowlist", "Enter manually"], key="tf_mode")
        tf_to  = st.selectbox("Recipient", allowlisted, key="tf_sel") if mode == "Select from allowlist" \
                 else st.text_input("Address", placeholder="0x…", key="tf_manual")
        tf_amt = st.number_input("Amount (KRDS)", min_value=1, step=1, key="tf_amt")
        st.caption("Transfers from the owner wallet. Receiver must be allowlisted.")
        if st.button("Transfer", type="primary"):
            if tf_to:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.transfer(
                        Web3.to_checksum_address(tf_to), tf_amt * (10 ** DECIMALS)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ Transferred {tf_amt:,} KRDS to {short_addr(tf_to)}")
                    st.cache_data.clear()

# ── ADMIN ─────────────────────────────────────
with tab_admin:
    st.header("Admin Controls")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Allowlist")
        add_addr = st.text_input("Add to allowlist", placeholder="0x…", key="add_wl")
        if st.button("Add", key="btn_add_wl"):
            if add_addr:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.addToAllowlist(Web3.to_checksum_address(add_addr)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(add_addr)} allowlisted.")
                    st.cache_data.clear()

        st.divider()
        rm_addr = st.selectbox("Remove from allowlist", [""] + allowlisted, key="rm_wl")
        if st.button("Remove", key="btn_rm_wl"):
            if rm_addr:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.removeFromAllowlist(Web3.to_checksum_address(rm_addr)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(rm_addr)} removed.")
                    st.cache_data.clear()

    with col2:
        st.subheader("🚫 Blockedlist")
        add_bl = st.text_input("Add to blockedlist", placeholder="0x…", key="add_bl")
        if st.button("Add", key="btn_add_bl"):
            if add_bl:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.addToBlockedlist(Web3.to_checksum_address(add_bl)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(add_bl)} blocked.")
                    st.cache_data.clear()

        st.divider()
        rm_bl = st.text_input("Remove from blockedlist", placeholder="0x…", key="rm_bl")
        if st.button("Remove", key="btn_rm_bl"):
            if rm_bl:
                with st.spinner("Sending…"):
                    receipt = send_tx(contract.functions.removeFromBlockedlist(Web3.to_checksum_address(rm_bl)))
                if receipt and receipt.status == 1:
                    st.success(f"✅ {short_addr(rm_bl)} unblocked.")
                    st.cache_data.clear()

        st.divider()
        st.subheader("🔍 Check Address")
        check = st.text_input("Address", placeholder="0x…", key="check")
        if check:
            try:
                addr = Web3.to_checksum_address(check)
                st.metric("Balance",     f"{to_human(contract.functions.balanceOf(addr).call()):,.0f} KRDS")
                st.metric("Allowlisted", "✅ Yes" if contract.functions.allowlist(addr).call() else "❌ No")
                st.metric("Blocked",     "🔴 Yes" if contract.functions.blockedlist(addr).call() else "✅ No")
            except Exception:
                st.error("Invalid address.")