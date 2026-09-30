from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class StudentQuestionItem(BaseModel):
    id: str
    question_text: str
    options: List[str]
    objective_ids: List[str]

class StudentExplanationItem(BaseModel):
    id: str
    title: str
    explanation: str
    objective_ids: List[str]

class StudentWorkedExampleItem(BaseModel):
    id: str
    title: str
    scenario: str
    steps: List[str]
    final_answer: str
    objective_ids: List[str]

class StudentPracticeTaskItem(BaseModel):
    id: str
    title: str
    problem_statement: str
    solution_guidance: str
    objective_ids: List[str]
    bloom_level: str
    difficulty_label: str

class StudentRevisionSheetItem(BaseModel):
    id: str
    title: str
    key_concepts: List[str]
    definitions: List[Dict[str, str]]
    important_relationships: List[str]
    key_example: str
    common_mistakes: List[str]
    objective_ids: List[str]

class StudentPackResponse(BaseModel):
    pack_id: str
    contract_title: str
    target_learner_level: str
    source_version_id: str
    concept_explanation: Optional[StudentExplanationItem] = None
    worked_example: Optional[StudentWorkedExampleItem] = None
    quiz_questions: List[StudentQuestionItem] = []
    easy_practice: Optional[StudentPracticeTaskItem] = None
    advanced_practice: Optional[StudentPracticeTaskItem] = None
    revision_sheet: Optional[StudentRevisionSheetItem] = None
    message: Optional[str] = None

class StudentQuizSubmissionRequest(BaseModel):
    answers: Dict[str, str]  # question_id -> selected_option_text

class StudentQuizResultItem(BaseModel):
    question_id: str
    question_text: str
    selected_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    rationale: Optional[str] = None

class ObjectiveMasteryItem(BaseModel):
    objective_id: str
    objective_description: Optional[str] = None
    bloom_level: Optional[str] = None
    attempted: int
    correct: int
    score_percentage: float
    mastery_state: str  # "MASTERED", "DEVELOPING", "NEEDS_PRACTICE"

class ActionLinkItem(BaseModel):
    label: str
    action: str
    target: str
    prompt: Optional[str] = None

class RecommendedActionItem(BaseModel):
    objective_id: str
    mastery_state: str
    headline: str
    explanation: str
    actions: List[ActionLinkItem] = []

class StudentMasteryResponse(BaseModel):
    pack_id: str
    student_id: str
    objectives: List[ObjectiveMasteryItem] = []
    recommended_action: Optional[RecommendedActionItem] = None
    total_attempts: int = 0

class StudentQuizScoreResponse(BaseModel):
    pack_id: str
    total_questions: int
    correct_count: int
    score_percentage: float
    results: List[StudentQuizResultItem]
    objective_performance: List[ObjectiveMasteryItem] = []
    recommended_action: Optional[RecommendedActionItem] = None

class StudentVoiceQueryRequest(BaseModel):
    pack_id: str
    question: str
    language: str = "en"
    current_asset_id: Optional[str] = None
    last_quiz_submission: Optional[Dict[str, Any]] = None

class StudentVoiceQueryResponse(BaseModel):
    answer: str
    objective_ids: List[str] = []
    source_evidence: List[str] = []
    grounded: bool = True
    language: str = "en"
    intent: Optional[str] = None
