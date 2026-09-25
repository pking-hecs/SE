# Extraction & Structuring Specification
Version: 1.0

## 1. Transformation Logic
The Extraction Agent transforms natural language into a JSON structure:

### Schema:
```json
{
  "req_id": "FR-PAY-XXX",
  "statement": "The system shall...",
  "category": "Functional",
  "source": "Stakeholder_Name",
  "justification": "Regulatory Requirement KB-REG-005",
  "priority": "Must-Have",
  "dependencies": ["FR-PAY-001"],
  "assumptions": [],
  "acceptance_criteria": ["Criterion 1", "Criterion 2"],
  "regulations": ["GDPR Art 25"],
  "risk_level": "Medium",
  "confidence_score": 0.95,
  "status": "Draft"
}
```

## 2. Multi-Label Classification
The Classification Agent assigns labels from the following taxonomy:
- **Business:** High-level goals.
- **Functional:** System behaviors.
- **Security:** Access control, encryption.
- **Privacy:** Data handling, consent.
- **Regulatory:** Law-mandated features.
- **Performance:** Latency, throughput.
- **Availability:** Uptime, DR.
- **Audit:** Logging, reporting.
- **Operational:** Backup, monitoring.
