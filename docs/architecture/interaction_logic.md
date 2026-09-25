# Adaptive Interview Logic
Version: 1.0

## 1. Interaction Strategy
The Stakeholder Interaction Agent uses an **Adaptive Branching** approach rather than a static list.

### The Loop:
1. **Core Objective:** Start with a high-level goal (e.g., "Understand Loan Origination Workflow").
2. **Contextual Query:** Ask a targeted question from the template.
3. **Response Analysis:**
   - **Complete:** Move to the next objective.
   - **Vague:** Trigger the **Clarification Agent** $\rightarrow$ "You mentioned 'fast processing', can you define the exact maximum latency in seconds?"
   - **Inconsistent:** Compare with previous answers $\rightarrow$ "Earlier you said X, but now you say Y. Which is correct?"
4. **Deep Dive:** If a "Security" keyword is detected, pivot to the Security/Compliance template.

## 2. Conversation State Tracking
The agent maintains a session state:
- `Gathered_Objectives`: List of fulfilled goals.
- `Pending_Clarifications`: List of ambiguous points.
- `Stakeholder_Persona`: Role (e.g., Compliance Officer).
- `Detected_Risks`: High-level risks flagged during conversation.
