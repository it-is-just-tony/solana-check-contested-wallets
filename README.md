# Solana Contested Wallet Checker

A heuristic tool for finding wallets that bought the same Solana token shortly after a target wallet.

> This is an analysis tool, not proof of copy-trading. Treat results as leads to investigate manually.

## Security notes

- Do **not** put private keys, seed phrases, or wallet files in this repo.
- Use a read-only RPC URL/API key with low privileges and rotate it if it is exposed.
- `config.json` is ignored by Git. Keep real API keys local only.
- The tool sends wallet and token addresses to GMGN endpoints to fetch recent activity and PNL data.
- Run in a virtual environment or disposable container when testing unfamiliar dependencies.

## Setup

1. Create a local config file:

   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json`:

   ```json
   {
     "rpc_url": "https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY",
     "walletAddress": "TARGET_WALLET_ADDRESS",
     "blockLimit": 1,
     "txLimit": 100
   }
   ```

   - `blockLimit`: number of blocks after the target transaction to scan.
   - `txLimit`: maximum number of transactions to inspect per block. Set a smaller value while testing to reduce RPC usage.

3. Install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Run:

   ```bash
   python main.py
   ```

   Or use a custom config path:

   ```bash
   python main.py --config path/to/config.json
   ```

## Local development workflow

When using Codex/cloud for changes, think of this repo like any normal Git branch:

1. Ask Codex for a focused change.
2. Review the diff in the PR.
3. Pull the branch locally.
4. Create your local config from `config.example.json`.
5. Run the same checks locally before merging.

Useful local commands:

```bash
python -m py_compile main.py
python main.py --config config.json
```

## Test wallets

- Cupsey: `suqh5sHtr8HyJ7q8scBimULPkPpA557prMG47xCHQfK`
- Euris: `DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj`
- Waddles: `73LnJ7G9ffBDjEBGgJDdgvLUhD5APLonKrNiHsKDCw5B`
- Gake: `DNfuF1L62WWyW3pNakVkyGGFzVVhj4Yr52jSmdTyeBHm`

## Current limitations

- Detection is heuristic and can produce false positives.
- SOL bought is estimated from inner system transfers and may include fees/tips/routing transfers.
- GMGN endpoints are unofficial dependencies and may change or rate-limit requests.
- Bot and fee wallet lists need ongoing maintenance.
