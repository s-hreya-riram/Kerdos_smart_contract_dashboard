# Kerdos Token Dashboard

A MetaMask-connected Web3 dashboard for the Kerdos RWA security token.

## Files

- `server.py` — FastAPI backend (owner tx signing, read endpoints)
- `index.html` — Frontend (MetaMask wallet connection, transfer, admin UI)
- `abi.json` — Contract ABI
- `requirements.txt` — Python dependencies

## Local Development

```bash
pip install -r requirements.txt

export RPC_URL="your_sepolia_rpc_url"
export CONTRACT_ADDR="your_contract_address"
export OWNER_ADDRESS="your_owner_wallet_address"
export PRIVATE_KEY="your_owner_private_key"
export ADMIN_PASSWORD="your_chosen_password"

uvicorn server:app --reload
```

Then open http://localhost:8000

## Deploying to Render

1. Push this folder to a GitHub repo
2. Go to render.com → New → Web Service
3. Connect the repo
4. Set these settings:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render's dashboard:
   - `RPC_URL`
   - `CONTRACT_ADDR`
   - `OWNER_ADDRESS`
   - `PRIVATE_KEY`
   - `ADMIN_PASSWORD`
6. Deploy — Render gives you a public URL

## How It Works

- **Overview tab:** Reads token state from chain via the FastAPI backend
- **Transactions tab:** Shows on-chain Transfer events + session-scoped blocked transactions
- **Transfer tab:** User connects MetaMask, signs transfer directly from their wallet — no private key touches the server
- **Admin tab:** Password-protected. Mint, burn, whitelist, blacklist are signed server-side by the owner key stored in Render's environment variables

## Architecture

```
Browser (index.html)
  ├── Read calls → GET /api/state, /api/transactions, /api/check/:addr
  ├── Transfer → MetaMask signs directly, broadcasts to Sepolia
  └── Admin actions → POST /api/mint|burn|whitelist|blacklist
                        └── server.py signs with PRIVATE_KEY env var
                              └── broadcasts to Sepolia via RPC_URL
```