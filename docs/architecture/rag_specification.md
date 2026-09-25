# RAG Implementation Specification
Version: 1.0

## 1. Technical Workflow
The Retrieval-Augmented Generation (RAG) pipeline follows these steps:
1. **Query Classification:** The Coordinator determines if the query needs grounding (e.g., "What are the AML requirements for cross-border payments?").
2. **Semantic Retrieval:** 
   - Convert query to embedding.
   - Search Vector Database (FKB) for top-k relevant policy/regulatory snippets.
3. **Context Construction:** 
   - Combine: `System Prompt` + `Retrieved Evidence` + `Stakeholder Query`.
4. **Grounded Generation:** LLM generates the response based *strictly* on the evidence.
5. **Verification:**
   - **Citations:** Every claim must have a reference to an FKB ID (e.g., `[KB-REG-001]`).
   - **Confidence Scoring:** Model outputs a confidence score (0.0-1.0).
6. **Escalation:** If confidence < 0.8 or no evidence found, route to Human-Approval Agent.

## 2. Prompt Template (Internal)
`You are a Financial Compliance Expert. Use the following excerpts from the Authorized Financial Knowledge Base to answer the query.`
`Evidence: {retrieved_context}`
`Query: {user_query}`
`Constraint: If the answer is not in the evidence, state 'Evidence not found' and escalate.`
