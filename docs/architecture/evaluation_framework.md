# Prototype & Evaluation Framework
Version: 1.0

## 1. Prototype Scope (Initial Use Case)
**Focus:** Digital Customer Onboarding & KYC.
- **Inputs:** KYC regulations, internal onboarding policy, stakeholder interviews.
- **Outputs:** KYC SRS, User Stories for ID verification, SDLC recommendation.

## 2. Evaluation Metrics (The "Scorecard")
The system's effectiveness is measured against manual baseline:
- **Extraction Precision:** (Correct Requirements / Total Extracted).
- **Regulatory Coverage:** (% of mandatory controls from FKB present in SRS).
- **Hallucination Rate:** (% of claims without valid FKB citations).
- **Ambiguity Rate:** (% of requirements flagged by human as "vague" vs AI flagged).
- **SDLC Accuracy:** Alignment between AI recommendation and Architect's decision.
- **Time Efficiency:** (Manual hours - AI hours).

## 3. Evaluation Process
1. **Blind Test:** Humans and AI analyze the same case study.
2. **Review:** Experts grade the AI's SRS for completeness and correctness.
3. **Gap Analysis:** Identify where AI missed regulatory controls.
4. **Iterate:** Update FKB and prompts based on failures.
