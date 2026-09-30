import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional
from backend.models.validation import ValidationReport
from backend.services.grounding_service import verify_grounding

# Bloom's Taxonomy Cognitive Hierarchy Ranks
BLOOM_RANKS = {
    "remember": 1,
    "understand": 2,
    "apply": 3,
    "analyze": 4,
    "evaluate": 5,
    "create": 6
}

# 1. Key Integrity (MCQ option match)
def validate_key_integrity(
    question_text: str,
    options: List[str],
    correct_answer: str,
    entity_id: str,
    question_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    normalized_options = [opt.strip().lower() for opt in options]
    clean_correct = correct_answer.strip().lower()

    matched = False
    for idx, opt in enumerate(normalized_options):
        if clean_correct == opt:
            matched = True
            break
        prefixes = [f"{chr(65+idx).lower()})", f"{chr(65+idx).lower()}.", f"option {chr(65+idx).lower()}"]
        if clean_correct in prefixes or clean_correct == chr(65+idx).lower():
            matched = True
            break
        if len(clean_correct) > 3 and clean_correct in opt:
            matched = True
            break

    if not matched:
        reports.append(ValidationReport(
            question_version_id=question_version_id,
            validation_type="KEY_INTEGRITY",
            severity="CRITICAL",
            rule_code="KEY_INTEGRITY_MISMATCH",
            message=f"Answer Key Mismatch: Specified correct answer '{correct_answer}' does not match any provided options: {options}",
            evidence_snippet=f"Options: {options} | Specified Key: '{correct_answer}'",
            affected_entity_id=entity_id,
            is_blocking=True
        ))
    return reports

# 2. Answer Key Consistency (Quiz vs Dedicated Answer Key)
def validate_answer_key_consistency(
    quiz_questions: List[Dict[str, Any]],
    answer_key_items: List[Dict[str, Any]],
    asset_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    key_dict = {item.get("question_id"): item for item in answer_key_items}

    for q in quiz_questions:
        q_id = q.get("question_id")
        q_correct = q.get("correct_answer", "").strip().lower()
        key_item = key_dict.get(q_id)

        if not key_item:
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                validation_type="KEY_INTEGRITY",
                severity="CRITICAL",
                rule_code="ANSWER_KEY_MISSING_ENTRY",
                message=f"Missing Answer Key Entry: No answer key entry found for question {q_id}.",
                evidence_snippet=f"Question ID: {q_id}",
                affected_entity_id=q_id or "answer_key",
                is_blocking=True
            ))
            continue

        key_option = key_item.get("correct_option", "").strip().lower()
        # Compare options (direct or substring match)
        if q_correct != key_option and (q_correct not in key_option and key_option not in q_correct):
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                validation_type="KEY_INTEGRITY",
                severity="CRITICAL",
                rule_code="ANSWER_KEY_CONSISTENCY_MISMATCH",
                message=f"Answer Key Conflict: Question {q_id} specifies correct answer '{q.get('correct_answer')}' but Answer Key specifies '{key_item.get('correct_option')}'.",
                evidence_snippet=f"Quiz Key: '{q.get('correct_answer')}' vs Answer Key: '{key_item.get('correct_option')}'",
                affected_entity_id=q_id or "answer_key",
                is_blocking=True
            ))
    return reports

