from pathlib import Path
import json

CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "alibi_round.py"
SDK = "v0.2.16"
PROMPT = "Independently compare two revealed testimonies"
CONTEXT = "In a fictional museum mystery, the alarm sounded at 20:10. The east gallery camera was offline, while the lobby clock and guard log are game facts."
RULES = "CONTRADICTION means both statements cannot be true together about the same time, place, or game fact. TENSION is suspicious but reconcilable. Otherwise they are CONSISTENT."


def deploy(vm, direct_deploy, alice):
    vm.sender = alice
    return direct_deploy(str(CONTRACT), CONTEXT, RULES, sdk_version=SDK)


def setup_round(contract, vm, alice, bob, charlie):
    players = [("alex", alice), ("blair", bob), ("casey", charlie)]
    testimonies = {
        "alex": "I was in the lobby from 20:00 until 20:15 and spoke with the guard when the alarm sounded.",
        "blair": "I was in the east gallery at 20:10 and saw Alex there beside the camera cabinet.",
        "casey": "I entered the lobby at 20:08 and saw Alex speaking with the guard when the alarm sounded.",
    }
    nonces = {"alex": "alex-secret-001", "blair": "blair-secret-001", "casey": "casey-secret-001"}
    for player_id, account in players:
        contract.register_player(player_id, "0x" + account.hex())
    contract.lock_roster()
    for player_id, account in players:
        vm.sender = account
        contract.commit_testimony(player_id, contract.make_testimony_commitment(player_id, testimonies[player_id], nonces[player_id]))
    vm.sender = alice
    contract.open_reveals()
    for player_id, account in players:
        vm.sender = account
        contract.reveal_testimony(player_id, testimonies[player_id], nonces[player_id])
    vm.sender = alice


def test_pair_graph_produces_deterministic_winner(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    setup_round(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    direct_vm.mock_llm(PROMPT, json.dumps({"relation": "CONTRADICTION"}))
    contract.compare_pair("alex", "blair")
    direct_vm.clear_mocks()
    direct_vm.mock_llm(PROMPT, json.dumps({"relation": "TENSION"}))
    contract.compare_pair("alex", "casey")
    direct_vm.clear_mocks()
    direct_vm.mock_llm(PROMPT, json.dumps({"relation": "CONSISTENT"}))
    contract.compare_pair("blair", "casey")
    contract.close_round()
    assert contract.get_round()["winner"] == "casey"
    assert contract.get_player("alex")["contradictions"] == 1
    leader = direct_vm._captured_validators[-1][0]
    assert direct_vm.run_validator(leader_result=leader) is True


def test_commitment_binding_and_player_identity(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    contract.register_player("alex", "0x" + direct_alice.hex())
    contract.register_player("blair", "0x" + direct_bob.hex())
    contract.register_player("casey", "0x" + direct_charlie.hex())
    contract.lock_roster()
    testimony = "I remained in the lobby for the entire fictional alarm window and did not enter either gallery."
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only_registered_player"):
        contract.commit_testimony("alex", contract.make_testimony_commitment("alex", testimony, "secret-alex-12"))
    direct_vm.sender = direct_alice
    contract.commit_testimony("alex", contract.make_testimony_commitment("alex", testimony, "secret-alex-12"))


def test_bad_relation_fails_without_recording_pair(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = deploy(direct_vm, direct_deploy, direct_alice)
    setup_round(contract, direct_vm, direct_alice, direct_bob, direct_charlie)
    direct_vm.mock_llm(PROMPT, json.dumps({"relation": "SUSPICIOUS"}))
    with direct_vm.expect_revert("invalid_relation"):
        contract.compare_pair("alex", "blair")
    assert contract.get_round()["compared_pairs"] == 0

