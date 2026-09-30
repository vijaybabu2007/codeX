from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# 1. Concept Explanation
class GeneratedConceptExplanation(BaseModel):
    title: str = Field(..., description="Comprehensive title for the concept explanation")
    explanation: str = Field(..., description="Well-structured conceptual explanation grounded strictly in the source text")
    objective_ids: List[str] = Field(..., min_length=1, description="List of learning objective codes addressed (e.g. ['LO-01', 'LO-02'])")
    supporting_quote: str = Field(..., description="Verbatim quote from the source supporting this concept explanation")

# 2. Worked / Guided Example
class GeneratedWorkedExample(BaseModel):
    title: str = Field(..., description="Descriptive title of the worked example")
    scenario: str = Field(..., description="Concrete problem scenario or context directly tied to source content")
    steps: List[str] = Field(..., min_length=2, description="Step-by-step reasoning or mathematical/conceptual derivation")
    final_answer: str = Field(..., description="Clear final resolution or summary of the worked example")
    objective_ids: List[str] = Field(..., min_length=1, description="Objective IDs addressed by this example")
    supporting_quote: str = Field(..., description="Verbatim quote from the source supporting the example")

# 3. Formative Quiz Question Item
class GeneratedQuizQuestion(BaseModel):
    question_id: str = Field(..., description="Identifier for question, e.g. Q1, Q2, Q3")
    question: str = Field(..., description="Question stem testing the concept")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 distinct answer choices (A, B, C, D text)")
    correct_answer: str = Field(..., description="The exact string matching one of the 4 options")
    objective_ids: List[str] = Field(..., min_length=1, description="Learning objective codes addressed by this question")
    supporting_quote: str = Field(..., description="Verbatim quote from the source text supporting the question and correct answer")
    cognitive_level: str = Field(default="Understand", description="Bloom level for question (Remember, Understand, Apply, Analyze)")

# 4. Dedicated Quiz Answer Key
class AnswerKeyItem(BaseModel):
    question_id: str = Field(..., description="Matching question identifier (Q1, Q2, Q3)")
    correct_option: str = Field(..., description="The exact correct answer option string matching the question")
    rationale: str = Field(..., description="Detailed explanation of why this answer is correct and why other distractors are incorrect")
    objective_ids: List[str] = Field(..., min_length=1, description="Objective IDs associated with this item")

class GeneratedQuizAnswerKey(BaseModel):
    items: List[AnswerKeyItem] = Field(..., min_length=3, max_length=3, description="Answer key entries matching each of the 3 quiz questions")

# 5. Differentiated Practice (Cognitive Demand)
class PracticeTask(BaseModel):
    title: str = Field(..., description="Title of the practice task")
    problem_statement: str = Field(..., description="Task instructions or problem for the student")
    solution_guidance: str = Field(..., description="Guided walkthrough or expected resolution criteria")
    objective_ids: List[str] = Field(..., min_length=1, description="Objective IDs addressed")
    supporting_quote: str = Field(..., description="Verbatim source quote supporting this task")
    bloom_level: str = Field(..., description="Bloom cognitive taxonomy: Remember, Understand, Apply, Analyze, Evaluate, Create")
    reasoning_step_count: int = Field(..., description="Number of distinct cognitive reasoning steps required (e.g., 1 for easy, 3+ for advanced)")
    concept_count: int = Field(..., description="Number of distinct concepts combined in this task")
    task_complexity: str = Field(..., description="e.g. Single-step direct recall vs Multi-step scenario transfer")
    difficulty_label: str = Field(..., description="'Easy' or 'Advanced'")

# 6. Concise Revision Sheet
class RevisionDefinition(BaseModel):
    term: str = Field(..., description="Key technical term from source")
    definition: str = Field(..., description="Concise definition grounded in source")

class GeneratedRevisionSheet(BaseModel):
    title: str = Field(..., description="Title of the revision sheet")
    key_concepts: List[str] = Field(default_factory=list, description="Bullet points summarizing core takeaways")
    definitions: List[RevisionDefinition] = Field(default_factory=list, description="Key terms and definitions")
    important_relationships: List[str] = Field(default_factory=list, description="Crucial relationships, equations, or contrast rules")
    key_example: str = Field(default="", description="Memory anchor example illustrating the main idea")
    common_mistakes: List[str] = Field(default_factory=list, description="Common misconceptions or pitfalls to avoid")
    objective_ids: List[str] = Field(default_factory=list, description="Objective IDs covered by this revision sheet")
    supporting_quote: str = Field(default="", description="Verbatim source quote grounding the revision sheet")

# Complete Connected Learning Pack Schema (7 Assets)
class CompleteLearningPackSchema(BaseModel):
    concept_explanation: GeneratedConceptExplanation
    worked_example: GeneratedWorkedExample
    quiz_questions: List[GeneratedQuizQuestion] = Field(..., min_length=3, max_length=3, description="Exactly 3 formative quiz questions")
    quiz_answer_key: GeneratedQuizAnswerKey
    easy_practice: PracticeTask
    advanced_practice: PracticeTask
    revision_sheet: GeneratedRevisionSheet

# Backward-compatibility alias for Milestone 0
class Milestone0StructuredPack(BaseModel):
    concept_explanation: GeneratedConceptExplanation
    quiz_questions: List[GeneratedQuizQuestion] = Field(..., min_length=3, max_length=3)
