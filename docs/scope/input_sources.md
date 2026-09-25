# Input Sources Definition
Version: 1.0
Date: 2026-09-25

## 1. Unstructured Input Sources
The system shall ingest and process the following unstructured data:
- **Conversations:** Transcripts from stakeholder interviews, Zoom/Teams meeting notes.
- **Communications:** Email threads, Slack/Teams chat logs.
- **Documentation:** Meeting minutes, rough requirement drafts, handwritten notes (via OCR).
- **Feedback:** Customer survey responses, incident reports, audit findings.

## 2. Structured Input Sources
The system shall ingest and process the following structured/semi-structured data:
- **Requirements Documents:** Existing PRDs, SRS documents, BRDs.
- **Policy Frameworks:** Internal banking policies, organizational procedures.
- **Regulatory Bodies:** Legal texts from regulators (e.g., SEC, ECB, FCA), compliance manuals.
- **Technical Specs:** API Swagger/OpenAPI files, database ER diagrams, system architecture diagrams.
- **Legacy Docs:** Old system manuals, COBOL/Mainframe documentation.

## 3. Data Processing Pipeline for Sensitive Information
To ensure security and privacy, all inputs must pass through a **Preprocessing Layer** before reaching the LLM:
1. **Classification:** Identify PII (Personally Identifiable Information) and SPI (Sensitive Personal Information).
2. **Masking/Anonymization:** 
   - Replace names with tokens (e.g., `[CUSTOMER_1]`).
   - Mask account numbers (e.g., `XXXX-XXXX-1234`).
   - Redact specific financial balances or internal secrets.
3. **Filtering:** Remove irrelevant noise and non-essential metadata.
4. **Validation:** Ensure the input format is compatible with the agent's extraction logic.
