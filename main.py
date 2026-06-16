import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

import tls_client
from fake_useragent import UserAgent

CONFIG_PATH = Path("config.json")
RESULTS_DIR = Path("results")
LAMPORTS_PER_SOL = 1_000_000_000


def shorten(s: str) -> str:
    return f"{s[:4]}...{s[-5:]}" if len(s) >= 9 else s


def checkTxIsBuy(txData: dict[str, Any]) -> bool:
    """Return True only when transaction logs explicitly identify a buy."""
    log_messages = txData.get("result", {}).get("meta", {}).get("logMessages", []) or []
    for msg in log_messages:
        if "Instruction: Sell" in msg:
            return False
        if "Instruction: Buy" in msg:
            return True
    return False


def getFeeInfo(txData: dict[str, Any]):
    feePaidTo = {}
    feePaid = 0
    instructions = txData.get("result", {}).get("transaction", {}).get("message", {}).get("instructions", [])
    for instr in instructions:
        if "parsed" in instr and instr["parsed"].get("type") == "transfer":
            info = instr["parsed"].get("info", {})
            dest = info.get("destination")
            lamports = int(info.get("lamports", 0))
            if dest in feeWallets:
                solAmount = lamports / LAMPORTS_PER_SOL
                feePaidTo[feeWallets[dest]] = solAmount
                feePaid += solAmount
    return feePaidTo, feePaid


def getSolAmountBought(txData: dict[str, Any]) -> float:
    solAmount = 0
    inner_instructions = txData.get("result", {}).get("meta", {}).get("innerInstructions", []) or []
    for group in inner_instructions:
        for instr in group.get("instructions", []):
            if instr.get("program") == "system":
                parsed = instr.get("parsed")
                if parsed and parsed.get("type") == "transfer":
                    lamports = parsed.get("info", {}).get("lamports")
                    if lamports:
                        solAmount += lamports / LAMPORTS_PER_SOL
    return solAmount


botAccounts = {
    "LUNARCc6FmA3hzPrwmXW3z6RNX1MYXhKS4opYoqCm9P": "Lunar",
    "vs1ongEMwP15z6RKykbUbWwAf8WXFKNTLkfEr5JN6K7": "VisionAIO",
    "BSfD6SHZigAfDWSjzD5Q41jw8LmKwtmjskPH9XW1mrRW": "Photon",
    "7HeD6sLLqAnKVRuSfc1Ko3BSPMNKWgGTiWLKXJF31vKM": "Bloom",
    "b1oomGGqPKGD6errbyfbVMBuzSC8WtAAYo8MwNafWW1": "Bloom",
    "GengarGzVQiNwzmXFC6sz3oT4HY91MnV26nDX6z2U97V": "SharpAIO",
    "minTcHYRLVPubRK8nt6sqe2ZpWrGDLQoNLipDJCGocY": "Mintech",
    "6m2CDdhRgxpH4WjvdzxAYbGxwdGUz5MziiL5jek2kBma": "OKX",
    "BANANAjs7FJiPQqJTGFzkZJndT9o7UmKiYYGaJz6frGu": "Banana Gun",
    "9QT9pBnnvrRXdEdkYhp5KrB9SqgTopmmVNunUm726DbJ": "StarkDex Bot",
    "97VmzkjX9w8gMFS2RnHTSjtMEDbifGXBq9pgosFdFnM": "TradeWiz",
    "CABAL69DYBisjkdHxwVktMy2TPHYVYc2D3UDQQ2DLwKM": "Cabal Bot",
    "b1oodtXw4tigt8MoRcRrWUGCW31WeFUtFMsFgwQpSQ9": "Blood",
    "Axiom3a2w1UbMt2SMgqSvRiuJFTPusDhwKamNgPTeNQ9": "Axiom",
    "PEPPER3dYQpY2TTqHp3XinzRu519X7GswmVNb5tqK8L": "Peppermints",
    "King7ki4SKMBPb3iupnQwTyjsq294jaXsgLmJo8cb7T": "King Bot (??)",
}

