#!/usr/bin/env python3
import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_history_flow():
    print("[1] Testing GET /history...")
    res = requests.get(f"{BASE_URL}/history")
    assert res.status_code == 200, f"GET /history failed: {res.text}"
    data = res.json()
    assert data["status"] == "success"
    sessions = data["sessions"]
    print(f"  Found {len(sessions)} saved sessions.")
    if sessions:
        s0 = sessions[0]
        print(f"  Sample session: ID={s0['id']}, Title='{s0['title']}', MsgCount={s0['message_count']}, ReqCount={s0.get('requirement_count')}")

    print("\n[2] Testing saving a chat with custom name via POST /history/save...")
    # First sign in to get a token if needed, or check existing session
    # Seeded persona analyst login
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "analyst@finreq.bank", "password": "FinReq2026!"})
    token = None
    if login_res.status_code == 200:
        login_data = login_res.json()
        if login_data.get("status") == "mfa_required":
            mfa_res = requests.post(f"{BASE_URL}/api/auth/mfa/verify", json={"email": "analyst@finreq.bank", "code": "000000"})
            if mfa_res.status_code == 200:
                token = mfa_res.json().get("token")
        else:
            token = login_data.get("token")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Pick an existing session or create one to test saving
    test_session_id = sessions[0]["id"] if sessions else "PROJ_TEST_SAVE"
    custom_title = f"Verified Custom Chat Workspace — {uuid.uuid4().hex[:6]}"
    
    save_payload = {
        "project_id": test_session_id,
        "title": custom_title,
        "messages": [
            {"role": "user", "html": "Can we assess liquidity buffers under Basel III?", "created_at": "2026-10-06T12:00:00Z"},
            {"role": "assistant", "html": "Basel III requires minimum capital adequacy and liquidity coverage ratio (LCR) >= 100%.", "created_at": "2026-10-06T12:00:05Z"}
        ]
    }
    save_res = requests.post(f"{BASE_URL}/history/save", json=save_payload, headers=headers)
    assert save_res.status_code == 200, f"POST /history/save failed: {save_res.text}"
    print(f"  Saved session with custom title: '{custom_title}'")

    print("\n[3] Testing GET /history/{session_id} to ensure full workspace restoration...")
    get_res = requests.get(f"{BASE_URL}/history/{test_session_id}")
    assert get_res.status_code == 200, f"GET /history/{test_session_id} failed: {get_res.text}"
    detail = get_res.json()["session"]
    
    assert detail["title"] == custom_title, f"Expected title '{custom_title}', got '{detail['title']}'"
    assert len(detail["messages"]) == 2, f"Expected 2 messages, got {len(detail['messages'])}"
    assert "requirements" in detail, "Missing requirements in restored session"
    assert "compliance_mappings" in detail, "Missing compliance_mappings in restored session"
    assert "risks" in detail, "Missing risks in restored session"
    assert "conflicts" in detail, "Missing conflicts in restored session"
    assert "audit_logs" in detail, "Missing audit_logs in restored session"
    
    print(f"  Restored session details:")
    print(f"    - Title: {detail['title']}")
    print(f"    - Messages: {len(detail['messages'])}")
    print(f"    - Requirements: {len(detail['requirements'])}")
    print(f"    - Compliance Mappings: {len(detail['compliance_mappings'])}")
    print(f"    - Risk Register: {len(detail['risks'])}")
    print(f"    - Conflicts: {len(detail['conflicts'])}")
    print(f"    - Audit Logs: {len(detail['audit_logs'])}")

    print("\n[4] Testing PATCH /history/{session_id} for renaming chat...")
    renamed_title = f"Renamed SME Platform — {uuid.uuid4().hex[:6]}"
    patch_res = requests.patch(f"{BASE_URL}/history/{test_session_id}", json={"title": renamed_title})
    assert patch_res.status_code == 200, f"PATCH failed: {patch_res.text}"
    print(f"  Renamed session to: '{renamed_title}'")

    # Verify rename reflected in GET /history
    list_again = requests.get(f"{BASE_URL}/history").json()["sessions"]
    matched = [s for s in list_again if s["id"] == test_session_id]
    assert len(matched) == 1 and matched[0]["title"] == renamed_title, "Renamed title not found in history list"
    print(f"  Verified rename in /history list: '{matched[0]['title']}'")

    print("\n[ALL TESTS PASSED] History feature and all information endpoints validated successfully!")

if __name__ == "__main__":
    test_history_flow()
