import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.pack import LearningPack, GeneratedAsset
from backend.models.contract import ObjectiveContract, LearningObjective
from backend.models.quiz import QuizQuestion, QuizQuestionVersion
from backend.models.mastery import ObjectiveMastery, StudentQuizAttempt
from backend.models.user import User
from backend.services.mastery_service import get_student_mastery


def get_teacher_student_analytics(
    db: Session,
    teacher_id: Optional[str] = None,
    pack_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Teacher Analytics Engine:
    Aggregates class-wide student performance metrics, objective mastery distribution,
    individual student roster tracking, recent quiz attempts, and actionable pedagogical insights.
    """
    # 1. Fetch available learning packs with attempt counts
    all_packs = db.query(LearningPack).order_by(LearningPack.created_at.desc()).all()
    available_packs = []
    pack_title_map: Dict[str, str] = {}

    for p in all_packs:
        title = p.contract.title if p.contract else f"Pack #{p.id[:8]}"
        learner_level = p.contract.target_learner_level if p.contract else "Standard"
        pack_title_map[p.id] = title
        
        # Count attempts for this pack
        attempts_count = db.query(StudentQuizAttempt).filter(
            StudentQuizAttempt.pack_id == p.id
        ).count()

        available_packs.append({
            "pack_id": p.id,
            "title": title,
            "target_learner_level": learner_level,
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "attempts_count": attempts_count
        })

    # Sort available packs: packs with attempts first, then recency
    available_packs.sort(key=lambda x: (x["attempts_count"] > 0, x["created_at"]), reverse=True)

    # 2. Scope attempts query
    attempts_query = db.query(StudentQuizAttempt)
    if pack_id and pack_id != "all":
        attempts_query = attempts_query.filter(StudentQuizAttempt.pack_id == pack_id)
    
    attempts = attempts_query.order_by(StudentQuizAttempt.created_at.desc()).all()

    # 3. Query all registered students
    student_users = db.query(User).filter(User.role.ilike("student")).all()
    user_map: Dict[str, User] = {u.id: u for u in student_users}
    for u in student_users:
        if u.student_id:
            user_map[u.student_id] = u

    # 4. Group attempts by student
    student_attempts_map: Dict[str, List[StudentQuizAttempt]] = {}
    for a in attempts:
        student_attempts_map.setdefault(a.student_id, []).append(a)

    # 5. Build Student Performance Roster
    roster: List[Dict[str, Any]] = []
    active_student_ids = set(student_attempts_map.keys())

    # Process all active students first
    for sid, s_attempts in student_attempts_map.items():
        user = user_map.get(sid)
        if not user and sid.lower() == "default_student":
            name = "Demo / Evaluator Student"
            email = "demo.student@lessonfoundry.edu"
            custom_id = "STU-DEMO"
        elif user:
            name = user.name
            email = user.email
            custom_id = user.student_id or f"STU-{user.id[:6].upper()}"
        else:
            name = f"Student {sid[:8]}"
            email = f"student_{sid[:8]}@foundry.edu"
            custom_id = f"STU-{sid[:6].upper()}"

        scores = [att.score_percentage for att in s_attempts]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        max_score = round(max(scores), 1) if scores else 0.0
        latest_att = s_attempts[0]  # ordered desc
        latest_score = round(latest_att.score_percentage, 1)

        # Determine overall tier
        if avg_score >= 90.0:
            tier = "MASTERED"
            status = "Excelling"
        elif avg_score >= 75.0:
            tier = "DEVELOPING"
            status = "On Track"
        elif avg_score >= 60.0:
            tier = "DEVELOPING"
            status = "Developing"
        else:
            tier = "NEEDS_PRACTICE"
            status = "Needs Attention"

        # Unique packs attempted
        packs_set = set(att.pack_id for att in s_attempts)
        packs_info = [
            {"pack_id": pid, "title": pack_title_map.get(pid, f"Pack #{pid[:8]}")}
            for pid in packs_set
        ]

        roster.append({
            "student_id": sid,
            "name": name,
            "email": email,
            "custom_student_id": custom_id,
            "attempts_count": len(s_attempts),
            "average_score": avg_score,
            "highest_score": max_score,
            "latest_score": latest_score,
            "latest_attempt_at": latest_att.created_at.isoformat() if latest_att.created_at else None,
            "mastery_tier": tier,
            "status_label": status,
            "packs_participated": packs_info,
            "needs_intervention": (tier == "NEEDS_PRACTICE" or avg_score < 60.0)
        })

    # Also include registered students without attempts (if viewing all packs)
    if not pack_id or pack_id == "all":
        for u in student_users:
            if u.id not in active_student_ids and (not u.student_id or u.student_id not in active_student_ids):
                roster.append({
                    "student_id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "custom_student_id": u.student_id or f"STU-{u.id[:6].upper()}",
                    "attempts_count": 0,
                    "average_score": 0.0,
                    "highest_score": 0.0,
                    "latest_score": 0.0,
                    "latest_attempt_at": None,
                    "mastery_tier": "NOT_ATTEMPTED",
                    "status_label": "Not Started",
                    "packs_participated": [],
                    "needs_intervention": False
                })

    # Sort roster: Needs intervention first, then average score desc, then attempts desc
    roster.sort(key=lambda s: (
        not s["needs_intervention"],
        -s["average_score"],
        -s["attempts_count"]
    ))

    # 6. Aggregate Executive KPIs
    total_enrolled = len(student_users)
    active_count = len(student_attempts_map)
    total_attempts_count = len(attempts)

    all_scores = [att.score_percentage for att in attempts]
    class_average = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0
    passing_attempts = [s for s in all_scores if s >= 60.0]
    pass_rate = round((len(passing_attempts) / len(all_scores) * 100.0), 1) if all_scores else 0.0

    mastered_count = sum(1 for s in roster if s["mastery_tier"] == "MASTERED")
    developing_count = sum(1 for s in roster if s["mastery_tier"] == "DEVELOPING")
    needs_practice_count = sum(1 for s in roster if s["mastery_tier"] == "NEEDS_PRACTICE")
    not_attempted_count = sum(1 for s in roster if s["mastery_tier"] == "NOT_ATTEMPTED")

    active_evaluated = max(active_count, 1)
    mastery_distribution = {
        "mastered_count": mastered_count,
        "mastered_percent": round((mastered_count / active_evaluated * 100.0), 1),
        "developing_count": developing_count,
        "developing_percent": round((developing_count / active_evaluated * 100.0), 1),
        "needs_practice_count": needs_practice_count,
        "needs_practice_percent": round((needs_practice_count / active_evaluated * 100.0), 1),
        "not_attempted_count": not_attempted_count
    }

    # 7. Objectives Analysis
    # Determine which packs to inspect for objectives
    scoped_pack_ids = [pack_id] if (pack_id and pack_id != "all") else list(set(a.pack_id for a in attempts))
    if not scoped_pack_ids and all_packs:
        scoped_pack_ids = [all_packs[0].id]

    objectives_analysis: List[Dict[str, Any]] = []
    contract_objectives_map: Dict[str, Dict[str, Any]] = {}

    # Gather contract objectives
    for pid in scoped_pack_ids:
        p = db.query(LearningPack).filter(LearningPack.id == pid).first()
        if p and p.contract and p.contract.objectives:
            for lo in p.contract.objectives:
                key = f"{pid}:{lo.code}"
                contract_objectives_map[key] = {
                    "pack_id": pid,
                    "pack_title": p.contract.title,
                    "code": lo.code,
                    "description": lo.description,
                    "bloom_level": lo.bloom_level
                }

    # Query ObjectiveMastery records
    mastery_query = db.query(ObjectiveMastery)
    if pack_id and pack_id != "all":
        mastery_query = mastery_query.filter(ObjectiveMastery.pack_id == pack_id)
    elif scoped_pack_ids:
        mastery_query = mastery_query.filter(ObjectiveMastery.pack_id.in_(scoped_pack_ids))

    all_mastery_records = mastery_query.all()

    # Group mastery records by (pack_id, objective_id) or objective_id
    grouped_mastery: Dict[str, List[ObjectiveMastery]] = {}
    for r in all_mastery_records:
        key = f"{r.pack_id}:{r.objective_id}"
        grouped_mastery.setdefault(key, []).append(r)

    # Compile objective statistics
    for key, obj_meta in contract_objectives_map.items():
        recs = grouped_mastery.get(key, [])
        attempted_total = sum(r.attempted_count for r in recs)
        correct_total = sum(r.correct_count for r in recs)
        scores = [r.score_percentage for r in recs if r.attempted_count > 0]
        avg_obj_score = round(sum(scores) / len(scores), 1) if scores else (
            round((correct_total / attempted_total * 100.0), 1) if attempted_total > 0 else 0.0
        )

        obj_mastered = sum(1 for r in recs if r.mastery_state == "MASTERED")
        obj_developing = sum(1 for r in recs if r.mastery_state == "DEVELOPING")
        obj_needs_practice = sum(1 for r in recs if r.mastery_state == "NEEDS_PRACTICE")
        total_eval = len(recs)

        if avg_obj_score >= 90.0:
            obj_state = "MASTERED"
        elif avg_obj_score >= 60.0:
            obj_state = "DEVELOPING"
        else:
            obj_state = "NEEDS_PRACTICE"

        needs_attention = (avg_obj_score < 60.0 or obj_needs_practice > obj_mastered)

        objectives_analysis.append({
            "key": key,
            "pack_id": obj_meta["pack_id"],
            "pack_title": obj_meta["pack_title"],
            "objective_id": obj_meta["code"],
            "description": obj_meta["description"],
            "bloom_level": obj_meta["bloom_level"],
            "students_evaluated": total_eval,
            "total_questions_attempted": attempted_total,
            "total_questions_correct": correct_total,
            "average_score": avg_obj_score,
            "mastery_state": obj_state,
            "students_mastered_count": obj_mastered,
            "students_developing_count": obj_developing,
            "students_needs_practice_count": obj_needs_practice,
            "needs_attention": needs_attention
        })

    # Sort objectives: Needs attention first, then score asc
    objectives_analysis.sort(key=lambda o: (not o["needs_attention"], o["average_score"]))

    # 8. Recent Quiz Attempts
    recent_attempts: List[Dict[str, Any]] = []
    for att in attempts[:15]:
        user = user_map.get(att.student_id)
        sname = user.name if user else ("Demo Student" if att.student_id.lower() == "default_student" else f"Student {att.student_id[:8]}")
        p_title = pack_title_map.get(att.pack_id, f"Pack #{att.pack_id[:8]}")
        
        recent_attempts.append({
            "attempt_id": att.id,
            "student_id": att.student_id,
            "student_name": sname,
            "pack_id": att.pack_id,
            "pack_title": p_title,
            "score_percentage": att.score_percentage,
            "correct_count": att.correct_count,
            "total_questions": att.total_questions,
            "created_at": att.created_at.isoformat() if att.created_at else ""
        })

    # 9. Pedagogical Actionable Insights
    insights: List[Dict[str, Any]] = []
    
    # Check for weak objectives
    weak_objs = [o for o in objectives_analysis if o["needs_attention"]]
    if weak_objs:
        target = weak_objs[0]
        insights.append({
            "type": "WARNING",
            "title": f"Curricular Gap Detected: {target['objective_id']}",
            "message": (
                f"Class average for '{target['objective_id']}: {target['description']}' is {target['average_score']}%. "
                f"{target['students_needs_practice_count']} students currently require remediation."
            ),
            "recommendation": (
                f"Action Recommended: Conduct a targeted review using the Guided Worked Example and formative quiz questions for {target['objective_id']}."
            )
        })

    # Check for at-risk students
    at_risk = [s for s in roster if s["needs_intervention"]]
    if at_risk:
        names = ", ".join(s["name"] for s in at_risk[:3])
        more = f" and {len(at_risk) - 3} others" if len(at_risk) > 3 else ""
        insights.append({
            "type": "ALERT",
            "title": f"Targeted Intervention Required ({len(at_risk)} Student{'s' if len(at_risk) != 1 else ''})",
            "message": f"Students needing attention: {names}{more} scored below the 60% mastery threshold.",
            "recommendation": "Assign Concept Explanation review sheets or 1-on-1 Voice Tutor practice sessions."
        })

    # Check for high performers
    top_performers = [s for s in roster if s["mastery_tier"] == "MASTERED" and s["attempts_count"] > 0]
    if top_performers:
        insights.append({
            "type": "SUCCESS",
            "title": f"High Mastery Tier ({len(top_performers)} Student{'s' if len(top_performers) != 1 else ''})",
            "message": f"{len(top_performers)} student(s) achieved full mastery (≥ 90%) across assessed objectives.",
            "recommendation": "Ready for Advanced Practice challenge problems and conceptual synthesis."
        })

    return {
        "summary": {
            "total_enrolled_students": total_enrolled,
            "active_students_count": active_count,
            "total_quiz_attempts": total_attempts_count,
            "class_average_score": class_average,
            "pass_rate": pass_rate,
            "mastery_distribution": mastery_distribution,
            "at_risk_count": len(at_risk)
        },
        "objectives_analysis": objectives_analysis,
        "students": roster,
        "recent_attempts": recent_attempts,
        "available_packs": available_packs,
        "insights": insights,
        "selected_pack_id": pack_id or "all"
    }


def get_teacher_student_detail(
    db: Session,
    student_id: str,
    pack_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Teacher Student Diagnostic Dossier:
    Returns full individual drilldown, including per-objective score breakdown,
    complete quiz attempt logs with question-level answers, and personalized recommendations.
    """
    # 1. Look up student profile
    user = db.query(User).filter(User.id == student_id).first()
    if not user and student_id.startswith("STU"):
        user = db.query(User).filter(User.student_id == student_id).first()

    if user:
        student_name = user.name
        email = user.email
        custom_id = user.student_id or f"STU-{user.id[:6].upper()}"
        joined_at = user.created_at.isoformat() if user.created_at else ""
    elif student_id.lower() == "default_student":
        student_name = "Demo / Evaluator Student"
        email = "demo.student@lessonfoundry.edu"
        custom_id = "STU-DEMO"
        joined_at = ""
    else:
        student_name = f"Student {student_id[:8]}"
        email = f"student_{student_id[:8]}@foundry.edu"
        custom_id = f"STU-{student_id[:6].upper()}"
        joined_at = ""

    # 2. Query student quiz attempts
    attempts_query = db.query(StudentQuizAttempt).filter(
        StudentQuizAttempt.student_id == student_id
    )
    if pack_id and pack_id != "all":
        attempts_query = attempts_query.filter(StudentQuizAttempt.pack_id == pack_id)
    
    attempts = attempts_query.order_by(StudentQuizAttempt.created_at.desc()).all()

    # 3. Query student objective masteries
    mastery_query = db.query(ObjectiveMastery).filter(
        ObjectiveMastery.student_id == student_id
    )
    if pack_id and pack_id != "all":
        mastery_query = mastery_query.filter(ObjectiveMastery.pack_id == pack_id)
    
    mastery_records = mastery_query.all()

    # Build objective items with descriptions from contracts
    objectives_list: List[Dict[str, Any]] = []
    pack_cache: Dict[str, Any] = {}

    for rec in mastery_records:
        if rec.pack_id not in pack_cache:
            p = db.query(LearningPack).filter(LearningPack.id == rec.pack_id).first()
            pack_cache[rec.pack_id] = p
        pack = pack_cache.get(rec.pack_id)
        
        desc = None
        bloom = "Understand"
        if pack and pack.contract and pack.contract.objectives:
            for lo in pack.contract.objectives:
                if lo.code == rec.objective_id:
                    desc = lo.description
                    bloom = lo.bloom_level
                    break

        objectives_list.append({
            "objective_id": rec.objective_id,
            "pack_id": rec.pack_id,
            "pack_title": pack.contract.title if pack and pack.contract else f"Pack #{rec.pack_id[:8]}",
            "description": desc,
            "bloom_level": bloom,
            "attempted_count": rec.attempted_count,
            "correct_count": rec.correct_count,
            "score_percentage": rec.score_percentage,
            "mastery_state": rec.mastery_state,
            "last_updated": rec.last_updated.isoformat() if rec.last_updated else ""
        })

    # Sort objectives by score ascending (weakest first)
    objectives_list.sort(key=lambda x: x["score_percentage"])

    # 4. Formulate attempt history
    attempt_history: List[Dict[str, Any]] = []
    for att in attempts:
        if att.pack_id not in pack_cache:
            p = db.query(LearningPack).filter(LearningPack.id == att.pack_id).first()
            pack_cache[att.pack_id] = p
        pack = pack_cache.get(att.pack_id)
        
        answers_dict = {}
        try:
            answers_dict = json.loads(att.answers_json) if att.answers_json else {}
        except Exception:
            answers_dict = {}

        attempt_history.append({
            "attempt_id": att.id,
            "pack_id": att.pack_id,
            "pack_title": pack.contract.title if pack and pack.contract else f"Pack #{att.pack_id[:8]}",
            "score_percentage": att.score_percentage,
            "correct_count": att.correct_count,
            "total_questions": att.total_questions,
            "answers": answers_dict,
            "created_at": att.created_at.isoformat() if att.created_at else ""
        })

    # 5. Get student recommendation if a pack is active
    recommendation = None
    target_pack_id = pack_id if (pack_id and pack_id != "all") else (attempts[0].pack_id if attempts else None)
    if target_pack_id:
        try:
            mastery_resp = get_student_mastery(db, target_pack_id, student_id)
            if mastery_resp and mastery_resp.recommended_action:
                recommendation = {
                    "headline": mastery_resp.recommended_action.headline,
                    "explanation": mastery_resp.recommended_action.explanation,
                    "objective_id": mastery_resp.recommended_action.objective_id,
                    "mastery_state": mastery_resp.recommended_action.mastery_state,
                    "actions": [
                        {"label": a.label, "action": a.action, "target": a.target, "prompt": a.prompt}
                        for a in mastery_resp.recommended_action.actions
                    ]
                }
        except Exception:
            recommendation = None

    scores = [att.score_percentage for att in attempts]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    return {
        "student": {
            "student_id": student_id,
            "name": student_name,
            "email": email,
            "custom_student_id": custom_id,
            "joined_at": joined_at,
            "total_attempts": len(attempts),
            "average_score": avg_score,
            "highest_score": round(max(scores), 1) if scores else 0.0,
            "mastery_tier": "MASTERED" if avg_score >= 90 else ("DEVELOPING" if avg_score >= 60 else "NEEDS_PRACTICE")
        },
        "objectives": objectives_list,
        "attempts": attempt_history,
        "recommendation": recommendation
    }