feeWallets = {
    "9yMwSPk9mrXSN7yDHUuZurAh1sjbJsfpUqjZ7SvVtdco": "Trojan",
    "AaG6of1gbj1pbDumvbSiTuJhRCRkkUNaWVxijSbWvTJW": "Axiom",
    "97VmzkjX9w8gMFS2RnHTSjtMEDbifGXBq9pgosFdFnM": "TradeWiz",
    "BB5dnY55FXS1e1NXqZDwCzgdYJdMCj3B92PU6Q5Fb6DT": "GMGN",
    "28KqHiudrpzfVkVWQ1jztQ2Aarf4W3CvTitjWEqTCkpA": "BullX",
    "HWEoBxYs7ssKuudEjzjmpfJVX7Dvi7wescFsVx2L5yoY": "Bloxroute",
    "7ks326H4LbMVaUC8nW5FpC5EoAf5eK5pf4Dsx4HDQLpq": "Bloxroute",
    "TEMPaMeCRFAS9EKF53Jd6KpHxgL47uWLcpFArU1Fanq": "Temporal",
    "noz3jAjPiHuBPqiSPkkugaJDkJscPuRhYnSpbi8UvC4": "Temporal",
    "noz3str9KXfpKknefHji8L1mPgimezaiUyCHYMDv1GE": "Temporal",
    "noz6uoYCDijhu1V7cutCpwxNiSovEwLdRHPwmgCGDNo": "Temporal",
    "noz9EPNcT7WH6Sou3sr3GGjHQYVkN3DNirpbvDkv9YJ": "Temporal",
    "nozc5yT15LazbLTFVZzoNZCwjh3yUtW86LoUyqsBu4L": "Temporal",
    "nozFrhfnNGoyqwVuwPAW4aaGqempx4PU6g6D9CJMv7Z": "Temporal",
    "nozievPk7HyK1Rqy1MPJwVQ7qQg2QoJGyP71oeDwbsu": "Temporal",
    "noznbgwYnBLDHu8wcQVCEw6kDrXkPdKkydGJGNXGvL7": "Temporal",
    "nozNVWs5N8mgzuD3qigrCG2UoKxZttxzZ85pvAQVrbP": "Temporal",
    "nozpEGbwx4BcGp6pvEdAh1JoC2CQGZdU6HbNP1v2p6P": "Temporal",
    "nozrhjhkCr3zXT3BiT4WCodYCUFeQvcdUkM7MqhKqge": "Temporal",
    "nozrwQtWhEdrA6W8dkbt9gnUaMs52PdAv5byipnadq3": "Temporal",
    "nozUacTVWub3cL4mJmGCYjKZTnE9RbdY5AP46iQgbPJ": "Temporal",
    "nozWCyTPppJjRuw2fpzDhhWbW355fzosWSzrrMYB1Qk": "Temporal",
    "nozWNju6dY353eMkMqURqwQEoM3SFgEKC6psLCSfUne": "Temporal",
    "nozxNBgWohjR75vdspfxR5H9ceC7XXH99xpxhVGt3Bb": "Temporal",
    "NexTbLoCkWykbLuB1NkjXgFWkX9oAtcoagQegygXXA2": "Next Block 1",
    "nextBLoCkPMgmG8ZgJtABeScP35qLa2AMCNKntAP7Xc": "Next Block 2",
    "NextbLoCkVtMGcV47JzewQdvBpLqT9TxQFozQkN98pE": "Next Block 3",
    "NEXTbLoCkB51HpLBLojQfpyVAMorm3zzKg7w9NFdqid": "Next Block 4",
    "NeXTBLoCKs9F1y5PJS9CKrFNNLU1keHW71rfh7KgA1X": "Next Block 5",
    "neXtBLock1LeC67jYd1QdAa32kbVeubsfPNTJC1V5At": "Next Block 6",
    "nEXTBLockYgngeRmRrjDV31mGSekVPqZoMGhQEZtPVG": "Next Block 7",
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5": "Jito1",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe": "Jito2",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY": "Jito3",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49": "Jito4",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh": "Jito5",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt": "Jito6",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL": "Jito7",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT": "Jito8",
    "6fQaVhYZA4w3MBSXjJ81Vf6W1EDYeUPXpgVQ6UQyU1Av": "0slot",
    "4HiwLEP2Bzqj3hM2ENxJuzhcPCdsafwiet3oGkMkuQY4": "0slot",
    "7toBU3inhmrARGngC7z6SjyP85HgGMmCTEwGNRAcYnEK": "0slot",
    "8mR3wB1nh4D6J9RUCugxUpc6ya8w38LPxZ3ZjcBhgzws": "0slot",
    "6SiVU5WEwqfFapRuYCndomztEwDjvS5xgtEof3PLEGm9": "0slot",
    "TpdxgNJBWZRL8UXF5mrEsyWxDWx9HQexA9P1eTWQ42p": "0slot",
    "D8f3WkQu6dCF33cZxuAsrKHrGsqGP2yvAHf8mX6RXnwf": "0slot",
    "GQPFicsy3P3NXxB5piJohoxACqTvWE9fKpLgdsMduoHE": "0slot",
    "Ey2JEr8hDkgN8qKJGrLf2yFjRhW7rab99HVxwi5rcvJE": "0slot",
    "4iUgjMT8q2hNZnLuhpqZ1QtiV8deFPy2ajvvjEpKKgsS": "0slot",
    "3Rz8uD83QsU8wKvZbgWAPvCNDU6Fy8TSZTMcPm3RB6zt": "0slot",
    "FCjUJZ1qozm1e8romw216qyfQMaaWKxWsuySnumVCCNe": "0slot",
    "Cix2bHfqPcKcM233mzxbLk14kSggUUiz2A87fJtGivXr": "0slot",
    "ENxTEjSQ1YabmUpXAdCgevnHQ9MHdLv8tzFiuiYJqa13": "0slot",
    "J9BMEWFbCBEjtQ1fG5Lo9kouX1HfrKQxeUxetwXrifBw": "0slot",
    "6rYLG55Q9RpsPGvqdPNJs4z5WTxJVatMB8zV3WJhs5EK": "0slot",
    "Dz8rMcdokTLfbnNz2ZdYocZixgaA1TMqbA31xtwPgcxb": "0slot"
}