# 3. Cognitive Difficulty Validation (Easy vs Advanced Practice)
def validate_cognitive_difficulty(
    easy_practice: Dict[str, Any],
    advanced_practice: Dict[str, Any],
    easy_version_id: str | None = None,
    adv_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    easy_bloom = easy_practice.get("bloom_level", "Understand").lower()
    adv_bloom = advanced_practice.get("bloom_level", "Apply").lower()
    
    easy_rank = BLOOM_RANKS.get(easy_bloom, 2)
    adv_rank = BLOOM_RANKS.get(adv_bloom, 3)

    easy_steps = easy_practice.get("reasoning_step_count", 1)
    adv_steps = advanced_practice.get("reasoning_step_count", 3)

    # Condition: Advanced practice must have greater cognitive demand (higher Bloom rank OR more reasoning steps)
    if adv_rank < easy_rank:
        reports.append(ValidationReport(
            asset_version_id=adv_version_id,
            validation_type="DIFFICULTY_ALIGNMENT",
            severity="CRITICAL",
            rule_code="COGNITIVE_DIFFICULTY_INVERSION",
            message=f"Difficulty Inversion: Advanced practice has lower Bloom cognitive level ({adv_bloom.capitalize()}) than Easy practice ({easy_bloom.capitalize()}).",
            evidence_snippet=f"Easy: {easy_bloom} (rank {easy_rank}), steps={easy_steps} | Advanced: {adv_bloom} (rank {adv_rank}), steps={adv_steps}",
            affected_entity_id=adv_version_id or "advanced_practice",
            is_blocking=True
        ))
    elif adv_rank == easy_rank and adv_steps <= easy_steps:
        reports.append(ValidationReport(
            asset_version_id=adv_version_id,
            validation_type="DIFFICULTY_ALIGNMENT",
            severity="WARNING",
            rule_code="COGNITIVE_DIFFICULTY_IDENTICAL",
            message=f"Insufficient Cognitive Differentiation: Advanced practice ({adv_bloom.capitalize()}, {adv_steps} steps) does not meaningfully exceed Easy practice ({easy_bloom.capitalize()}, {easy_steps} steps).",
            evidence_snippet=f"Both tasks share similar cognitive steps and Bloom level: {easy_bloom}",
            affected_entity_id=adv_version_id or "advanced_practice",
            is_blocking=False
        ))
    return reports

# 4. Duplicate and Near-Duplicate Question Detection
def validate_duplicate_questions(
    quiz_questions: List[Dict[str, Any]],
    asset_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    for i in range(len(quiz_questions)):
        for j in range(i + 1, len(quiz_questions)):
            q1 = quiz_questions[i]
            q2 = quiz_questions[j]
            stem1 = q1.get("question", "").strip().lower()
            stem2 = q2.get("question", "").strip().lower()

            if not stem1 or not stem2:
                continue

            similarity = SequenceMatcher(None, stem1, stem2).ratio()
            q1_id = q1.get("question_id", f"Q{i+1}")
            q2_id = q2.get("question_id", f"Q{j+1}")

            if similarity >= 0.95:
                reports.append(ValidationReport(
                    asset_version_id=asset_version_id,
                    validation_type="DUPLICATE_DETECTION",
                    severity="CRITICAL",
                    rule_code="DUPLICATE_QUESTION",
                    message=f"Duplicate Question Detected: {q1_id} and {q2_id} are identical or virtually identical.",
                    evidence_snippet=f"{q1_id}: '{stem1}' vs {q2_id}: '{stem2}' (similarity: {similarity:.2f})",
                    affected_entity_id=q2_id,
                    is_blocking=True
                ))
            elif similarity >= 0.80:
                reports.append(ValidationReport(
                    asset_version_id=asset_version_id,
                    validation_type="DUPLICATE_DETECTION",
                    severity="WARNING",
                    rule_code="NEAR_DUPLICATE_QUESTION",
                    message=f"Near-Duplicate Question Detected: {q1_id} and {q2_id} exhibit high textual similarity ({similarity:.2f}).",
                    evidence_snippet=f"{q1_id}: '{stem1}' vs {q2_id}: '{stem2}'",
                    affected_entity_id=q2_id,
                    is_blocking=False
                ))
    return reports

# 5. Answer Leakage Detection
def validate_answer_leakage(
    quiz_questions: List[Dict[str, Any]],
    worked_example_scenario: str = "",
    asset_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    stop_words = {"the", "and", "for", "with", "that", "this", "from", "both", "none", "true", "false", "all", "yes", "not"}

    for q in quiz_questions:
        q_id = q.get("question_id", "Quiz Question")
        stem = q.get("question", "").lower()
        correct = q.get("correct_answer", "").strip().lower()

        # Only check substantial answers (>4 characters, non-stopwords)
        if len(correct) < 4 or correct in stop_words:
            continue

        # Check leakage in the question's own stem
        if correct in stem:
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                validation_type="ANSWER_LEAKAGE",
                severity="CRITICAL",
                rule_code="ANSWER_LEAKAGE_IN_STEM",
                message=f"Answer Leakage: The correct answer '{correct}' is explicitly revealed in the question stem.",
                evidence_snippet=f"Question stem: '{stem}' | Correct answer: '{correct}'",
                affected_entity_id=q_id,
                is_blocking=True
            ))

        # Check leakage in worked example scenario if scenario directly gives away question
        if worked_example_scenario and f"answer to {q_id.lower()}" in worked_example_scenario.lower():
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                validation_type="ANSWER_LEAKAGE",
                severity="WARNING",
                rule_code="ANSWER_LEAKAGE_IN_WORKED_EXAMPLE",
                message=f"Answer Leakage: Worked example scenario mentions {q_id} explicitly.",
                evidence_snippet=f"Worked example references {q_id}",
                affected_entity_id=q_id,
                is_blocking=False
            ))
    return reports

