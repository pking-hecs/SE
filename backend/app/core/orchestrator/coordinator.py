import logging
from typing import List
from backend.app.core.orchestrator.state import ProjectState, RequirementSchema
from backend.app.agents.extraction_agent import extraction_agent
from backend.app.agents.quality_agent import quality_agent
from backend.app.agents.conflict_agent import conflict_agent
from backend.app.agents.compliance_agent import compliance_agent
from backend.app.agents.risk_agent import risk_agent

logger = logging.getLogger(__name__)

class CoordinatorAgent:
    """
    The central brain that manages the requirement engineering workflow.
    """
    async def process_inputs(self, state: ProjectState, new_input: str):
        logger.info(f"Coordinator: Processing input for project {state.project_id}")

        # 1. Add input to raw inputs
        state.raw_inputs.append(new_input)

        # 2. Extract Requirements
        logger.info("Coordinator: Routing to Extraction Agent")
        new_reqs = await extraction_agent.extract(new_input)
        state.requirements.extend(new_reqs)

        # 3. Quality Analysis
        logger.info("Coordinator: Routing to Quality Agent")
        quality_findings = await quality_agent.analyze(state.requirements)
        state.findings.extend(quality_findings)

        # 4. Conflict Detection
        logger.info("Coordinator: Routing to Conflict Agent")
        conflicts = await conflict_agent.detect_conflicts(state.requirements)
        state.findings.extend(conflicts)

        # 5. Compliance & Risk (Run for each new requirement)
        for req in new_reqs:
            logger.info(f"Coordinator: Analyzing Compliance & Risk for {req.requirement_id}")

            # Compliance RAG
            comp_findings = await compliance_agent.analyze_compliance(req, state.project_id)
            state.findings.extend(comp_findings)

            # Risk Score
            risk_finding = await risk_agent.evaluate_risk(req)
            state.findings.append(risk_finding)

        # 6. State Update
        # In a real implementation, we would save this state to Redis/DB here

        logger.info(f"Coordinator: Processed {len(new_reqs)} requirements and {len(state.findings)} total findings.")
        return state

coordinator_agent = CoordinatorAgent()
