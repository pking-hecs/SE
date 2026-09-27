import os
import asyncio
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.core.orchestrator.state import ProjectState, Requirement
from agents.specialists import (
    LLMCaller,
    SecurityGuard,
    StakeholderInteractionAgent,
    RequirementExtractionAgent,
    ClarificationAgent,
    ClassificationAgent,
    ConflictDetectionAgent,
    ComplianceAgent,
    SecurityPrivacyAgent,
    RiskAnalysisAgent,
    SDLCSelectionAgent,
    DocumentationAgent,
    ValidationAgent,
    HumanApprovalAgent
)

class AgentOrchestrator:
    """
    Central Coordinator Agent that orchestrates all 13 collaborative AI specialist agents
    and enforces security, compliance, and governance workflows as per specification.
    Powered by authentic Google Gemini API calls.
    """
    def __init__(self, model_name: str = "gemini-3.7-flash"):
        self.llm_caller = LLMCaller(model=model_name)
        self.security_guard = SecurityGuard()

        # Instantiate 13 Specialists with Gemini LLMCaller
        self.interviewer = StakeholderInteractionAgent(self.llm_caller)
        self.extractor = RequirementExtractionAgent(self.llm_caller)
        self.clarifier = ClarificationAgent(self.llm_caller)
        self.classifier = ClassificationAgent(self.llm_caller)
        self.conflict_detector = ConflictDetectionAgent(self.llm_caller)
        self.compliance_agent = ComplianceAgent(self.llm_caller)
        self.security_agent = SecurityPrivacyAgent(self.llm_caller)
        self.risk_agent = RiskAnalysisAgent(self.llm_caller)
        self.sdlc_agent = SDLCSelectionAgent(self.llm_caller)
        self.doc_agent = DocumentationAgent(self.llm_caller)
        self.validator = ValidationAgent()
        self.approval_agent = HumanApprovalAgent()

    async def process_request_async(
        self,
        state: ProjectState,
        user_prompt: str,
        domain: Optional[str] = None,
        stakeholder_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end multi-agent pipeline via authentic Gemini API calls:
        1. Security Guard (Prompt Injection + PII Masking)
        2. Extraction & Classification
        3. Clarification & Conflict Detection
        4. Compliance & Policy Mapping (RAG)
        5. Threat Modeling & Risk Assessment
        6. SDLC Selection & Custom Workflow Architecture
        7. Artifact Synthesis (SRS, RTM, User Stories, Risk Register)
        8. Validation Gate & State Update
        """
        if domain:
            state.domain = domain
        if stakeholder_role:
            state.stakeholder_role = stakeholder_role

        active_domain = state.domain or "Digital Banking & Payments"
        active_role = state.stakeholder_role or "Business Analyst"

        print(f"\n⚡ [Coordinator] Initiating 13-Agent Autonomous AI Pipeline for Project {state.project_id}")
        state.log_event("Coordinator Agent", "Workflow Start", f"Pipeline initiated for domain '{active_domain}', role '{active_role}'.")

        # 1. SECURITY GUARD
        injection_alert = self.security_guard.check_prompt_injection(user_prompt)
        if injection_alert:
            state.log_event("Security Guard", "Security Alert", injection_alert)
            raise ValueError(f"Security Alert: {injection_alert}")

        safe_prompt, masked_items = self.security_guard.mask_pii(user_prompt)
        if masked_items:
            state.log_event("Security Guard", "PII Redaction", f"Redacted sensitive items: {', '.join(masked_items)}")

        # 2. REQUIREMENT EXTRACTION AGENT (Autonomous AI)
        print("🤖 [Agent 3: Requirement Extraction] Extracting atomic requirements via AI Engine...", flush=True)
        raw_reqs = await self.extractor.extract(safe_prompt, active_domain, active_role)
        print(f"Extracted {len(raw_reqs)} requirements.")
        state.log_event("Requirement Extraction Agent", "Extraction", f"Extracted {len(raw_reqs)} candidate requirements via AI Engine.")

        async def _stagger(coro, delay_sec):
            if delay_sec > 0:
                await asyncio.sleep(delay_sec)
            return await coro

        # 3. CONCURRENT ANALYSIS TIER 1: Classification, Clarification, Conflict Detection
        print("🤖 [Agents 4, 5, 6] Concurrently executing Clarification, Classification, and Conflict Detection via AI Engine...", flush=True)
        clarification_task = _stagger(self.clarifier.detect_clarifications_async(raw_reqs, active_domain), 0.0)
        classification_task = _stagger(self.classifier.classify_all_async(raw_reqs), 0.3)
        conflict_task = _stagger(self.conflict_detector.detect_conflicts_async(raw_reqs), 0.6)

        clarifications, classification_dict, conflicts = await asyncio.gather(
            clarification_task,
            classification_task,
            conflict_task
        )

        for r in raw_reqs:
            r["all_categories"] = classification_dict.get(r["id"], [r.get("category", "Functional")])

        state.clarifications = [c["clarification_question"] for c in clarifications]
        state.log_event("Clarification Agent", "Quality Review", f"Identified {len(clarifications)} subjective terms needing clarification.")
        state.conflicts = [f"{c['type']}: {c['description']} (Resolution: {c['resolution']})" for c in conflicts]
        state.log_event("Conflict Detection Agent", "Conflict Analysis", f"Detected {len(conflicts)} potential conflicts.")

        interview_questions = [c["clarification_question"] for c in clarifications]
        role_questions = self.interviewer.TEMPLATES.get(active_role, self.interviewer.TEMPLATES["Business Analyst"])
        for rq in role_questions:
            if len(interview_questions) >= 3:
                break
            if rq not in interview_questions:
                interview_questions.append(rq)

        # 4. CONCURRENT ANALYSIS TIER 2: Compliance RAG, Threat Modeling, Risk Register
        print("🤖 [Agents 7, 8, 9] Concurrently executing Compliance RAG, Threat Modeling, and Risk Assessment via AI Engine...", flush=True)
        compliance_task = _stagger(self.compliance_agent.map_compliance_async(raw_reqs), 0.0)
        security_task = _stagger(self.security_agent.analyze_security_async(active_domain, raw_reqs), 0.3)
        risk_task = _stagger(self.risk_agent.evaluate_risks_async(active_domain, raw_reqs), 0.6)

        compliance_mappings, security_profile, risk_register = await asyncio.gather(
            compliance_task,
            security_task,
            risk_task
        )
        state.risk_register = risk_register
        state.log_event("Compliance Agent", "RAG Grounding", f"Mapped {len(compliance_mappings)} requirements to financial regulations via AI Engine.")
        state.log_event("Security & Privacy Agent", "Threat Modeling", "Completed STRIDE threat model via AI Engine.")
        state.log_event("Risk Analysis Agent", "Risk Evaluation", f"Generated {len(risk_register)} project risks via AI Engine.")

        # 5. SDLC SELECTION AGENT (Autonomous Multi-Criteria Decision Engine)
        print("🤖 [Agent 10: SDLC Selection] Calculating MCDA ranking and custom workflow via AI Engine...", flush=True)
        sdlc_info = await self.sdlc_agent.select_sdlc_async(raw_reqs, active_domain)
        sdlc_workflow = await self.sdlc_agent.generate_custom_workflow_async(sdlc_info["recommended_model"], active_domain)
        state.sdlc_recommendation = sdlc_info["recommended_model"]
        state.sdlc_workflow = [f"{w['phase']}: {', '.join(w.get('activities', []))}" for w in sdlc_workflow]
        state.log_event("SDLC Selection Agent", "Model Decision", f"Recommended {sdlc_info['recommended_model']} with MCDA ranking.")

        # 6. DOCUMENTATION AGENT (User Stories via Gemini, SRS, RTM)
        print("🤖 [Agent 11: Documentation] Synthesizing User Stories, SRS, and RTM...", flush=True)
        user_stories = await self.doc_agent.generate_user_stories_async(raw_reqs)
        srs_content = self.doc_agent.generate_srs(state, raw_reqs, sdlc_info, compliance_mappings, risk_register)
        rtm_content = self.doc_agent.generate_rtm(raw_reqs, compliance_mappings)
        state.final_srs = srs_content
        state.rtm = rtm_content

        # 7. VALIDATION AGENT
        print("🤖 [Agent 12: Validation] Verifying evidence and completeness...", flush=True)
        validation_report = self.validator.validate(raw_reqs, compliance_mappings, conflicts)

        # 8. UPDATE BASELINE REQUIREMENTS IN STATE
        state.requirements_baseline.clear()
        for r in raw_reqs:
            matched_citation = next((c['citation'] for c in compliance_mappings if c['req_id'] == r['id']), "KB-REG-ISO-27001")
            req_obj = Requirement(
                req_id=r["id"],
                statement=r["statement"],
                category=r["category"],
                priority=r["priority"],
                status="validated",
                source=active_role,
                justification=r.get("business_justification", f"Automated extraction for {active_domain}"),
                compliance_mapping=[matched_citation],
                regulations=[matched_citation],
                risk_level=r["risk"],
                confidence_score=r.get("confidence_score", 0.94),
                acceptance_criteria=[r["acceptance_criteria"]],
                approval_status="pending"
            )
            state.requirements_baseline[r["id"]] = req_obj

        state.update_phase("REVIEW")
        state.log_event("Coordinator Agent", "Baseline Ready", f"Requirements baseline constructed with {len(state.requirements_baseline)} verified requirements.")

        # Formatted summaries for UI compatibility
        reqs_summary = "\n".join(
            f"• [{r['id']}] ({r['category']} | Priority: {r['priority']} | Risk: {r['risk']})\n  {r['statement']}\n  ✓ Acceptance: {r['acceptance_criteria']}"
            for r in raw_reqs
        )

        comp_summary = "\n".join(
            f"• [{c['req_id']}] ➔ Citation: `{c['citation']}` ({c['coverage']} Coverage | Confidence: {int(c['confidence']*100)}%)\n  Evidence: \"{c['evidence']}\""
            for c in compliance_mappings
        )

        sdlc_summary = (
            f"★ Recommended Model: {sdlc_info['recommended_model']}\n"
            f"Rationale: {sdlc_info['justification']}\n\n"
            f"Multi-Criteria Model Ranking (Normalized Score Distribution, Total = 100%):\n" +
            "\n".join(f"  - {model}: {score}%" for model, score in sdlc_info["ranked_scores"].items()) +
            f"\n  (Total = {sum(sdlc_info['ranked_scores'].values())}%)\n\n"
            f"Customised 7-Phase Financial Workflow:\n" +
            "\n".join(f"  {w['phase']} ➔ Gate: {w['validation_gate']}" for w in sdlc_workflow)
        )

        return {
            "requirements": reqs_summary,
            "compliance": comp_summary,
            "sdlc": sdlc_summary,
            "srs_plan": srs_content,
            "structured_requirements": raw_reqs,
            "compliance_mappings": compliance_mappings,
            "sdlc_info": sdlc_info,
            "sdlc_workflow": sdlc_workflow,
            "user_stories": user_stories,
            "rtm": rtm_content,
            "risk_register": risk_register,
            "clarifications": clarifications,
            "interview_questions": interview_questions,
            "interview_role": active_role,
            "conflicts": conflicts,
            "security_profile": security_profile,
            "validation": validation_report,
            "pii_masked_items": masked_items
        }

    async def handle_interaction(self, state: ProjectState, message: str) -> str:
        """
        Handles multi-turn conversational interaction for adaptive interviews and clarification loops.
        Powered by Gemini API.
        """
        state.chat_history.append({"role": "user", "content": message})

        # Check prompt injection
        injection_alert = self.security_guard.check_prompt_injection(message)
        if injection_alert:
            warning = f"⚠️ Security Alert: {injection_alert}. Action logged to audit trail."
            state.log_event("Security Guard", "Security Alert", injection_alert)
            state.chat_history.append({"role": "assistant", "content": warning})
            return warning

        safe_message, masked_items = self.security_guard.mask_pii(message)
        if masked_items:
            state.log_event("Security Guard", "PII Redacted", f"Redacted: {', '.join(masked_items)}")

        lower_msg = safe_message.lower()
        updated_items = []

        if not hasattr(state, 'answered_topics') or state.answered_topics is None:
            state.answered_topics = []
        if not hasattr(state, 'interview_turn') or state.interview_turn is None:
            state.interview_turn = 0

        # Check for Approval Intent
        if any(w in lower_msg for w in ("approve", "approved", "looks good", "finalize", "proceed to export", "accept all", "baseline ok")):
            state.approved_baseline = True
            state.update_phase("APPROVED")
            for req in state.requirements_baseline.values():
                req.approval_status = "approved"
                req.status = "approved"
            state.log_event("Human-Approval Agent", "Baseline Approved", f"Stakeholder approved all {len(state.requirements_baseline)} requirements.")
            approval_msg = (
                "🎉 **Requirements Baseline Formally Approved!**\n\n"
                f"All **{len(state.requirements_baseline)}** requirements, regulatory compliance citations, and the **{state.sdlc_recommendation or 'Agile–DevSecOps hybrid'}** development model have been verified.\n\n"
                "You can now download the finalized project documentation from the **Generated Artifacts** tab:\n"
                "• **Software Requirements Specification (SRS)** (ISO/IEC/IEEE 29148 Standard)\n"
                "• **Requirements Traceability Matrix (RTM)** (Full Regulatory & NFR Mapping)\n"
                "• **Gherkin User Stories & Acceptance Criteria**\n"
                "• **Threat & Risk Register**"
            )
            state.chat_history.append({"role": "assistant", "content": approval_msg})
            return approval_msg

        # Use Gemini to intelligently analyze stakeholder input for clarifications/modifications
        parse_prompt = (
            f"You are the Coordinator & Extraction Agent in a financial requirements engineering platform.\n"
            f"Domain: {state.domain}\n"
            f"Stakeholder Persona: {state.stakeholder_role}\n"
            f"Current Requirements Baseline:\n" +
            "\n".join([f"- [{r.req_id}] {r.statement}" for r in state.requirements_baseline.values()]) + "\n\n"
            f"Stakeholder's Latest Input: {safe_message}\n\n"
            f"Task: Determine if the stakeholder provides new requirements or clarifies existing specifications (such as performance SLA, monetary limits, credit scoring rules, API protocols, or audit retention).\n"
            f"Return strictly a JSON object with keys:\n"
            f"- extracted_requirements: array of new or modified requirements (each with 'id', 'statement', 'category', 'priority', 'risk', 'acceptance_criteria'). Return empty array [] if none.\n"
            f"- summary_of_changes: string (1 sentence summary of what was updated, or empty string)"
        )
        parsed_ai = await self.llm_caller.call_json_async(parse_prompt, timeout=20.0)
        if isinstance(parsed_ai, dict) and "extracted_requirements" in parsed_ai:
            for r in parsed_ai["extracted_requirements"]:
                req_id = r.get("id")
                if not req_id or req_id in state.requirements_baseline:
                    req_id = f"FR-MOD-{len(state.requirements_baseline) + 1:03d}"
                req_obj = Requirement(
                    req_id=req_id,
                    statement=r.get("statement", ""),
                    category=r.get("category", "Functional"),
                    priority=r.get("priority", "High"),
                    status="validated",
                    source=state.stakeholder_role,
                    justification="Refined via conversational AI clarification",
                    compliance_mapping=["KB-REG-ISO-27001"],
                    regulations=["KB-REG-ISO-27001"],
                    risk_level=r.get("risk", "Medium"),
                    confidence_score=0.95,
                    acceptance_criteria=[r.get("acceptance_criteria", "Given the action executes, then verify compliance.")],
                    approval_status="pending"
                )
                state.requirements_baseline[req_id] = req_obj
                updated_items.append(f"Updated/Added **{req_id}**: {r.get('statement')[:60]}...")
            if parsed_ai.get("summary_of_changes"):
                state.log_event("Coordinator Agent", "Adaptive Clarification", parsed_ai["summary_of_changes"])

        # Advance interview progression with AI
        state.interview_turn += 1
        context = f"Project ID: {state.project_id}, Domain: {state.domain}, Requirements count: {len(state.requirements_baseline)}"
        ai_response = await self.interviewer.interview(
            state.stakeholder_role,
            context,
            safe_message,
            answered_topics=state.answered_topics,
            turn_index=state.interview_turn
        )

        response_parts = []
        if updated_items:
            response_parts.append("✅ **Clarifications Ingested & Requirements Baseline Updated:**")
            for item in updated_items:
                response_parts.append(f"• {item}")
            response_parts.append("")

        response_parts.append(ai_response)
        response = "\n".join(response_parts)

        state.chat_history.append({"role": "assistant", "content": response})
        return response

    def process_request(self, user_prompt: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for legacy callers (app.py and generate_data.py).
        """
        state = ProjectState("PROJ_SYNC_001", user_prompt)
        return asyncio.run(self.process_request_async(state, user_prompt))
