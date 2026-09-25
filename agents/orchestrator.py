import os
import asyncio
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

load_dotenv()

class FinancialRequirementAgent:
    def __init__(self, role, goal):
        # Using 3B for quality, but we will optimize how we call it
        self.llm = OllamaLLM(model="llama3.2:3b", temperature=0)
        self.role = role
        self.goal = goal

    async def run_async(self, input_text):
        # Async wrapper to prevent the server from freezing
        prompt = (
            f"Role: {self.role}. Goal: {self.goal}.\n"
            f"Input: {input_text}\n\n"
            "Provide a professional, concise financial industry response. "
            "No preamble. No headers. Just the result."
        )
        try:
            # Using the async invoke method of OllamaLLM
            return await self.llm.ainvoke(prompt)
        except Exception as e:
            return f"Error: {str(e)}"

class AgentOrchestrator:
    def __init__(self):
        self.extractor = FinancialRequirementAgent("Senior Business Analyst", "Extract a detailed list of Functional, Non-Functional, and Security requirements.")
        self.compliance = FinancialRequirementAgent("Chief Compliance Officer", "Map requirements to financial regulations (GDPR, PCI-DSS) and identify risks.")
        self.sdlc = FinancialRequirementAgent("Software Architect", "Recommend the optimal SDLC model and justify it.")
        self.doc = FinancialRequirementAgent("Technical Writer", "Generate a professional SRS, User Stories, and a roadmap.")

    async def process_request_async(self, user_prompt):
        print("\n⚡ Starting Parallelized Professional Pipeline...")

        # STEP 1: Run Extraction and Compliance in PARALLEL
        print("🤖 Agents 1 & 2: Extracting & Compliance (Parallel)...", end=" ", flush=True)
        # We start both tasks at once
        req_task = self.extractor.run_async(user_prompt)
        comp_task = self.compliance.run_async(user_prompt)

        # Wait for both to finish
        reqs, comp = await asyncio.gather(req_task, comp_task)
        print("✅")

        # STEP 2: Run SDLC based on previous results
        print("🤖 Agent 3: Architecting SDLC...", end=" ", flush=True)
        sdlc = await self.sdlc.run_async(f"Requirements: {reqs}\nCompliance: {comp}")
        print("✅")

        # STEP 3: Run SRS based on everything
        print("🤖 Agent 4: Drafting SRS...", end=" ", flush=True)
        srs = await self.doc.run_async(f"Requirements: {reqs}\nSDLC: {sdlc}")
        print("✅")

        print("\n✨ Fast-Track Analysis Complete!\n")

        return {
            "requirements": reqs,
            "compliance": comp,
            "sdlc": sdlc,
            "srs_plan": srs
        }

    # Wrapper to call the async function from the synchronous FastAPI route
    def process_request(self, user_prompt):
        return asyncio.run(self.process_request_async(user_prompt))