class CopyWalletFinder:
    def __init__(self, rpcUrl: str):
        self.rpcUrl = rpcUrl
        self.session = tls_client.Session(client_identifier="chrome_103")
        self.headers = {}

    def randomiseRequest(self):
        self.identifier = random.choice(
            [browser for browser in tls_client.settings.ClientIdentifiers.__args__
             if browser.startswith(('chrome', 'safari', 'firefox', 'opera'))]
        )
        parts = self.identifier.split('_')
        identifier, version, *rest = parts
        identifier = identifier.capitalize()

        if identifier == 'Opera':
            osType = 'Windows'
        elif version.lower() == 'ios':
            osType = 'iOS'
        else:
            osType = 'Windows'

        try:
            self.user_agent = UserAgent(os=[osType]).random
        except Exception:
            self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0"

        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://gmgn.ai/?chain=sol',
            'user-agent': self.user_agent,
        }

    def _request_json(self, method: str, url: str, **kwargs):
        try:
            response = getattr(self.session, method)(url, **kwargs)
            return response.json()
        except Exception as exc:
            print(f"Request failed: {exc}")
            return None

    def _rpc(self, method: str, params: list[Any]):
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        data = self._request_json("post", self.rpcUrl, json=payload)
        if not data:
            return None
        if data.get("error"):
            print(f"RPC {method} error: {data['error']}")
            return None
        if data.get("result") is None:
            print(f"RPC {method} returned no result")
            return None
        return data

    def getPNL(self, contractAddress: str, walletAddress: str):
        url = f"https://gmgn.ai/defi/quotation/v1/smartmoney/sol/walletstat/{walletAddress}?token_address={contractAddress}&period=1d"
        for _ in range(3):
            self.randomiseRequest()
            tokenData = (self._request_json("get", url, headers=self.headers) or {}).get('data')
            if not isinstance(tokenData, dict):
                continue
            try:
                profitUsd = f"${float(tokenData.get('total_profit', 0)):,.2f}"
                profitPercent = f"{float(tokenData.get('realized_profit_pnl', 0)):,.2f}%"
                return profitUsd, profitPercent
            except (TypeError, ValueError):
                return "N/A", "N/A"
        return None, None

    def getLastBuy(self, walletAddress: str):
        url = f"https://gmgn.mobi/api/v1/wallet_activity/sol?type=buy&wallet={walletAddress}&limit=10&cost=10"
        for _ in range(3):
            self.randomiseRequest()
            data = self._request_json("get", url, headers=self.headers) or {}
            activities = data.get('data', {}).get('activities', [])
            buys = [act for act in activities if act.get("event_type") == "buy" and act.get('token', {}).get('address')]
            if not buys:
                continue
            lastToken = max(buys, key=lambda x: x.get('timestamp', 0))['token']['address']
            tokenBuys = [act for act in buys if act['token']['address'] == lastToken]
            firstTokenBuy = min(tokenBuys, key=lambda x: x.get('timestamp', 0))
            return firstTokenBuy.get('tx_hash'), firstTokenBuy['token']['address']
        return None, None

    def getBlockHash(self, transaction: str):
        txData = self._rpc("getTransaction", [
            transaction,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}
        ])
        if not txData:
            return None, None
        meta = txData.get("result", {}).get("meta") or {}
        if meta.get("err") is not None or not checkTxIsBuy(txData):
            return None, txData
        return int(txData['result']['slot']), txData

    def getPotentialCopyTraders(self, startBlock: int, walletAddress: str, contractAddress: str, blockLimit: int, txLimit: int | None):
        mainTx = None
        potentialTraders = {}
        for currentBlock in range(startBlock, startBlock + blockLimit + 1):
            data = self._rpc("getBlock", [
                currentBlock,
                {"encoding": "json", "maxSupportedTransactionVersion": 0, "transactionDetails": "full", "rewards": False}
            ])
            if not data:
                continue
            transactions = data.get('result', {}).get('transactions') or []
            if txLimit and txLimit > 0:
                transactions = transactions[:txLimit]
            if currentBlock == startBlock:
                for tx in transactions:
                    accountKeys = tx.get('transaction', {}).get('message', {}).get('accountKeys', [])
                    if walletAddress in accountKeys:
                        postBalances = tx.get('meta', {}).get('postTokenBalances', [])
                        if any(balance.get('mint') == contractAddress for balance in postBalances):
                            mainTx = tx.get('transaction', {}).get('signatures', [None])[0]
                            break
            for tx in transactions:
                accountKeys = tx.get('transaction', {}).get('message', {}).get('accountKeys', [])
                if not accountKeys:
                    continue
                trader = accountKeys[0]
                if trader == walletAddress:
                    continue
                postBalances = tx.get('meta', {}).get('postTokenBalances', [])
                if any(balance.get('mint') == contractAddress for balance in postBalances):
                    potentialTraders.setdefault(trader, (tx.get('transaction', {}).get('signatures', [None])[0], currentBlock))
        uniqueTraders = [(w, sig, blk) for w, (sig, blk) in potentialTraders.items() if sig]
        return mainTx, startBlock, uniqueTraders