# 6. Grounding Validation
def validate_grounding_evidence(
    supporting_quote: str,
    source_text: str,
    entity_id: str,
    asset_version_id: str | None = None,
    question_version_id: str | None = None
) -> tuple[List[ValidationReport], str]:
    is_grounded, status_str, detail = verify_grounding(supporting_quote, source_text)
    reports = []
    if not is_grounded:
        reports.append(ValidationReport(
            asset_version_id=asset_version_id,
            question_version_id=question_version_id,
            validation_type="GROUNDING",
            severity="WARNING",
            rule_code="GROUNDING_UNVERIFIED_QUOTE",
            message="Unsupported Claim: The provided supporting quote could not be verified in the source text.",
            evidence_snippet=f"Unverified quote: '{supporting_quote[:120]}...'",
            affected_entity_id=entity_id,
            is_blocking=False
        ))
    return reports, status_str

# 7. Revision Sheet Grounding & Concept Validation
def validate_revision_sheet_grounding(
    revision_sheet: Dict[str, Any],
    source_text: str,
    asset_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    # Check definitions
    definitions = revision_sheet.get("definitions", [])
    for d in definitions:
        term = d.get("term", "").strip()
        if term and term.lower() not in source_text.lower():
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                validation_type="GROUNDING",
                severity="WARNING",
                rule_code="REVISION_UNGROUNDED_CONCEPT",
                message=f"Revision Sheet Discrepancy: Defined technical term '{term}' is absent from the source text.",
                evidence_snippet=f"Term: '{term}'",
                affected_entity_id=asset_version_id or "revision_sheet",
                is_blocking=False
            ))
    return reports

# 8. Cross-Asset Contradiction Check
def validate_cross_asset_contradiction(
    explanation_text: str,
    worked_example: Dict[str, Any],
    asset_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    exp_lower = explanation_text.lower()
    ex_steps = " ".join(worked_example.get("steps", [])).lower()

    # Heuristic checks for common contradictory patterns (e.g. "requires oxygen" vs "does not require oxygen")
    contradiction_pairs = [
        ("requires oxygen", "does not require oxygen"),
        ("aerobic process", "anaerobic process"),
        ("in the stroma", "in the thylakoid"),
        ("light-dependent", "light-independent")
    ]

    for p1, p2 in contradiction_pairs:
        if (p1 in exp_lower and p2 in ex_steps) or (p2 in exp_lower and p1 in ex_steps):
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                validation_type="CONSISTENCY",
                severity="WARNING",
                rule_code="CROSS_ASSET_CONTRADICTION",
                message=f"Potential Contradiction: Found conflicting statements between Explanation ('{p1}') and Worked Example ('{p2}').",
                evidence_snippet=f"Conflict between '{p1}' and '{p2}'",
                affected_entity_id=asset_version_id or "worked_example",
                is_blocking=False
            ))
    return reports

# 9. Terminology Consistency
def validate_terminology_consistency(
    concept_explanation: Dict[str, Any],
    revision_sheet: Dict[str, Any],
    asset_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    exp_text = concept_explanation.get("explanation", "").lower()
    definitions = revision_sheet.get("definitions", [])

    for d in definitions:
        term = d.get("term", "").lower().strip()
        if term and term not in exp_text:
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                validation_type="CONSISTENCY",
                severity="INFO",
                rule_code="TERMINOLOGY_INCONSISTENCY",
                message=f"Terminology Notice: Revision sheet emphasizes term '{term}' which is not explicitly mentioned in the Concept Explanation.",
                evidence_snippet=f"Term '{term}' absent from explanation text.",
                affected_entity_id=asset_version_id or "revision_sheet",
                is_blocking=False
            ))
    return reports

