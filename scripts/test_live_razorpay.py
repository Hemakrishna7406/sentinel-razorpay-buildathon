import os
import requests
import time
import uuid

# Configuration
API_URL = "http://localhost:8000"
AGENT_ID = "agent_prod_alpha"


def test_live_execution():
    print("=== Sentinel End-to-End Live Execution Test ===")

    intent_id = f"tx_{uuid.uuid4().hex[:8]}"
    idempotency_key = f"idem_{uuid.uuid4().hex[:8]}"

    # 1. Agent submits intent for evaluation
    print(f"[*] Submitting Intent {intent_id} for evaluation...")
    intent_payload = {
        "intent_id": intent_id,
        "agent_id": AGENT_ID,
        "action_type": "payout",
        "amount": 500,  # 500 INR
        "currency": "INR",
        "recipient": "acc_12345",
        "context": {"vendor_name": "Razorpay Test Vendor", "loss_label": 0},
    }

    headers = {"Idempotency-Key": idempotency_key, "X-Sentinel-Mode": "govern"}

    response = requests.post(f"{API_URL}/evaluate", json=intent_payload, headers=headers)

    if response.status_code != 200:
        print(f"[!] Evaluation Failed: {response.text}")
        return

    eval_result = response.json()
    decision = eval_result.get("decision")
    print(f"[*] Sentinel Decision: {decision}")

    if decision != "ALLOW":
        print("[!] Transaction blocked by Sentinel. Cannot proceed to execution.")
        return

    capability_token = eval_result.get("capability_token")
    if not capability_token:
        print("[!] ALLOWED but no capability token provided. Error.")
        return

    print(f"[*] Capability Token acquired: {capability_token[:30]}...")

    # 2. Agent submits capability token for execution
    print(f"[*] Submitting Capability Token to Execution Gateway...")

    execute_payload = {
        "intent_id": intent_id,
        "action_type": "payout",
        "amount": 500,
        "currency": "INR",
        "recipient": "acc_12345",
        "capability_token": capability_token,
    }

    exec_response = requests.post(f"{API_URL}/execute", json=execute_payload, headers=headers)

    if exec_response.status_code != 200:
        print(f"[!] Execution Failed: {exec_response.text}")
        return

    exec_result = exec_response.json()
    tx_id = exec_result.get("executed_tx_id")
    status = exec_result.get("status")

    print(f"[+] Execution Successful! Live Razorpay Transaction ID: {tx_id}")
    print(f"[+] Status: {status}")


if __name__ == "__main__":
    test_live_execution()
