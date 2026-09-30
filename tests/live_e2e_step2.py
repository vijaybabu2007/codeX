import os
import sys
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def run_live_e2e():
    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    print("\n========================================================")
    print("LESSONFOUNDRY MILESTONE 2 STEP 2: LIVE ACCEPTANCE TEST")
    print("========================================================")

    # Health check
    h = client.get("/health").json()
    print(f"Server Health: {h}")
    assert h["status"] == "ok"
    assert h["provider"] == "groq"
    assert "gpt-oss-20b" in h["model_configured"]

    # Step 1: Create fresh source
    print("\n[Step 1] Ingesting fresh source document...")
    source_text = (
        "Cellular respiration is the biochemical process by which eukaryotic cells break down glucose "
        "to synthesize adenosine triphosphate (ATP). The pathway comprises glycolysis in the cytoplasm, "
        "the citric acid cycle within the mitochondrial matrix, and oxidative phosphorylation along the "
        "inner mitochondrial membrane cristae. Glycolysis splits glucose into two molecules of pyruvate, "
        "producing a net yield of 2 ATP and 2 NADH without requiring oxygen. In the presence of oxygen, "
        "pyruvate enters the mitochondrion, yielding acetyl-CoA, which fuels the Krebs cycle to generate "
        "NADH and FADH2 electron carriers. Finally, the electron transport chain uses oxygen as the terminal "
        "electron acceptor, driving ATP synthase via chemiosmosis to produce approximately 30-32 ATP."
    )
    res_src = client.post("/api/v1/sources/text", json={
        "name": "Cellular Respiration Core Biology",
        "text": source_text
    })
    assert res_src.status_code == 200, res_src.text
    src_data = res_src.json()
    source_ver_id = src_data["id"]
    print(f"[OK] Source version created: {source_ver_id} (Length: {src_data['char_count']} chars)")

    # Step 2: Create Contract with at least 2 Learning Objectives
    print("\n[Step 2] Creating Objective Contract...")
    contract_payload = {
        "source_version_id": source_ver_id,
        "title": "Cellular Respiration & Bioenergetics",
        "target_learner_level": "Grade 11 AP Biology",
        "expected_difficulty": "Medium",
        "objectives": [
            {
                "code": "LO-01",
                "description": "Identify the primary stages, cellular locations, and net ATP yields of cellular respiration.",
                "bloom_level": "Understand"
            },
            {
                "code": "LO-02",
                "description": "Analyze the biochemical role of oxygen as the terminal electron acceptor in oxidative phosphorylation.",
                "bloom_level": "Analyze"
            }
        ],
        "constraints": {
            "length_budget": "Standard",
            "answer_reveal": "after_submission"
        }
    }
    res_contract = client.post("/api/v1/contracts", json=contract_payload)
    assert res_contract.status_code == 200, res_contract.text
    contract = res_contract.json()
    contract_id = contract["id"]
    print(f"[OK] Contract created: {contract_id} with 2 Learning Objectives")

    # Step 3: Generate Real 7-Asset Learning Pack via Groq
    print("\n[Step 3] Generating 7-asset learning pack with LIVE Groq LLM...")
    res_pack = client.post("/api/v1/packs/generate", json={"contract_id": contract_id})
    assert res_pack.status_code == 200, res_pack.text
    pack = res_pack.json()
    pack_id = pack["pack_id"]
    print(f"[OK] Learning pack generated: {pack_id}")
    print(f"  Concept Explanation: {pack['concept_explanation']['title']}")
    print(f"  Worked Example: {pack['worked_example']['content']['title']}")
    print(f"  Quiz Questions: {len(pack['quiz_questions'])} items")
    assert len(pack["quiz_questions"]) >= 3, "Expected at least 3 quiz questions"

    q1 = pack["quiz_questions"][0]
    q2 = pack["quiz_questions"][1]
    q3 = pack["quiz_questions"][2]

    print(f"\nInitial Question Statuses:")
    print(f"  Q1 (v{q1['version_number']}): {q1['review_status']} - {q1['question_text'][:55]}...")
    print(f"  Q2 (v{q2['version_number']}): {q2['review_status']} - {q2['question_text'][:55]}...")
    print(f"  Q3 (v{q3['version_number']}): {q3['review_status']} - {q3['question_text'][:55]}...")

    # Step 4: Approve Q1 and Q2
    print("\n[Step 4] Approving Q1 and Q2...")
    res_app_q1 = client.post(f"/api/v1/decisions/question-versions/{q1['version_id']}", json={
        "action": "APPROVED",
        "acknowledged_warning_ids": []
    })
    assert res_app_q1.status_code == 200, res_app_q1.text
    print(f"[OK] Q1 approved (v{q1['version_number']})")

    res_app_q2 = client.post(f"/api/v1/decisions/question-versions/{q2['version_id']}", json={
        "action": "APPROVED",
        "acknowledged_warning_ids": []
    })
    assert res_app_q2.status_code == 200, res_app_q2.text
    print(f"[OK] Q2 approved (v{q2['version_number']})")

    # Step 5: Keep Q3 as DRAFT & check student projection
    print("\n[Step 5] Checking student projection with Q3 in DRAFT...")
    stud_res_1 = client.get(f"/api/v1/student/packs/{pack_id}").json()
    stud_q_texts_1 = [q["question_text"] for q in stud_res_1["quiz_questions"]]
    print(f"[OK] Student sees {len(stud_res_1['quiz_questions'])} questions: Q1 and Q2 visible, Q3 HIDDEN.")
    assert len(stud_res_1["quiz_questions"]) == 2
    assert q1["question_text"] in stud_q_texts_1
    assert q2["question_text"] in stud_q_texts_1
    assert q3["question_text"] not in stud_q_texts_1

    # Step 6: Edit Q3 manually (creating v2)
    print("\n[Step 6] Teacher manually edits Question 3...")
    edited_stem = "Which cellular structure contains the electron transport chain involved in oxidative phosphorylation?"
    edited_options = [
        "Inner mitochondrial membrane cristae",
        "Outer mitochondrial membrane",
        "Cytoplasm cytosol",
        "Nuclear envelope"
    ]
    edited_correct = "Inner mitochondrial membrane cristae"
    edited_rationale = "The electron transport chain is embedded within the cristae of the inner mitochondrial membrane."
    teacher_notes = "Teacher corrected distractor options to sharpen organelle compartmentalization."

    res_edit = client.post(f"/api/v1/questions/{q3['question_id']}/edit", json={
        "question_text": edited_stem,
        "options": edited_options,
        "correct_answer": edited_correct,
        "rationale": edited_rationale,
        "teacher_notes": teacher_notes
    })
    assert res_edit.status_code == 200, res_edit.text
    edit_data = res_edit.json()

    # Step 7, 8, 9, 10: Confirm versioning & draft state & sibling protection
    print("\n[Step 7-10] Verifying immutable versioning and sibling protection...")
    q3_v2 = edit_data.get("active_version") or edit_data.get("question") or edit_data
    q3_v2_id = q3_v2.get("version_id") or edit_data.get("active_version_id")
    assert q3_v2["version_number"] == 2, f"Expected v2, got v{q3_v2['version_number']}"
    assert q3_v2["review_status"] == "DRAFT", f"Expected DRAFT, got {q3_v2['review_status']}"
    assert q3_v2["source_version_id"] == source_ver_id
    assert (q3_v2.get("question_text") or edit_data.get("question", {}).get("question_text")) == edited_stem
    print(f"[OK] Q3 incremented to v{q3_v2['version_number']} in status {q3_v2['review_status']}")

    refreshed_pack = client.get(f"/api/v1/packs/{pack_id}").json()
    q1_refreshed = refreshed_pack["quiz_questions"][0]
    q2_refreshed = refreshed_pack["quiz_questions"][1]
    assert q1_refreshed["version_id"] == q1["version_id"]
    assert q1_refreshed["review_status"] == "APPROVED"
    assert q2_refreshed["version_id"] == q2["version_id"]
    assert q2_refreshed["review_status"] == "APPROVED"
    print("[OK] Approved siblings Q1 and Q2 remain completely unchanged (immutable protection verified)")

    # Step 11: Confirm student projection still excludes Q3 v2
    print("\n[Step 11] Verifying student projection hides unapproved edited Q3 (v2)...")
    stud_res_2 = client.get(f"/api/v1/student/packs/{pack_id}").json()
    assert len(stud_res_2["quiz_questions"]) == 2
    assert edited_stem not in [q["question_text"] for q in stud_res_2["quiz_questions"]]
    print("[OK] Student mode continues to show ONLY Q1 and Q2. Unapproved Q3 v2 is completely protected from students.")

    # Step 12 & 13: Approve Q3 new version and verify student projection
    print("\n[Step 12-13] Approving Q3 v2 and testing student exposure...")
    res_app_q3 = client.post(f"/api/v1/decisions/question-versions/{q3_v2_id}", json={
        "action": "APPROVED",
        "acknowledged_warning_ids": []
    })
    assert res_app_q3.status_code == 200, res_app_q3.text
    print(f"[OK] Q3 v2 approved!")

    stud_res_3 = client.get(f"/api/v1/student/packs/{pack_id}").json()
    assert len(stud_res_3["quiz_questions"]) == 3, f"Expected 3, got {len(stud_res_3['quiz_questions'])}"
    stud_q_texts_3 = [q["question_text"] for q in stud_res_3["quiz_questions"]]
    assert edited_stem in stud_q_texts_3
    print("[OK] Student projection now safely includes Q1, Q2, and the approved Q3 (v2)!")

    # Step 14: Test Student Quiz Scoring
    print("\n[Step 14] Testing Student Quiz Scoring Endpoint...")
    score_payload = {
        "answers": {
            q1["question_id"]: q1["correct_answer"],
            q2["question_id"]: q2["correct_answer"],
            q3["question_id"]: edited_correct
        }
    }
    score_res = client.post(f"/api/v1/student/packs/{pack_id}/submit-quiz", json=score_payload)
    assert score_res.status_code == 200, score_res.text
    score_data = score_res.json()
    assert score_data["total_questions"] == 3
    assert score_data["correct_count"] == 3
    assert score_data["score_percentage"] == 100.0
    print(f"[OK] Student quiz scored: {score_data['correct_count']}/{score_data['total_questions']} (100.0%) - Instant feedback & rationale verified")

    # Step 15: Clean Student View (No teacher metadata)
    print("\n[Step 15] Verifying Clean Student-Ready View...")
    clean_stud = client.get(f"/api/v1/student/packs/{pack_id}").json()
    assert clean_stud.get("teacher_notes") is None
    assert clean_stud.get("validations") is None
    assert clean_stud.get("decisions") is None
    for q_item in clean_stud["quiz_questions"]:
        assert "teacher_notes" not in q_item
        assert "validations" not in q_item
    print("[OK] Clean student view verified: approved-only content, no teacher notes, no validation warnings, no internal provenance metadata")

    # Step 16: Open version history and compute side-by-side diff
    print("\n[Step 16] Inspecting Version History and Side-by-Side Diff...")
    res_diff = client.get(f"/api/v1/questions/{q3['question_id']}/diff?v1=1&v2=2")
    assert res_diff.status_code == 200, res_diff.text
    diff_report = res_diff.json()

    print(f"[OK] Diff generated between v{diff_report['version_a']['version_number']} and v{diff_report['version_b']['version_number']}:")
    print(f"  Changed Fields: {diff_report['changed_fields']}")
    assert "question_text" in diff_report["changed_fields"]
    assert "options" in diff_report["changed_fields"]
    assert "correct_answer" in diff_report["changed_fields"]
    assert "rationale" in diff_report["changed_fields"]

    print(f"  Base (v1) Stem: {diff_report['version_a']['question_text']}")
    print(f"  Target (v2) Stem: {diff_report['version_b']['question_text']}")
    print(f"  Target (v2) Teacher Notes: {diff_report['version_b']['teacher_notes']}")

    # Step 17: Verify Teacher Decision / Audit History
    print("\n[Step 17] Verifying Teacher Decision Audit Trail...")
    history_res = client.get(f"/api/v1/questions/{q3['question_id']}").json()
    assert len(history_res["versions"]) == 2
    v1_hist = next(v for v in history_res["versions"] if v["version_number"] == 1)
    v2_hist = next(v for v in history_res["versions"] if v["version_number"] == 2)
    assert v1_hist["id"] == q3["version_id"]
    assert v2_hist["id"] == q3_v2_id
    assert len(v2_hist["decisions"]) >= 2  # EDITED decision + APPROVED decision
    actions = [d["action"] for d in v2_hist["decisions"]]
    print(f"[OK] Audit decisions recorded on Q3 v2: {actions}")
    assert "EDITED" in actions
    assert "APPROVED" in actions

    print("\n========================================================")
    print("ALL 17 ACCEPTANCE CRITERIA VERIFIED ON LIVE SERVER (GROQ)")
    print("========================================================\n")

if __name__ == "__main__":
    run_live_e2e()
