# Financial Knowledge Base (FKB) Specification
Version: 1.0
Date: 2026-09-25

## 1. Knowledge Domains
The FKB is a version-controlled repository categorized into the following domains:
- **Terminology:** Financial glossary, business process definitions (e.g., "KYC", "AML", "RTGS").
- **Policies:** Internal organizational controls, corporate governance.
- **Regulations:** Global and local laws (e.g., Basel III, GDPR, PSD2).
- **Standards:** Security standards (ISO 27001, PCI-DSS), Requirement Engineering guidelines.
- **SDLC Logic:** Deterministic rules for selecting development models.
- **Templates:** Approved formats for SRS, User Stories, and Use Cases.
- **Historical Data:** Previously approved project documents (for few-shot learning).

## 2. Data Structure (Schema)
Each item in the FKB must follow this metadata schema:
```json
{
  "id": "KB-REG-001",
  "title": "GDPR Article 25",
  "content": "Data protection by design and by default...",
  "category": "Regulatory",
  "jurisdiction": "EU",
  "effective_date": "2018-05-25",
  "version": "1.0",
  "applicability": ["Customer Data", "Privacy"],
  "source": "Official Journal of the European Union",
  "tags": ["privacy", "data-protection"]
}
```

## 3. Management & Governance
- **Version Control:** All changes tracked via Git.
- **Authorization:** Only Compliance/Legal officers can update Regulatory items.
- **Audit Trail:** Every update must be linked to a regulatory change notice.
- **Retrieval:** Indexed in a Vector Database for semantic search during RAG.
