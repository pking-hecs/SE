# Custom SDLC Workflow Generation
Version: 1.0

## 1. Customization Logic
Once a model is selected, the system generates a **Project-Specific Workflow**.

### Workflow Components:
- **Phases:** (e.g., Inception $\rightarrow$ Design $\rightarrow$ Security Review $\rightarrow$ Dev $\rightarrow$ UAT $\rightarrow$ Compliance Audit $\rightarrow$ Release).
- **Activities:** Detailed tasks per phase (e.g., "Threat Modeling" in Design phase).
- **Roles:** Responsibility matrix (RACI) for each activity.
- **Validation Gates:** Exit criteria for each phase (e.g., "Compliance sign-off on Data Privacy Impact Assessment").
- **Security Controls:** Integration of SAST/DAST/Pen-testing into the pipeline.

## 2. Example: Financial-Grade DevSecOps Workflow
1. **Backlog Grooming:** (Includes Compliance Review).
2. **Sprint Planning:** (Includes Security User Stories).
3. **Development:** (Includes IDE-level linting + Secret scanning).
4. **CI Pipeline:** (Build $\rightarrow$ Unit Test $\rightarrow$ SAST $\rightarrow$ Dependency Check).
5. **Staging:** (DAST $\rightarrow$ Transactional Integrity Tests).
6. **Governance Gate:** (Human sign-off by Risk/Compliance officer).
7. **Production:** (Canary deployment + Real-time Audit logging).
