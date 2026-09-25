# SDLC Selection Engine Specification
Version: 1.0

## 1. Decision Factor Extraction
The SDLC Selection Agent analyzes the final requirement set to extract the following factors:
- **Requirement Stability:** (High/Low) based on the number of changes during the gathering phase.
- **Regulatory Criticality:** (Critical/Standard) based on the number of 'Hard' compliance mappings.
- **Technical Risk:** (High/Low) based on legacy system dependencies and new tech.
- **Complexity:** (High/Medium/Low) based on the total number of requirements and integrations.
- **Change Frequency:** (High/Low) based on business volatility.
- **Verification Need:** (Formal/Standard) based on safety/financial risk of failure.

## 2. Selection Mechanism (Hybrid Approach)
The engine uses a **Weighted Scoring Model** combined with LLM justification:

| Model | High Weight Factors | Low Weight Factors |
| :--- | :--- | :--- |
| **Waterfall** | Stability, Formal Approval, Fixed Scope | Change Frequency, Uncertainty |
| **Agile** | Change Frequency, Stakeholder Availability | Regulatory Criticality (Strict) |
| **V-Model** | Strict Verification, High Regulatory Risk | Speed of Delivery |
| **Spiral** | High Technical Risk, Prototyping Need | Low Budget, Simple Scope |
| **DevSecOps** | Continuous Delivery, Security Priority | Low Change Frequency |

## 3. Output Format
The engine produces a **Ranked Recommendation**:
1. **Primary Recommendation:** (e.g., Hybrid Agile-V-Model - 92%)
2. **Justification:** "Selected due to high regulatory criticality (Basel III) requiring formal verification, but high business volatility requiring iterative feature delivery."
3. **Alternative:** (e.g., V-Model - 70%)
