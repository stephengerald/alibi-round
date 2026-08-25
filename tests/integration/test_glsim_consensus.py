from __future__ import annotations
import json
from pathlib import Path
from gltest import get_contract_factory, get_validator_factory
from gltest.accounts import create_accounts
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address

PROMPT = "Independently compare two revealed testimonies"


def context():
    validators = get_validator_factory().batch_create_mock_validators(5, mock_llm_response={"nondet_exec_prompt": {PROMPT: json.dumps({"relation": "CONSISTENT"})}})
    return {"validators": [validator.to_dict() for validator in validators]}


def ok(receipt):
    assert tx_execution_succeeded(receipt)


def test_five_validator_testimony_graph():
    alex, blair, casey = create_accounts(3)
    factory = get_contract_factory(contract_file_path=Path(__file__).resolve().parents[2] / "contracts" / "alibi_round.py")
    args = ["In a fictional museum mystery, the alarm sounded at 20:10 and the lobby clock and guard log are fixed game facts.", "CONTRADICTION means both statements cannot be true together; TENSION is suspicious but reconcilable; otherwise CONSISTENT."]
    deployed = factory.deploy_contract_tx(args=args, account=alex, wait_transaction_status=TransactionStatus.FINALIZED)
    ok(deployed)
    address = extract_contract_address(deployed)
    host = factory.build_contract(address, account=alex)
    players = [("alex", alex), ("blair", blair), ("casey", casey)]
    texts = {"alex": "I remained in the lobby from 20:00 through 20:15 and spoke with the guard when the alarm sounded.", "blair": "I entered the lobby at 20:05 and waited by the south door until after the alarm.", "casey": "I reached the lobby at 20:08 and saw the guard speaking with Alex when the alarm sounded."}
    nonces = {"alex": "alex-secret-001", "blair": "blair-secret-001", "casey": "casey-secret-001"}
    for player_id, account in players:
        ok(host.register_player(args=[player_id, account.address]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    ok(host.lock_roster(args=[]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    for player_id, account in players:
        player_contract = factory.build_contract(address, account=account)
        commitment = player_contract.make_testimony_commitment(args=[player_id, texts[player_id], nonces[player_id]]).call()
        ok(player_contract.commit_testimony(args=[player_id, commitment]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    ok(host.open_reveals(args=[]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    for player_id, account in players:
        player_contract = factory.build_contract(address, account=account)
        ok(player_contract.reveal_testimony(args=[player_id, texts[player_id], nonces[player_id]]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    for left, right in (("alex", "blair"), ("alex", "casey"), ("blair", "casey")):
        ok(host.compare_pair(args=[left, right]).transact(transaction_context=context(), wait_transaction_status=TransactionStatus.FINALIZED))
    ok(host.close_round(args=[]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    assert host.get_round(args=[]).call()["result"] == "TIE"

