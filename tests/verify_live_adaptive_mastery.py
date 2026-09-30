import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uuid
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, init_db
from backend.models.user import User
from backend.services.auth_service import register_user

def run_live_adaptive_mastery_verification():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("=" * 60)
    print("LESSONFOUNDRY - LIVE ADAPTIVE MASTERY ENGINE VERIFICATION")
    print("=" * 60)

    init_db()
    db = SessionLocal()
    client = TestClient(app)

    unique_suffix = uuid.uuid4().hex[:6]

    # 1. Register Teacher
    teacher_email = f"prof_mastery_{unique_suffix}@lessonfoundry.edu"
    teacher, teacher_token = register_user(
        db,
        name="Professor Bio",
        email=teacher_email,
        password="password123",
        confirm_password="password123",
        role="teacher"
    )
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    print(f"✓ Registered Teacher: {teacher.name} ({teacher.email})")

    # 2. Upload Trusted Source
    source_title = f"Cellular Respiration and Bioenergetics {unique_suffix}"
    source_body = (
        "Cellular respiration is the biochemical pathway by which cells harvest energy from organic molecules. "
        "The first metabolic phase is Glycolysis, occurring exclusively in the cytoplasm. "
        "During glycolysis, one six-carbon glucose molecule is broken down into two three-carbon pyruvate molecules, "
        "yielding a net gain of 2 ATP molecules and 2 NADH molecules via substrate-level phosphorylation. "
        "The second major phase is the Citric Acid Cycle, also known as the Krebs cycle, which occurs within the inner mitochondrial matrix. "
        "Pyruvate is converted to acetyl-CoA, releasing carbon dioxide. Each turn of the cycle produces 1 ATP, 3 NADH, and 1 FADH2. "
        "Finally, the electron transport chain in the inner mitochondrial cristae transfers electrons to generate approximately 28 to 32 ATP."
    )

    src_res = client.post(
        "/api/v1/sources/text",
        json={"name": source_title, "text": source_body},
        headers=teacher_headers
    )
    assert src_res.status_code == 200, f"Source upload failed: {src_res.text}"
    source_version_id = src_res.json()["id"]
    print(f"✓ Snapshot Source: v{src_res.json()['version_number']} (ID: {source_version_id})")

    # 3. Create Objective Contract with 2 objectives
    contract_payload = {
        "source_version_id": source_version_id,
        "title": "Bioenergetics Curricular Contract",
        "target_learner_level": "Grade 11",
        "expected_difficulty": "Medium",
        "objectives": [
            {
                "code": "LO-01",
                "description": "Understand Glycolysis pathway and net ATP yield in cytoplasm",
                "bloom_level": "Understand"
            },
            {
                "code": "LO-02",
                "description": "Analyze Krebs Cycle reactions in mitochondrial matrix",
                "bloom_level": "Analyze"
            }
        ]
    }
    contract_res = client.post("/api/v1/contracts", json=contract_payload, headers=teacher_headers)
    assert contract_res.status_code == 200, f"Contract creation failed: {contract_res.text}"
    contract_id = contract_res.json()["id"]
    print(f"✓ Created Contract: {contract_id} with LO-01 and LO-02")

    # 4. Generate Real Learning Pack
    print("⏳ Generating real 7-asset learning pack via configured provider...")
    gen_res = client.post(
        "/api/v1/packs/generate",
        json={"contract_id": contract_id},
        headers=teacher_headers
    )
    assert gen_res.status_code == 200, f"Pack generation failed: {gen_res.text}"
    pack_data = gen_res.json()
    pack_id = pack_data["pack_id"]
    print(f"✓ Generated Learning Pack ID: {pack_id}")

    # 5. Teacher Review: Approve All Assets & Questions
    print("⏳ Approving assets in Teacher Review Gate...")
    pack_details = client.get(f"/api/v1/packs/{pack_id}", headers=teacher_headers).json()

    for asset_key in ["concept_explanation", "worked_example", "easy_practice", "advanced_practice", "revision_sheet"]:
        asset = pack_details.get(asset_key)
        if asset and asset.get("version_id"):
            client.post(
                f"/api/v1/decisions/asset-versions/{asset['version_id']}",
                json={"action": "APPROVED"},
                headers=teacher_headers
            )

    for q in pack_details.get("quiz_questions", []):
        if q.get("version_id"):
            client.post(
                f"/api/v1/decisions/question-versions/{q['version_id']}",
                json={"action": "APPROVED"},
                headers=teacher_headers
            )
    print("✓ All 7 assets and quiz questions Approved for Student Projection.")

    # 6. Register Student
    student_email = f"student_mastery_{unique_suffix}@lessonfoundry.edu"
    student, student_token = register_user(
        db,
        name="Alex Student",
        email=student_email,
        password="password123",
        confirm_password="password123",
        role="student",
        student_id=f"STU-{unique_suffix.upper()}"
    )
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print(f"✓ Registered Student: {student.name} ({student.student_id})")

    # 7. Student retrieves approved pack
    student_pack = client.get(f"/api/v1/student/packs/{pack_id}", headers=student_headers).json()
    assert len(student_pack["quiz_questions"]) >= 2, "Expected approved quiz questions in student pack"
    print(f"✓ Student retrieved approved projection: {len(student_pack['quiz_questions'])} quiz items")

    # 8. Student Takes Quiz: Intentionally produce LO-01 = 100%, LO-02 = 0%
    # We query the question version to see correct answers
    from backend.models.quiz import QuizQuestionVersion, QuizQuestion
    answers = {}
    import json
    for q_item in student_pack["quiz_questions"]:
        qv = db.query(QuizQuestionVersion).filter(QuizQuestionVersion.question_id == q_item["id"]).order_by(QuizQuestionVersion.version_number.desc()).first()
        lo_ids = json.loads(qv.objective_ids_json) if qv.objective_ids_json else []
        correct_ans = qv.correct_answer

        if "LO-01" in lo_ids and "LO-02" not in lo_ids:
            # Answer correctly for LO-01
            answers[q_item["id"]] = correct_ans
        elif "LO-02" in lo_ids and "LO-01" not in lo_ids:
            # Pick a wrong answer for LO-02
            wrong_options = [opt for opt in q_item["options"] if opt != correct_ans]
            answers[q_item["id"]] = wrong_options[0] if wrong_options else "Wrong Answer"
        else:
            # If mapped to both or none, answer correctly
            answers[q_item["id"]] = correct_ans

    # Submit quiz
    quiz_submit_res = client.post(
        f"/api/v1/student/packs/{pack_id}/submit-quiz",
        json={"answers": answers},
        headers=student_headers
    )
    assert quiz_submit_res.status_code == 200, f"Quiz submit failed: {quiz_submit_res.text}"
    score_data = quiz_submit_res.json()

    print("\n--- QUIZ SUBMISSION RESULTS ---")
    print(f"Overall Score: {score_data['score_percentage']}% ({score_data['correct_count']}/{score_data['total_questions']})")
    print("Objective-Level Mastery Performance:")
    lo1_item = None
    lo2_item = None
    for obj in score_data.get("objective_performance", []):
        print(f"  • {obj['objective_id']}: {obj['score_percentage']}% ({obj['correct']}/{obj['attempted']}) -> {obj['mastery_state']}")
        if obj["objective_id"] == "LO-01":
            lo1_item = obj
        elif obj["objective_id"] == "LO-02":
            lo2_item = obj

    assert lo1_item is not None and lo1_item["mastery_state"] == "MASTERED", f"Expected LO-01 to be MASTERED, got {lo1_item}"
    assert lo2_item is not None and lo2_item["mastery_state"] == "NEEDS_PRACTICE", f"Expected LO-02 to be NEEDS_PRACTICE, got {lo2_item}"

    # Verify Adaptive Recommendation
    rec = score_data.get("recommended_action")
    assert rec is not None, "Expected recommended_action in quiz score response"
    print("\n--- ADAPTIVE RECOMMENDATION ---")
    print(f"Target Objective: {rec['objective_id']}")
    print(f"Headline: {rec.get('headline') or rec.get('title')}")
    print(f"Explanation: {rec['explanation']}")
    print("Actions:")
    for a in rec.get("actions", []):
        print(f"  [{a['label']}] -> target: {a['target']}")

    assert rec["objective_id"] == "LO-02", "Recommendation must focus on weak objective LO-02"
    assert rec["mastery_state"] == "NEEDS_PRACTICE"
    targets = [a["target"] for a in rec["actions"]]
    assert "concept_explanation" in targets or "easy_practice" in targets
    assert "voice_tutor" in targets

    # 9. Ask Voice Tutor targeting LO-02
    print("\n--- VOICE TUTOR CONTEXTUAL QUERY ---")
    voice_action = next(a for a in rec["actions"] if a["target"] == "voice_tutor")
    contextual_query = voice_action.get("prompt") or voice_action.get("contextual_query") or "Help me understand LO-02 because I am struggling with this objective."
    print(f"Query: \"{contextual_query}\"")

    voice_res = client.post(
        "/api/v1/student/voice/query",
        json={
            "pack_id": pack_id,
            "question": contextual_query,
            "language": "en"
        },
        headers=student_headers
    )
    assert voice_res.status_code == 200, f"Voice query failed: {voice_res.text}"
    voice_data = voice_res.json()
    print(f"Voice Tutor Answer:\n\"{voice_data['answer']}\"")
    print(f"Grounded: {voice_data['grounded']}")
    print(f"Source Evidence: {voice_data.get('source_evidence', [])}")
    assert voice_data["grounded"] is True, "Voice tutor response must be certified grounded"
    assert len(voice_data["answer"]) > 10, "Voice tutor must provide an educational explanation"

    # 10. Verify Persistence via GET /api/v1/student/packs/{pack_id}/mastery
    print("\n--- VERIFYING PERSISTENCE ---")
    mastery_get_res = client.get(f"/api/v1/student/packs/{pack_id}/mastery", headers=student_headers)
    assert mastery_get_res.status_code == 200, f"Get mastery failed: {mastery_get_res.text}"
    mastery_data = mastery_get_res.json()
    assert len(mastery_data["objectives"]) == 2
    assert mastery_data["recommended_action"]["objective_id"] == "LO-02"
    print("✓ GET /api/v1/student/packs/{pack_id}/mastery successfully returned persisted mastery data!")

    print("\n" + "=" * 60)
    print("✓ LIVE ADAPTIVE MASTERY ENGINE MVP VERIFICATION COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    run_live_adaptive_mastery_verification()
