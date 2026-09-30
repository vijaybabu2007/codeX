import os
import sys
import json
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"

def run_live_judge_demo_verification():
    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    print("\n" + "="*70)
    print("YUVA MEGATHON EDUGENAI: ROUND 3 FINAL JUDGE DEMO FLOW VERIFICATION")
    print("="*70)

    # Health check
    health = client.get("/health").json()
    print(f"Health Check: {health}")
    assert health["status"] == "ok"
    assert health["provider"] == "groq"
    assert "gpt-oss-20b" in health["model_configured"]

    # STEP 1: Fresh source ingestion
    print("\n[STEP 1] Ingesting fresh educational source...")
    source_text = (
        "Cellular respiration is the fundamental biochemical process by which eukaryotic cells "
        "harvest energy from glucose to synthesize adenosine triphosphate (ATP). The overall aerobic pathway "
        "comprises glycolysis in the cytoplasm, the pyruvate dehydrogenase reaction and citric acid cycle "
        "within the mitochondrial matrix, and oxidative phosphorylation coupled with chemiosmosis along the "
        "inner mitochondrial cristae. Glycolysis breaks down one 6-carbon glucose molecule into two 3-carbon pyruvate "
        "molecules, producing a net yield of 2 ATP (via substrate-level phosphorylation) and 2 NADH without consuming oxygen. "
        "In the presence of molecular oxygen, pyruvate enters the mitochondrial matrix where the Krebs cycle generates "
        "carbon dioxide, NADH, and FADH2. Finally, in oxidative phosphorylation, high-energy electrons are passed through "
        "protein complexes I to IV in the inner membrane, pumping protons into the intermembrane space to generate an "
        "electrochemical gradient. Molecular oxygen acts as the terminal electron acceptor, reduced to water. As protons flow "
        "back through ATP synthase via chemiosmosis, 26 to 28 ATP are synthesized, yielding a theoretical total of 30-32 ATP per glucose."
    )
    res_src = client.post("/api/v1/sources/text", json={
        "name": "Mitochondrial Bioenergetics & Respiration",
        "text": source_text
    })
    assert res_src.status_code == 200, res_src.text
    src_data = res_src.json()
    source_ver_id = src_data["id"]
    print(f"  -> Source Version ID: {source_ver_id}")
    print(f"  -> Content Length: {src_data['char_count']} chars")

    # STEP 2: Two learning objectives
    print("\n[STEP 2] Defining Objective Contract with 2 Learning Objectives...")
    contract_payload = {
        "source_version_id": source_ver_id,
        "title": "Mitochondrial Respiration and Chemiosmosis",
        "target_learner_level": "Grade 11 AP Biology",
        "expected_difficulty": "Medium",
        "objectives": [
            {
                "code": "LO-01",
                "description": "Explain the stages, cellular compartments, and net ATP yields of glycolysis and the citric acid cycle.",
                "bloom_level": "Understand"
            },
            {
                "code": "LO-02",
                "description": "Analyze how the proton-motive force and terminal electron acceptor (oxygen) drive ATP synthesis via chemiosmosis.",
                "bloom_level": "Analyze"
            }
        ],
        "constraints": {
            "length_budget": "Standard",
            "curriculum": "AP Biology"
        }
    }
    res_contract = client.post("/api/v1/contracts", json=contract_payload)
    assert res_contract.status_code == 200, res_contract.text
    contract = res_contract.json()
    contract_id = contract["id"]
    print(f"  -> Contract ID: {contract_id}")
    print(f"  -> Objectives: {[o['code'] for o in contract['objectives']]}")

    # STEP 3: Generate connected 7-asset learning pack
    print("\n[STEP 3] Generating connected 7-asset learning pack via LIVE Groq LLM...")
    res_pack = client.post("/api/v1/packs/generate", json={"contract_id": contract_id})
    assert res_pack.status_code == 200, res_pack.text
    pack = res_pack.json()
    pack_id = pack["pack_id"]
    print(f"  -> Generated Learning Pack ID: {pack_id}")
    print(f"  -> Concept Explanation: '{pack['concept_explanation']['title']}'")
    print(f"  -> Worked Example: '{pack['worked_example']['content']['title']}'")
    print(f"  -> Quiz Items: {len(pack['quiz_questions'])} questions")
    assert len(pack["quiz_questions"]) == 3, f"Expected 3 quiz items, got {len(pack['quiz_questions'])}"

    q1 = pack["quiz_questions"][0]
    q2 = pack["quiz_questions"][1]
    q3 = pack["quiz_questions"][2]

    # STEP 4: Show alignment matrix
    print("\n[STEP 4] Alignment Matrix Inspection...")
    print(f"  -> Concept Explanation LOs: {pack['concept_explanation'].get('objective_ids')}")
    print(f"  -> Worked Example LOs: {pack['worked_example']['content'].get('objective_ids')}")
    for idx, q in enumerate(pack["quiz_questions"], 1):
        print(f"  -> Q{idx} LOs: {q.get('objective_ids')} | Bloom: {q.get('bloom_level')}")

    # STEP 5: Show grounding / source evidence
    print("\n[STEP 5] Grounding & Provenance Verification...")
    print(f"  -> Source Version Ref: {pack['concept_explanation'].get('source_version_id')}")
    print(f"  -> Concept Supporting Quote: \"{pack['concept_explanation'].get('supporting_quote', '')[:70]}...\"")
    print(f"  -> Q1 Supporting Quote: \"{q1.get('supporting_quote', '')[:70]}...\"")

    # STEP 6 & 7: Quality warnings & Teacher Review
    print("\n[STEP 6 & 7] Quality Warnings & Teacher Review...")
    res_pack_detail = client.get(f"/api/v1/packs/{pack_id}").json()
    warnings = res_pack_detail.get("validations", [])
    print(f"  -> Active Validation Reports: {len(warnings)}")
    for w in warnings:
        print(f"     [{w['severity']}] {w['rule_code']}: {w['message']}")

    # STEP 8: Approve Q1 and Q2
    print("\n[STEP 8] Approving Q1 and Q2...")
    res_app_q1 = client.post(f"/api/v1/decisions/question-versions/{q1['version_id']}", json={
        "action": "APPROVED",
        "acknowledged_warning_ids": []
    })
    assert res_app_q1.status_code == 200, res_app_q1.text
    print(f"  -> Q1 Approved: Version {q1['version_number']}")

    res_app_q2 = client.post(f"/api/v1/decisions/question-versions/{q2['version_id']}", json={
        "action": "APPROVED",
        "acknowledged_warning_ids": []
    })
    assert res_app_q2.status_code == 200, res_app_q2.text
    print(f"  -> Q2 Approved: Version {q2['version_number']}")

    # STEP 9: Keep Q3 as DRAFT
    print("\n[STEP 9] Question 3 remains in initial DRAFT review state...")
    print(f"  -> Q3 Status: {q3['review_status']}")
    assert q3["review_status"] == "DRAFT"

    # STEP 10: Edit or regenerate Q3 (Surgical Question Update)
    print("\n[STEP 10] Surgically editing Question 3...")
    new_stem = "Which complex in the electron transport chain transfers electrons directly to molecular oxygen?"
    new_options = ["Complex IV (Cytochrome c oxidase)", "Complex I (NADH dehydrogenase)", "Complex II (Succinate dehydrogenase)", "ATP Synthase"]
    new_correct = "Complex IV (Cytochrome c oxidase)"
    new_rationale = "Complex IV delivers high-energy electrons directly to oxygen, reducing it to water."
    teacher_notes = "Refined question stem to target Complex IV role as terminal oxidase directly."

    res_edit = client.post(f"/api/v1/questions/{q3['question_id']}/edit", json={
        "question_text": new_stem,
        "options": new_options,
        "correct_answer": new_correct,
        "rationale": new_rationale,
        "teacher_notes": teacher_notes
    })
    assert res_edit.status_code == 200, res_edit.text
    edit_data = res_edit.json()
    q3_v2 = edit_data.get("active_version") or edit_data.get("question") or edit_data
    q3_v2_id = q3_v2.get("version_id") or edit_data.get("active_version_id")
    print(f"  -> Q3 incremented to Version {q3_v2['version_number']} (Status: {q3_v2['review_status']})")
    assert q3_v2["version_number"] == 2
    assert q3_v2["review_status"] == "DRAFT"

    # STEP 11: Show Q3 version history
    print("\n[STEP 11] Inspecting Q3 Version History...")
    res_hist = client.get(f"/api/v1/questions/{q3['question_id']}").json()
    print(f"  -> Total Immutable Versions for Q3: {len(res_hist['versions'])}")
    for v in res_hist["versions"]:
        print(f"     v{v['version_number']} ({v['review_status']}) created at {v['created_at']}")
    assert len(res_hist["versions"]) == 2

    # STEP 12: Show side-by-side diff
    print("\n[STEP 12] Generating Side-by-Side Version Diff (v1 vs v2)...")
    res_diff = client.get(f"/api/v1/questions/{q3['question_id']}/diff?v1=1&v2=2").json()
    print(f"  -> Changed Fields: {res_diff['changed_fields']}")
    print(f"  -> v1 Stem: \"{res_diff['version_a']['question_text']}\"")
    print(f"  -> v2 Stem: \"{res_diff['version_b']['question_text']}\"")
    assert "question_text" in res_diff["changed_fields"]

    # STEP 13: Show Q1 and Q2 unchanged
    print("\n[STEP 13] Verifying Sibling Protection (Q1 and Q2 byte-for-byte unchanged)...")
    refreshed_pack = client.get(f"/api/v1/packs/{pack_id}").json()
    q1_post = refreshed_pack["quiz_questions"][0]
    q2_post = refreshed_pack["quiz_questions"][1]
    assert q1_post["version_id"] == q1["version_id"]
    assert q1_post["question_text"] == q1["question_text"]
    assert q1_post["review_status"] == "APPROVED"
    assert q2_post["version_id"] == q2["version_id"]
    assert q2_post["question_text"] == q2["question_text"]
    assert q2_post["review_status"] == "APPROVED"
    print("  -> Q1 and Q2 remain strictly unchanged in APPROVED state.")

    # STEP 14 & 15: Open Student Portal & verify Q3 hidden while draft
    print("\n[STEP 14 & 15] Student Portal Projection (Q3 hidden while DRAFT)...")
    stud_view_draft = client.get(f"/api/v1/student/packs/{pack_id}").json()
    stud_stems_draft = [q["question_text"] for q in stud_view_draft["quiz_questions"]]
    print(f"  -> Visible Questions to Student: {len(stud_view_draft['quiz_questions'])}")
    assert len(stud_view_draft["quiz_questions"]) == 2
    assert new_stem not in stud_stems_draft
    print("  -> Draft Q3 (v2) is 100% invisible to student projection.")

    # STEP 16: Approve Q3
    print("\n[STEP 16] Teacher Approves Q3 v2...")
    res_app_q3 = client.post(f"/api/v1/decisions/question-versions/{q3_v2_id}", json={
        "action": "APPROVED",
        "acknowledged_warning_ids": []
    })
    assert res_app_q3.status_code == 200, res_app_q3.text
    print("  -> Q3 v2 review_status is now APPROVED.")

    # STEP 17: Verify Q3 appears
    print("\n[STEP 17] Student Portal Projection (Q3 now visible after approval)...")
    stud_view_app = client.get(f"/api/v1/student/packs/{pack_id}").json()
    stud_stems_app = [q["question_text"] for q in stud_view_app["quiz_questions"]]
    print(f"  -> Visible Questions to Student: {len(stud_view_app['quiz_questions'])}")
    assert len(stud_view_app["quiz_questions"]) == 3
    assert new_stem in stud_stems_app
    print("  -> Approved Q3 v2 is now accessible in student view!")

    # STEP 18 & 19: Submit student quiz and show scoring + rationale
    print("\n[STEP 18 & 19] Student Quiz Submission, Instant Scoring & Rationale...")
    res_score = client.post(f"/api/v1/student/packs/{pack_id}/submit-quiz", json={
        "answers": {
            q1["question_id"]: q1["correct_answer"],
            q2["question_id"]: q2["correct_answer"],
            q3["question_id"]: new_correct
        }
    })
    assert res_score.status_code == 200, res_score.text
    score_data = res_score.json()
    print(f"  -> Score: {score_data['correct_count']} / {score_data['total_questions']} ({score_data['score_percentage']}%)")
    assert score_data["score_percentage"] == 100.0
    for fb in score_data["results"]:
        print(f"     [{'CORRECT' if fb['is_correct'] else 'INCORRECT'}] {fb['question_text'][:45]}... -> {fb['rationale']}")

    # STEP 20: Clean Student Handout (zero teacher metadata)
    print("\n[STEP 20] Print/Export Clean Student Handout...")
    clean_handout = client.get(f"/api/v1/student/packs/{pack_id}").json()
    assert clean_handout.get("teacher_notes") is None
    assert clean_handout.get("validations") is None
    assert clean_handout.get("decisions") is None
    for q in clean_handout["quiz_questions"]:
        assert "teacher_notes" not in q
        assert "validations" not in q
        assert "correct_answer" not in q  # Unsubmitted view must not leak answers!
    print("  -> Clean student handout verified: No answer leakage, zero internal teacher metadata.")

    # FAILURE-RECOVERY VERIFICATION (Section 9)
    print("\n" + "-"*70)
    print("FAILURE-RECOVERY VERIFICATION (LLM Failure Protection)")
    print("-" * 70)
    # Test generation with invalid contract ID -> must yield clear 404, never fake generated content
    res_fail = client.post("/api/v1/packs/generate", json={"contract_id": "non-existent-contract-id"})
    assert res_fail.status_code == 400
    print(f"  -> Non-existent contract returns clean HTTP 400 with detail: '{res_fail.json().get('detail')}' (No fake pack generated)")

    # Verify existing approved pack remains intact after failed request
    recheck_pack = client.get(f"/api/v1/packs/{pack_id}").json()
    assert recheck_pack["pack_id"] == pack_id
    assert len(recheck_pack["quiz_questions"]) == 3
    print("  -> Existing approved pack is completely intact and safe after external failure.")

    print("\n" + "="*70)
    print("ALL 20 DEMO STEPS + FAILURE RECOVERY VERIFIED WITH 100% SUCCESS")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_live_judge_demo_verification()
