import os
import asyncio
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from src.core.orchestrator.state import ProjectState, Requirement

load_dotenv()

class FinancialRequirementAgent:
    def __init__(self, role, goal):
        # Using 3B for quality
        self.llm = OllamaLLM(model="llama3.2:3b", temperature=0)
        self.role = role
        self.goal = goal

    async def run_async(self, input_text):
        prompt = (
            f"Role: {self.role}. Goal: {self.goal}.\n"
            f"Input: {input_text}\n\n"
            "Constraint: Provide a concise, professional response using bullet points. "
            "NO preamble, NO introductions, NO fluff. Max 200 words. "
            "Focus only on technical accuracy."
        )
        try:
            return await self.llm.ainvoke(prompt)
        except Exception as e:
            return f"Error: {str(e)}"

class AgentOrchestrator:
    def __init__(self):
        # Specialized Agents
        self.interviewer = FinancialRequirementAgent("Stakeholder Interaction Agent", "Conduct adaptive interviews to gather missing project details and clarify ambiguities.")
        self.extractor = FinancialRequirementAgent("Senior Business Analyst", "Extract a detailed list of Functional, Non-Functional, and Security requirements.")
        self.compliance = FinancialRequirementAgent("Chief Compliance Officer", "Map requirements to financial regulations (GDPR, PCI-DSS) and identify risks.")
        self.sdlc = FinancialRequirementAgent(
            "Software Architect",
            "Analyze project risks and recommend the optimal SDLC model. "
            "You MUST consider and differentiate between these specific models:\n"
            "- Waterfall: For fixed requirements and strict linear milestones.\n"
            "- V-Model: For mission-critical systems requiring strict verification/validation.\n"
            "- Spiral: For high-risk projects requiring iterative risk analysis.\n"
            "- Agile/Scrum: For changing requirements and fast feedback loops.\n"
            "- DevSecOps: For continuous secure deployment and rapid iteration.\n"
            "- RAG-Incremental Prototype: For AI-driven projects that evolve through iterative data retrieval, "
            "grounding improvement, and incremental knowledge base expansion.\n\n"
            "Justify the choice by explaining why the selected model outperforms the others for this financial case."
        )
        self.doc = FinancialRequirementAgent("Technical Writer", "Generate a professional SRS, User Stories, and a roadmap.")

    async def process_request_async(self, state: ProjectState, user_prompt: str):
        """
        The main pipeline that transforms a prompt into a set of requirements and an SDLC.
        Now updates the ProjectState object.
        """
        print(f"\n⚡ Processing Project {state.project_id} - Phase: {state.current_phase}")

        # STEP 1: Extraction and Compliance (Parallel)
        print("🤖 Agents: Extracting & Compliance (Parallel)...", end=" ", flush=True)
        req_task = self.extractor.run_async(user_prompt)
        comp_task = self.compliance.run_async(user_prompt)
        reqs, comp = await asyncio.gather(req_task, comp_task)
        print("✅")

        # Update State with baseline requirements (simulated extraction into Requirement objects)
        # In a production system, the extractor would return structured JSON
        state.requirements_baseline["REQ-001"] = Requirement(
            req_id="REQ-001",
            statement=reqs,
            category="General",
            priority="High"
        )
        state.log_event("Extractor Agent", "Extraction", "Initial requirements extracted from prompt.")
        state.log_event("Compliance Agent", "Compliance", f"Regulatory mapping completed: {comp[:100]}...")

        # STEP 2: SDLC Selection
        print("🤖 Agent: Architecting SDLC...", end=" ", flush=True)
        sdlc_rec = await self.sdlc.run_async(f"Requirements: {reqs}\nCompliance: {comp}")
        state.sdlc_recommendation = sdlc_rec
        print("✅")

        # STEP 3: Documentation
        print("🤖 Agent: Drafting SRS...", end=" ", flush=True)
        srs = await self.doc.run_async(f"Requirements: {reqs}\nSDLC: {sdlc_rec}")
        state.final_srs = srs
        print("✅")

        return {
            "requirements": reqs,
            "compliance": comp,
            "sdlc": sdlc_rec,
            "srs_plan": srs
        }

    async def handle_interaction(self, state: ProjectState, message: str):
        """
        Handles multi-turn dialogue based on the current project phase.
        """
        state.chat_history.append({"role": "user", "content": message})

        if state.current_phase == "INTERVIEWING":
            # Use the Interviewer agent to ask follow-up questions
            context = f"Initial Prompt: {state.initial_prompt}\nUser says: {message}\nRequirements so far: {state.requirements_baseline}"
            response = await self.interviewer.run_async(context)
            state.chat_history.append({"role": "assistant", "content": response})

            # Simple logic to transition phase: if user says 'complete' or 'enough'
            if any(word in message.lower() for word in ["complete", "enough", "done", "proceed"]):
                state.update_phase("ANALYZING")
                state.log_event("Coordinator", "Phase Transition", "Moved from INTERVIEWING to ANALYZING")
                return "I have enough information. Transitioning to the analysis phase. I will now refine the requirements and recommend an SDLC."

            return response

        elif state.current_phase == "ANALYZING":
            # In analysis phase, we might refine requirements based on feedback
            response = await self.extractor.run_async(f"Refine these requirements based on user feedback: {message}\nExisting: {state.requirements_baseline}")
            state.log_event("Extractor Agent", "Refinement", "Requirements updated based on user feedback.")
            state.chat_history.append({"role": "assistant", "content": response})
            return response

        else:
            # Default behavior
            response = await self.interviewer.run_async(f"Project context: {state.initial_prompt}. User message: {message}")
            return response

    def process_request(self, user_prompt):
        # Legacy support for sync calls (not used in session API)
        state = ProjectState("LEGACY", user_prompt)
        return asyncio.run(self.process_request_async(state, user_prompt))
