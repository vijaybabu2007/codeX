# LessonFoundry: Milestone 1
**Constraint-Aware Learning Asset Generation Studio**
*YUVA Megathon 2026 EduGenAI*

---
TEAM DETAILS:
1.VIJAY AB,[9042426460],[vijaybabu392007@gmail.com]
2.SHANMUGANATHAN,[9487260768],[sannathan07@gmail.com]
3.VISHWAJITH S,[9363641200],[vishwa.cse4@gmail.com]

## Overview

LessonFoundry turns one trusted teaching source into a complete, internally consistent learning pack while preventing the AI from freely inventing unsupported information.

### Milestone 1: The Connected Learning Pack (Round 2 Target)
Generates and deterministically validates all 7 core educational assets:
1. **Concept Explanation**
2. **Worked / Guided Example**
3. **Formative Practice Quiz (3 items)**
4. **Dedicated Quiz Answer Key**
5. **Easy Practice Task (Procedural Recall)**
6. **Advanced Practice Task (Multi-Step Synthesis)**
7. **Concise Revision Sheet**

Includes:
- **Bipartite Objective Alignment Matrix** (Uncovered objective & coverage imbalance detection)
- **Deterministic Quality Guardrails** (Duplicate detection, near-duplicate detection, answer leakage, cognitive difficulty inversion, malformed answer keys, revision-sheet grounding, terminology consistency, cross-asset contradictions)
- **Teacher Review Gate** (`DRAFT` → `NEEDS_REVISION` → `APPROVED` / `OVERRIDE`)
- **Server-Enforced Approved-Only Student Projection**

---

## Runtime Environment & Compatibility
- **Supported Python Versions:** Python 3.11 to 3.14 (Verified and tested on **Python 3.14.2**)
- **Platform:** Windows / Linux / macOS compatible
- **Database Engine:** SQLite 3 with Write-Ahead Logging (`WAL` mode)
- **Node.js:** v20+ (Verified on Node.js v24.19.0)

---

## Quickstart

### 1. Environment Configuration
Create a `.env` file in the project root:
```bash
GEMINI_MODEL=gemini-3.8-flash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Run Backend & Frontend (Unified Server)
The backend automatically serves both the API and the React SPA at `http://127.0.0.1:8000`:
```bash
.\venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://localhost:8000` in your browser.

Alternatively, for frontend hot-reload development:
```bash
cd frontend
npm run dev
```

### 3. Run Complete Automated Test Suite (30 Tests)
Execute all Milestone 0 and Milestone 1 tests:
```bash
.\venv\Scripts\python -m pytest -v tests/test_milestone0.py tests/test_milestone1.py
```