def processTransaction(finder: CopyWalletFinder, txSignature: str, mainBlock: int, wallet: str):
    botUsed = botAccounts.get(wallet, "")
    blockInfo, txData = finder.getBlockHash(txSignature)
    if blockInfo is None or not txData:
        return None
    instructions = txData.get("result", {}).get("transaction", {}).get("message", {}).get("instructions", [])
    for instr in instructions:
        if "programId" in instr and instr["programId"] in botAccounts:
            botUsed = botAccounts[instr["programId"]]
            break
    feePaidTo, feePaid = getFeeInfo(txData)
    solBought = getSolAmountBought(txData)
    blockDelay = blockInfo - mainBlock
    return {
        "hash": txSignature,
        "blockDelay": blockDelay,
        "botUsed": botUsed,
        "feePaidTo": feePaidTo,
        "feePaid": f"{feePaid:.8f}",
        "solAmountBought": solBought,
    }


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Copy config.example.json to config.json and fill in your values.")
    with path.open() as f:
        return json.load(f)


def validate_config(config: dict[str, Any]) -> tuple[str, str, int, int | None]:
    rpcUrl = str(config.get('rpc_url', '')).strip()
    walletAddress = str(config.get('walletAddress', '')).strip()
    blockLimit = int(config.get('blockLimit', 1))
    txLimit = config.get('txLimit')
    txLimit = int(txLimit) if txLimit not in (None, "") else None

    if not rpcUrl or rpcUrl.endswith("api-key=xxx"):
        raise ValueError("Set rpc_url in config.json to a real read-only Solana RPC URL.")
    if not walletAddress:
        raise ValueError("Set walletAddress in config.json.")
    if blockLimit < 0:
        raise ValueError("blockLimit must be zero or greater.")
    if txLimit is not None and txLimit <= 0:
        raise ValueError("txLimit must be greater than zero when provided.")
    return rpcUrl, walletAddress, blockLimit, txLimit