# 10. Objective Alignment, Orphan Content & Imbalance Detection
def validate_objective_alignment(
    objective_ids: List[str],
    valid_contract_codes: List[str],
    entity_id: str,
    asset_version_id: str | None = None,
    question_version_id: str | None = None
) -> List[ValidationReport]:
    reports = []
    if not objective_ids:
        reports.append(ValidationReport(
            asset_version_id=asset_version_id,
            question_version_id=question_version_id,
            validation_type="ALIGNMENT",
            severity="WARNING",
            rule_code="ALIGNMENT_ORPHAN_ITEM",
            message="Orphan Content: Item has no associated learning objective.",
            evidence_snippet=None,
            affected_entity_id=entity_id,
            is_blocking=False
        ))
    else:
        invalid_codes = [code for code in objective_ids if code not in valid_contract_codes]
        if invalid_codes:
            reports.append(ValidationReport(
                asset_version_id=asset_version_id,
                question_version_id=question_version_id,
                validation_type="ALIGNMENT",
                severity="WARNING",
                rule_code="ALIGNMENT_UNKNOWN_CODE",
                message=f"Unknown Objective Code(s) referenced: {invalid_codes}. Contract defines: {valid_contract_codes}",
                evidence_snippet=f"Invalid codes: {invalid_codes}",
                affected_entity_id=entity_id,
                is_blocking=False
            ))
    return reports

def compute_alignment_matrix_and_audit(
    contract_objectives: List[str],
    mapped_items: List[Dict[str, Any]] # Each has: {"id": str, "type": str, "objective_ids": List[str]}
) -> tuple[Dict[str, Any], List[ValidationReport]]:
    """
    Computes bipartite coverage matrix and checks for:
    - UNCOVERED_OBJECTIVE (an objective with 0 items)
    - COVERAGE_IMBALANCE (ratio > 3:1 between covered objectives)
    """
    coverage_counts = {code: 0 for code in contract_objectives}
    matrix = {}
    reports = []

    for item in mapped_items:
        item_id = item.get("id")
        item_name = item.get("type", "Item")
        item_objs = item.get("objective_ids", [])
        matrix[item_id] = {
            "name": item_name,
            "coverage": {code: (code in item_objs) for code in contract_objectives}
        }
        for code in item_objs:
            if code in coverage_counts:
                coverage_counts[code] += 1

    # Audit A: Uncovered Objective
    for code, count in coverage_counts.items():
        if count == 0:
            reports.append(ValidationReport(
                validation_type="ALIGNMENT",
                severity="WARNING",
                rule_code="UNCOVERED_OBJECTIVE",
                message=f"Missing Objective Coverage: Learning objective '{code}' is not addressed by any generated asset or quiz item.",
                evidence_snippet=f"Objective '{code}' has 0 mapped items.",
                affected_entity_id=code,
                is_blocking=False
            ))

    # Audit B: Coverage Imbalance
    covered_counts = [count for count in coverage_counts.values() if count > 0]
    if len(covered_counts) >= 2:
        max_c = max(covered_counts)
        min_c = min(covered_counts)
        if min_c > 0 and (max_c / min_c) > 3.0:
            reports.append(ValidationReport(
                validation_type="ALIGNMENT",
                severity="WARNING",
                rule_code="OBJECTIVE_COVERAGE_IMBALANCE",
                message=f"Coverage Imbalance Detected: High variance in objective representation ({max_c} items vs {min_c} items, ratio > 3:1).",
                evidence_snippet=f"Coverage distribution: {coverage_counts}",
                affected_entity_id="alignment_matrix",
                is_blocking=False
            ))

    summary = {
        "matrix": matrix,
        "counts": coverage_counts,
        "total_items": len(mapped_items),
        "uncovered_objectives": [c for c, count in coverage_counts.items() if count == 0]
    }
    return summary, reports
