import time
from src.core.orchestrator.state import ProjectState, Requirement, AgentResponse
from src.core.rag.engine import FinancialRAG
from src.agents.interaction.agent import InteractionAgent
from src.agents.extraction.agent import ExtractionAgent
from src.agents.analysis.agent import AnalysisAgent
from src.agents.compliance.agent import ComplianceAgent
from src.agents.documentation.agent import DocumentationAgent
from src.core.sdlc_engine.engine import SDLCEngine
from src.agents.approval.agent import HumanApprovalAgent
from src.core.security.guard import SecurityAgent

class FinancialRequirementSystem:
    """
    The Main Orchestrator that executes the 20-step workflow.
    """
    def __init__(self):
        self.security = SecurityAgent()
        self.rag = FinancialRAG()
        self.interaction = InteractionAgent(self.rag)
        self.extraction = ExtractionAgent()
        self.analysis = AnalysisAgent()
        self.compliance = ComplianceAgent(self.rag)
        self.docs = DocumentationAgent()
        self.sdlc = SDLCEngine()
        self.approval = HumanApprovalAgent()

    def run_pipeline(self, project_id: str, stakeholder_role: str, raw_input: str):
        print(f"\n--- Starting Agentic Workflow for Project: {project_id} ---")
        state = ProjectState(project_id)

        # 1. Security Guard
        safe_input = self.security.mask_data(raw_input)
        if self.security.check_prompt_injection(safe_input):
            return "Security Alert: Prompt injection detected!"

        # 2. Interaction & Extraction
        print("[Step 7-8] Gathering & Extracting...")
        self.interaction.conduct_interview(state, stakeholder_role, safe_input)
        self.extraction.extract(state, safe_input, stakeholder_role)

        # 3. Analysis & Compliance
        print("[Step 9-11] Analyzing Quality & Compliance...")
        self.analysis.analyze_quality(state)
        self.compliance.map_compliance(state)

        # 4. Artifact Generation
        print("[Step 12] Generating Artifacts...")
        srs = self.docs.generate_srs(state)
        rtm = self.docs.generate_rtm(state)

        # 5. SDLC Selection
        print("[Step 13-15] Recommending SDLC...")
        factors = self.sdlc.extract_factors(state)
        model, justification, score = self.sdlc.recommend_model(factors)
        workflow = self.sdlc.generate_workflow(model)

        # 6. Final Approval
        print("[Step 16] Final Human Approval...")
        if self.approval.verify_baseline(state):
            state.approved_baseline = True
            print("Project Baseline Approved!")

        return {
            "srs": srs,
            "rtm": rtm,
            "sdlc_model": model,
            "sdlc_justification": justification,
            "sdlc_workflow": workflow,
            "requirements_count": len(state.requirements)
        }

if __name__ == "__main__":
    # Test Run
    sys = FinancialRequirementSystem()
    result = sys.run_pipeline(
        project_id="BANK-KYC-2026",
        stakeholder_role="Compliance Officer",
        raw_input="The system shall require step-up authentication for transactions exceeding 10000 dollars to comply with AML laws. Contact me at admin@bank.com"
    )
    print("\n--- FINAL RESULT ---")
    print(f"SDLC Model: {result['sdlc_model']}")
    print(f"Justification: {result['sdlc_justification']}")
    print(f"Workflow: {result['sdlc_workflow']}")
    print(f"Requirements Processed: {result['requirements_count']}")
    print("\nSRS Preview:\n", result['srs'])
