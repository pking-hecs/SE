# Quality & Compliance Analysis Logic
Version: 1.0

## 1. Quality Check Heuristics (The "Analysis Agent")
Each requirement is scanned for the following "Red Flags":
- **Ambiguity:** Use of words like "fast", "user-friendly", "efficient", "appropriate".
- **Incompleteness:** Missing "who" or "under what condition".
- **Inconsistency:** Contradicts another requirement (e.g., "No external access" vs "API for partners").
- **Untestability:** Statements that cannot be verified by a test case.

## 2. Compliance Mapping Workflow (The "Compliance Agent")
1. **Keyword Trigger:** Identify keywords (e.g., "Personal Data" $\rightarrow$ GDPR).
2. **FKB Retrieval:** Fetch relevant articles from the Knowledge Base.
3. **Gap Analysis:** 
   - Compare Requirement $\leftrightarrow$ Regulation.
   - If Regulation requires X but Requirement only does Y $\rightarrow$ Flag **Compliance Gap**.
4. **Evidence Chain:** Link `Requirement ID` $\rightarrow$ `Regulation Article` $\rightarrow$ `FKB Source`.
