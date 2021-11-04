# Imports and dependicies include the Algorand Python SDK, the Python Hashlib library, and the Python Matplotlib library.
from algosdk import account, encoding, mnemonic,transaction
from algosdk.future.transaction import AssetTransferTxn, PaymentTxn
from algosdk.v2client import algod
import hashlib
import random
import matplotlib
import matplotlib.pyplot as plt



algod_address = "https://testnet-algorand.api.purestake.io/ps2" # Put Algod Client address here
algod_token = "gAYfMSHWPR5phDz2dq75w1kCIkUKfdO56DgpQSDw" # Put Algod Token here
headers = {"X-API-Key": algod_token }
# Initializes client for node.
algod_client = algod.AlgodClient(algod_token,algod_address,headers)

# Escrow creation.
escrow_address = "XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI" # Put in main fund address here
escrow_mnemonic = "maximum shove federal random silver venture sister juice vacuum invite inmate play mouse deny wood often noodle plug erupt panic month sunset among absorb middle" # Put in main fund receiver_mnemonic here
escrow_key = mnemonic.to_private_key(escrow_mnemonic)
choice_id = 21364625 # Official Test Asset ID for Choice Coin

def slugify(string) -> str:
    slug = string.lower().replace(" ","-")
    return slug

def wait_for_transaction_confirmation(transaction_id: str):
    """Wait until the transaction is confirmed or rejected, or until timeout snumber of rounds have passed."""

    TIMEOUT = 4
    start_round = algod_client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + TIMEOUT:
        try:
            pending_txn = algod_client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception("pool error: {}".format(pending_txn["pool-error"]))

        algod_client.status_after_block(current_round)
        current_round += 1
    raise Exception("pending tx not found in TIMEOUT rounds, TIMEOUT value = : {}".format(TIMEOUT))


def generate_algorand_keypair():
    private_key, address = account.generate_account()
    phrase = mnemonic.from_private_key(private_key)
    return address, phrase, private_key

def choice_vote(sender, key, receiver,amount,comment):
    parameters = algod_client.suggested_params() # Sets suggested parameters
    transaction = AssetTransferTxn(sender, parameters, receiver, amount, choice_id, note=comment)
    # Defines an inital transaction for Choice Coin
    signature = transaction.sign(key)

    # Signs the transaction with the senders private key
    algod_client.send_transaction(signature)
    
    # Sends the transaction with the signature
    final = transaction.get_txid()

    return True, final

def vote_candidate(candidate_address):
    TX_ID = choice_vote(escrow_address, escrow_key, candidate_address, 1, "Tabulated using Choice Coin") 
    message = "Vote counted. \n You can validate that your vote was counted correctly at https://testnet.algoexplorer.io/tx/" + TX_ID[1] + "."
    # AlgoExplorer returned for validation.
    
    return message

def count(address):
    message = ''
    error = ''
    account_info = algod_client.account_info(address) # Fetch account information for the address.
    assets = account_info.get("assets") # Fetch asset information.
    for asset in assets:
        # Iterate over assets until Choice Coin is reached. Return the amount if it exists.
        if asset["asset-id"] ==  choice_id:
            amount = asset.get("amount")
            message = amount
            return message
    error = 'The account has not opted-in to the asset yet.'
    return error


def reset(address, phrase, amount):
    message = ''
    params = algod_client.suggested_params()
    transaction = AssetTransferTxn(address, params, escrow_address, amount, choice_id, note="reset")
    signature = transaction.sign(mnemonic.to_private_key(phrase))
    algod_client.send_transaction(signature)
    
    message = 'Vote accounts reset. New Voting Process started.'
    return message

def send_initial_algorand(
    escrow_address: str,
    escrow_private_key: str,
    recipient_address: str,
) -> None:
    """Send algorand to candidate address."""

    AMOUNT = 210000
    suggested_params = algod_client.suggested_params()
    unsigned_transaction = PaymentTxn(
        escrow_address,
        suggested_params,
        recipient_address,
        AMOUNT,
        note="Initial Funding for Candidate Creation",
    )
    signed_transaction = unsigned_transaction.sign(escrow_private_key)

    try:
        transaction_id = algod_client.send_transaction(signed_transaction)
        wait_for_transaction_confirmation(transaction_id)
    except Exception as err:
        print(err)
        return True
    return False

def choice_coin_opt_in(address, private_key):
    """Opt into Choice Coin."""
    is_failed = send_initial_algorand(
                escrow_address, escrow_key, address
    )
    suggested_params = algod_client.suggested_params()
    transaction = AssetTransferTxn(address, suggested_params, address, 0, choice_id)
    signature = transaction.sign(private_key)
    try:
        transaction_id = algod_client.send_transaction(signature)
    except Exception as e:
        print(e)
    wait_for_transaction_confirmation(transaction_id)

    

def count(address):
    message = ''
    error = ''
    account_info = algod_client.account_info(address) # Fetch account information for the address.
    assets = account_info.get("assets") # Fetch asset information.
    for asset in assets:
        # Iterate over assets until Choice Coin is reached. Return the amount if it exists.
        if asset["asset-id"] ==  choice_id:
            amount = asset.get("amount")
            message = amount
            return message
    error = 'The account has not opted-in to the asset yet.'
    return error

def count_votes(candidates):
    """Count the votes of candidates in an election."""
    labels = []
    values = []
    for candidate in candidates:
        _ = count(candidate.address)
        labels.append(candidate.first_name)
        values.append(_)
    return labels, values