def write_outputs(walletAddress: str, contractAddress: str, outputData: dict[str, Any]):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = RESULTS_DIR / f"copytraders_{shorten(walletAddress)}_{shorten(contractAddress)}.json"
    with filename.open("w") as outfile:
        json.dump(outputData, outfile, indent=4)

    csvFilename = RESULTS_DIR / f"copytraders_{shorten(walletAddress)}_{shorten(contractAddress)}.csv"
    with csvFilename.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["WalletAddress", "Trader", "TxSignature", "BlockDelay", "BotUsed", "FeePaidTo", "FeePaid", "SOL Bought", "Profit/PNL"])
        for trader, data in outputData[walletAddress]["potentialCopyTraders"].items():
            writer.writerow([
                walletAddress,
                trader,
                data["hash"],
                data["blockDelay"],
                data["botUsed"],
                json.dumps(data["feePaidTo"]),
                data["feePaid"],
                data["solAmountBought"],
                data["profitPNL"],
            ])
    return filename, csvFilename


def main():
    parser = argparse.ArgumentParser(description="Find wallets that bought the same Solana token shortly after a target wallet.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Path to config JSON file")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        rpcUrl, walletAddress, blockLimit, txLimit = validate_config(config)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    finder = CopyWalletFinder(rpcUrl)
    transaction, contractAddress = finder.getLastBuy(walletAddress)
    if not transaction or not contractAddress:
        print("Could not retrieve main wallet transaction details")
        sys.exit(1)

    mainBlock, txData = finder.getBlockHash(transaction)
    if mainBlock is None or not txData:
        print("Main transaction failed or did not meet the criteria; cannot proceed.")
        sys.exit(1)

    mainSolBought = getSolAmountBought(txData)

    outputData = {
        walletAddress: {
            "contractAddress": contractAddress,
            "mainTransaction": transaction,
            "mainBlock": mainBlock,
            "potentialCopyTraders": {},
        }
    }

    _, mainBlock, potentialTraders = finder.getPotentialCopyTraders(mainBlock, walletAddress, contractAddress, blockLimit, txLimit)
    rows = []
    headers = ["Trader", "Signature", "Block Delay", "Bot Used", "Tx Processor/Fee Wallet", "Fee Paid", "SOL Bought", "Profit/PNL"]
    rows.append(headers)

    for trader, txSig, contestantBlock in potentialTraders:
        result = processTransaction(finder, txSig, mainBlock, trader)
        if not result:
            continue

        profitUsd, profitPercent = finder.getPNL(contractAddress, trader)
        profitPNL = f"{profitUsd} ({profitPercent})" if profitUsd and profitPercent else "N/A"
        result["profitPNL"] = profitPNL

        outputData[walletAddress]["potentialCopyTraders"][trader] = result
        feeWalletsStr = ", ".join(result["feePaidTo"].keys())
        rows.append([
            trader,
            shorten(txSig),
            str(result["blockDelay"]),
            result["botUsed"],
            feeWalletsStr,
            f"{result['feePaid']} SOL",
            f"{result['solAmountBought']:.8f} SOL",
            profitPNL,
        ])

    filename, csvFilename = write_outputs(walletAddress, contractAddress, outputData)

    colWidths = [max(len(str(row[i])) for row in rows) for i in range(len(headers))]
    separator = "+" + "+".join("-" * (w + 2) for w in colWidths) + "+"

    def formatRow(row):
        return "| " + " | ".join(f"{str(cell):<{colWidths[i]}}" for i, cell in enumerate(row)) + " |"

    print(f"Target Wallet: {walletAddress} - {shorten(transaction)} - Block: {mainBlock} - Bought: {mainSolBought:.8f} SOL\n")
    print("Potential copy traders:\n")
    print(separator)
    print(formatRow(rows[0]))
    print(separator)
    for row in rows[1:]:
        print(formatRow(row))
    print(separator)
    print(f"\nCheck {filename} and {csvFilename} for more info")


if __name__ == "__main__":
    main()
