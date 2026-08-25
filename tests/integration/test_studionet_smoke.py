import json
from pathlib import Path

import pytest
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address


def _ok(receipt):
    assert tx_execution_succeeded(receipt)
    return receipt


@pytest.mark.integration
def test_studionet_testimony_comparison(default_account, secondary_account, tertiary_account):
    factory = get_contract_factory(contract_file_path=Path(__file__).resolve().parents[2] / "contracts" / "alibi_round.py")
    args = ["In a fictional museum mystery, the alarm sounded at 20:10 and the lobby clock and guard log are fixed game facts.", "CONTRADICTION means both statements cannot be true together; TENSION is suspicious but reconcilable; otherwise CONSISTENT."]
    deployed = _ok(factory.deploy_contract_tx(args=args, account=default_account, wait_transaction_status=TransactionStatus.FINALIZED))
    address = extract_contract_address(deployed)
    host = factory.build_contract(address, account=default_account)
    players = [("alex", default_account), ("blair", secondary_account), ("casey", tertiary_account)]
    texts = {"alex": "I remained in the lobby from 20:00 through 20:15 and spoke with the guard when the alarm sounded.", "blair": "I entered the lobby at 20:05 and waited by the south door until after the alarm.", "casey": "I reached the lobby at 20:08 and saw the guard speaking with Alex when the alarm sounded."}
    nonces = {"alex": "alex-secret-001", "blair": "blair-secret-001", "casey": "casey-secret-001"}
    for player_id, account in players:
        _ok(host.register_player(args=[player_id, account.address]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    _ok(host.lock_roster(args=[]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    for player_id, account in players:
        contract = factory.build_contract(address, account=account)
        commitment = contract.make_testimony_commitment(args=[player_id, texts[player_id], nonces[player_id]]).call()
        _ok(contract.commit_testimony(args=[player_id, commitment]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    _ok(host.open_reveals(args=[]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    for player_id, account in players:
        contract = factory.build_contract(address, account=account)
        _ok(contract.reveal_testimony(args=[player_id, texts[player_id], nonces[player_id]]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    intelligent = _ok(host.compare_pair(args=["alex", "blair"]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    state = host.get_round(args=[]).call()
    assert state["compared_pairs"] == 1 and state["phase"] == "COMPARING"
    print("STUDIONET_RECORD=" + json.dumps({"address": address, "deploy_tx": deployed["hash"], "intelligent_tx": intelligent["hash"], "observed": "one_pair_compared"}, sort_keys=True))
