import logging
import os
import time
from typing import List, Dict

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import DepositTransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet

MAINNET_ENDPOINT = "https://ctz.solidwallet.io/api/v3"
GOVERNANCE_ADDR = "cx0000000000000000000000000000000000000001"
ICX_FACTOR = 10**18
STEP_LIMIT = 1_000_000
WAIT_SEC = 10

logging.debug(f"===== Initialize User Defined Variables...")
KEY_PATH = os.environ.get("kEY_PATH") or "./keystore"
KEY_PASSPHRASE = os.environ.get("kEY_PASSPHRASE")
CONTRACT_ADDR = os.environ.get("CONTRACT_ADDR")
DEPOSIT_AMOUNT = os.environ.get("DEPOSIT_AMOUNT") or 5000

if None in [KEY_PASSPHRASE, CONTRACT_ADDR, KEY_PATH, DEPOSIT_AMOUNT]:
    raise ValueError(f"Check variables.")


def add(value: int):
    """Deposit ICX values to SCORE."""
    tx = DepositTransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(CONTRACT_ADDR) \
        .value(value * ICX_FACTOR) \
        .step_limit(STEP_LIMIT) \
        .action("add") \
        .build()

    signed_tx = SignedTransaction(tx, wallet)
    return icon_service.send_transaction(signed_tx)


def withdraw(deposit_id: str):
    """Withdraw ICX values from SCORE."""
    tx = DepositTransactionBuilder() \
        .from_(wallet.get_address()) \
        .to(CONTRACT_ADDR) \
        .step_limit(STEP_LIMIT) \
        .nonce(100) \
        .action("withdraw") \
        .id(deposit_id) \
        .build()

    signed_tx = SignedTransaction(tx, wallet)
    return icon_service.send_transaction(signed_tx)


def get_score_status(addr: str) -> dict:
    """Check SCORE status to extract deposit IDs."""
    call = CallBuilder() \
        .from_(wallet.get_address()) \
        .to(GOVERNANCE_ADDR) \
        .method("getScoreStatus") \
        .params({"address": addr}) \
        .build()

    return icon_service.call(call)


# ===============
logging.debug(f"===== Check Wallet Address...")
wallet = KeyWallet.load(KEY_PATH, KEY_PASSPHRASE)
icon_service = IconService(HTTPProvider(MAINNET_ENDPOINT))
logging.debug(f"- Wallet Address: {wallet.get_address()}")

logging.debug(f"===== Check Wallet Balance...")
balance = icon_service.get_balance(wallet.get_address())
logging.debug(f"- Wallet Balance: {balance}")

logging.debug(f"===== Check pre-deposit values on contract {CONTRACT_ADDR}...")
score_status = get_score_status(CONTRACT_ADDR)
if score_status:
    logging.debug(f"... Pre-deposited value found.")
    deposits: List[Dict[str, str]] = score_status["depositInfo"]["deposits"]

    for each_deposit in deposits:
        deposit_id = each_deposit["id"]
        logging.debug(f"... Try to withdraw of {deposit_id}")
        withdraw_result = withdraw(deposit_id)
        logging.debug(f"... Deposit ({deposit_id}) is in withdrawal: {withdraw_result}")

logging.debug(f"===== Wait {WAIT_SEC} for reaching consensus...")
time.sleep(WAIT_SEC)

logging.debug(f"===== Try to deposit assets: {DEPOSIT_AMOUNT} ICX...")
add_result = add(DEPOSIT_AMOUNT)
logging.debug(f"===== COMPLETE! Check on tracker: ")
logging.debug(f"https://tracker.icon.foundation/transaction/{add_result.get('result')}")
