import json
import os
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from web3 import Web3

# ─────────────────────────────────────────────
#  CONFIG — all values come from environment variables
#  Set these in Render's dashboard, never hardcode them
# ─────────────────────────────────────────────
RPC_URL        = os.environ["RPC_URL"]
CONTRACT_ADDR  = os.environ["CONTRACT_ADDR"]
OWNER_ADDRESS  = Web3.to_checksum_address(os.environ["OWNER_ADDRESS"])
PRIVATE_KEY    = os.environ["PRIVATE_KEY"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "abi.json") as f:
    ABI = json.load(f)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDR),
    abi=ABI
)
DECIMALS = contract.functions.decimals().call()

# ─────────────────────────────────────────────
#  FASTAPI APP
# ─────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (index.html) from the same directory
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(BASE_DIR / "index.html"))

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def to_raw(amount: float) -> int:
    return int(Decimal(str(amount)) * Decimal(10) ** DECIMALS)

def to_human(raw: int) -> float:
    return raw / (10 ** DECIMALS)

def send_tx(fn):
    """Sign and broadcast a transaction as the owner. Returns tx hash."""
    nonce   = w3.eth.get_transaction_count(OWNER_ADDRESS)
    tx      = fn.build_transaction({
        "from":     OWNER_ADDRESS,
        "nonce":    nonce,
        "gasPrice": w3.eth.gas_price,
        "gas":      200_000,
    })
    signed  = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise Exception("Transaction reverted")
    return tx_hash.hex()

def check_admin_password(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

# ─────────────────────────────────────────────
#  READ ENDPOINTS (no auth needed)
# ─────────────────────────────────────────────
@app.get("/api/config")
def get_config():
    """Returns non-sensitive config the frontend needs — contract address only."""
    return {"contract_addr": CONTRACT_ADDR}

@app.get("/api/state")
def get_state():
    total_supply = to_human(contract.functions.totalSupply().call())
    token_name   = contract.functions.name().call()
    token_symbol = contract.functions.symbol().call()

    whitelisted_events = contract.events.Whitelisted.get_logs(from_block=0)
    wallets = {e["args"]["account"] for e in whitelisted_events}
    wallets.add(OWNER_ADDRESS)
    wallets = {addr for addr in wallets if contract.functions.whitelist(addr).call()}

    wallets_data = []
    for addr in wallets:
        wallets_data.append({
            "address":     addr,
            "balance":     to_human(contract.functions.balanceOf(addr).call()),
            "whitelisted": contract.functions.whitelist(addr).call(),
            "blacklisted": contract.functions.blacklist(addr).call(),
        })

    return {
        "total_supply": total_supply,
        "token_name":   token_name,
        "token_symbol": token_symbol,
        "owner":        OWNER_ADDRESS,
        "wallets":      wallets_data,
    }

@app.get("/api/transactions")
def get_transactions():
    transfer_events = contract.events.Transfer.get_logs(from_block=0)
    rows = []
    for e in transfer_events:
        from_addr = e["args"]["from"]
        to_addr   = e["args"]["to"]
        rows.append({
            "block":  e["blockNumber"],
            "from":   from_addr,
            "to":     to_addr,
            "amount": to_human(e["args"]["value"]),
            "type":   "Mint"     if from_addr == "0x0000000000000000000000000000000000000000"
                      else "Burn" if to_addr   == "0x0000000000000000000000000000000000000000"
                      else "Transfer",
        })
    return sorted(rows, key=lambda x: x["block"], reverse=True)

@app.get("/api/check/{address}")
def check_address(address: str):
    try:
        addr = Web3.to_checksum_address(address)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid address")
    return {
        "address":     addr,
        "balance":     to_human(contract.functions.balanceOf(addr).call()),
        "whitelisted": contract.functions.whitelist(addr).call(),
        "blacklisted": contract.functions.blacklist(addr).call(),
    }

# ─────────────────────────────────────────────
#  OWNER/ADMIN ENDPOINTS (password protected)
# ─────────────────────────────────────────────
class AdminRequest(BaseModel):
    password: str
    address:  str

class MintRequest(BaseModel):
    password: str
    address:  str
    amount:   float

class BurnRequest(BaseModel):
    password: str
    address:  str
    amount:   float

@app.post("/api/mint")
def mint(req: MintRequest):
    check_admin_password(req.password)
    try:
        addr = Web3.to_checksum_address(req.address)
        if not contract.functions.whitelist(addr).call():
            raise HTTPException(status_code=400, detail="Receiver not whitelisted")
        if contract.functions.blacklist(addr).call():
            raise HTTPException(status_code=400, detail="Receiver is blacklisted")
        tx_hash = send_tx(contract.functions.mint(addr, to_raw(req.amount)))
        return {"tx_hash": tx_hash}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/burn")
def burn(req: BurnRequest):
    check_admin_password(req.password)
    try:
        addr = Web3.to_checksum_address(req.address)
        if not contract.functions.whitelist(addr).call():
            raise HTTPException(status_code=400, detail="Sender not whitelisted")
        if contract.functions.blacklist(addr).call():
            raise HTTPException(status_code=400, detail="Sender is blacklisted")
        raw_balance = contract.functions.balanceOf(addr).call()
        if to_raw(req.amount) > raw_balance:
            raise HTTPException(status_code=400, detail=f"Insufficient balance. Available: {to_human(raw_balance):.4f}")
        tx_hash = send_tx(contract.functions.burn(addr, to_raw(req.amount)))
        return {"tx_hash": tx_hash}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/whitelist/add")
def add_whitelist(req: AdminRequest):
    check_admin_password(req.password)
    try:
        addr    = Web3.to_checksum_address(req.address)
        tx_hash = send_tx(contract.functions.addToWhitelist(addr))
        return {"tx_hash": tx_hash}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/whitelist/remove")
def remove_whitelist(req: AdminRequest):
    check_admin_password(req.password)
    try:
        addr    = Web3.to_checksum_address(req.address)
        tx_hash = send_tx(contract.functions.removeFromWhitelist(addr))
        return {"tx_hash": tx_hash}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/blacklist/add")
def add_blacklist(req: AdminRequest):
    check_admin_password(req.password)
    try:
        addr    = Web3.to_checksum_address(req.address)
        tx_hash = send_tx(contract.functions.addToBlacklist(addr))
        return {"tx_hash": tx_hash}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/blacklist/remove")
def remove_blacklist(req: AdminRequest):
    check_admin_password(req.password)
    try:
        addr    = Web3.to_checksum_address(req.address)
        tx_hash = send_tx(contract.functions.removeFromBlacklist(addr))
        return {"tx_hash": tx_hash}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))