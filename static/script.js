let currentProjectId = null;
let projectData = null;
let currentRequirements = [];
let editingReqId = null;

// ---------------------------
// THEME MANAGEMENT (LIGHT / DARK)
// ---------------------------
function initTheme() {
    const saved = localStorage.getItem('finreq-theme') || 'dark';
    applyTheme(saved);
}

function toggleTheme() {
    const isLight = document.body.classList.contains('light-theme');
    const newTheme = isLight ? 'dark' : 'light';
    applyTheme(newTheme);
    localStorage.setItem('finreq-theme', newTheme);
}

function applyTheme(theme) {
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');
    if (theme === 'light') {
        document.body.classList.add('light-theme');
        document.documentElement.classList.add('light-theme');
        if (icon) icon.className = 'fas fa-moon text-blue-700';
        if (text) text.textContent = 'Dark';
    } else {
        document.body.classList.remove('light-theme');
        document.documentElement.classList.remove('light-theme');
        if (icon) icon.className = 'fas fa-sun text-amber-500';
        if (text) text.textContent = 'Light';
    }
}

document.addEventListener('DOMContentLoaded', initTheme);

const PRESETS = {
    loan: {
        domain: "Loan Origination & Credit Assessment",
        role: "Business Analyst",
        prompt: "An automated SME loan origination and risk assessment platform. The system shall evaluate borrower credit scores using credit bureau APIs, calculate debt-to-income ratios, enforce Basel III capital liquidity buffers, and disburse digital loan contracts with dual-authorization for loans exceeding $50,000."
    },
    kyc: {
        domain: "Customer Onboarding & KYC",
        role: "Compliance Officer",
        prompt: "A digital customer onboarding system for retail and SME banking. The system shall verify government identity documents using biometric liveness detection, screen applicants against OFAC and PEP sanction lists, adhere to GDPR Article 25 data protection by design, and notify compliance officers within 72 hours of any security incident."
    },
    payments: {
        domain: "Payment Processing & ISO 20022",
        role: "Information-Security Team",
        prompt: "A high-throughput cross-border payment gateway processing ISO 20022 messages. The system shall encrypt all cardholder and account data using AES-256 at rest and TLS 1.3 in transit, require step-up MFA for transfers exceeding $10,000, enforce sub-500ms transaction settlement, and maintain immutable WORM audit logs for 7 years."
    },
    fraud: {
        domain: "Fraud Detection & Real-Time AML",
        role: "Risk-Management Team",
        prompt: "A real-time fraud detection and transaction monitoring engine. The system shall analyze card transactions with sub-100ms latency, generate automated Suspicious Activity Reports (SAR), screen transactions against AML thresholds, and block anomalous geographic withdrawal patterns."
    }
};

function loadPreset(key) {
    const p = PRESETS[key];
    if (!p) return;
    document.getElementById('domain-select').value = p.domain;
    document.getElementById('role-select').value = p.role;
    document.getElementById('user-input').value = p.prompt;
    document.getElementById('user-input').focus();
}

function escapeHTML(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function formatMarkdown(text) {
    if (!text) return '';
    let safe = escapeHTML(text);
    // Replace **bold** with <strong>bold</strong>
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-inherit">$1</strong>');
    // Replace *italic* with <em>italic</em>
    safe = safe.replace(/\*(.*?)\*/g, '<em class="text-slate-400">$1</em>');
    // Replace `code` with styled <code>
    safe = safe.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded badge-blue font-mono text-xs">$1</code>');
    // Bullet points • or - at line start
    safe = safe.replace(/^[•\-] (.*)$/gm, '<div class="flex items-start gap-2 my-1"><span class="text-blue-600 font-bold">•</span><span>$1</span></div>');
    // Numbered items: 1.
    safe = safe.replace(/^(\d+)\.\s+(.*)$/gm, '<div class="flex items-start gap-2 my-1"><span class="text-blue-600 font-bold">$1.</span><span>$2</span></div>');
    // Line breaks
    safe = safe.replace(/\n/g, '<br>');
    return safe;
}

window.fillChatInput = function(text) {
    const input = document.getElementById('user-input');
    if (input) {
        input.value = text;
        input.focus();
    }
};

function switchTab(tabId) {
    const tabs = ['requirements', 'compliance', 'sdlc', 'risks', 'clarifications', 'artifacts', 'audit'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const content = document.getElementById(`tab-content-${t}`);
        if (btn) btn.classList.toggle('active', t === tabId);
        if (content) content.classList.toggle('hidden', t !== tabId);
    });
}

function setAgentsActive(active) {
    const agentIds = [
        'coordinator', 'interaction', 'extraction', 'clarification',
        'classification', 'conflict', 'compliance', 'security',
        'risk', 'sdlc', 'doc', 'validator', 'approval'
    ];
    agentIds.forEach((id, index) => {
        const el = document.getElementById(`agent-${id}`);
        if (!el) return;
        if (active) {
            setTimeout(() => {
                el.className = "p-2 rounded-xl inner-card !border-blue-600 font-semibold shadow-md text-blue-600 transition-all";
            }, index * 60);
        } else {
            el.className = "p-2 rounded-xl inner-card text-xs font-medium transition-all shadow-sm";
        }
    });
}

async function handleSend(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('user-input');
    const prompt = input.value.trim();
    if (!prompt) return;

    input.value = '';
    appendChatMessage('user', prompt);

    const loadingId = 'loading-' + Date.now();
    appendChatMessage('assistant', '<div class="flex items-center gap-2 text-slate-400 text-xs"><i class="fas fa-circle-notch fa-spin text-sky-400"></i> Autonomous multi-agent pipeline executing...</div>', loadingId);

    setAgentsActive(true);
    document.getElementById('pipeline-status').innerHTML = '<span class="w-2 h-2 rounded-full bg-sky-400 pulse-badge"></span> Orchestrating 13 Specialists...';

    const domain = document.getElementById('domain-select').value;
    const role = document.getElementById('role-select').value;

    try {
        let endpoint = '/session/chat';
        let body = { project_id: currentProjectId, message: prompt, stakeholder_role: role };

        if (!currentProjectId) {
            endpoint = '/session/start';
            body = {
                prompt: prompt,
                domain: domain,
                stakeholder_role: role
            };
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const result = await response.json();
        document.getElementById(loadingId)?.remove();
        setAgentsActive(false);

        if (!response.ok || result.status !== 'success') {
            document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Error encountered';
            appendChatMessage('assistant', `❌ Error: ${escapeHTML(result.detail || 'Request failed')}`);
            return;
        }

        document.getElementById('pipeline-status').innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span> All 13 agents validated';

        if (result.project_id && !currentProjectId) {
            currentProjectId = result.project_id;
            document.getElementById('active-project-tag').textContent = currentProjectId;
        }

        // Render Initial Analysis
        if (result.initial_analysis) {
            const data = result.initial_analysis;
            projectData = data;
            currentRequirements = data.structured_requirements || [];

            // PII alert check
            if (data.pii_masked_items && data.pii_masked_items.length > 0) {
                const alertBar = document.getElementById('security-alert-bar');
                const alertText = document.getElementById('security-alert-text');
                alertText.innerHTML = `<i class="fas fa-shield-halved mr-1.5 text-amber-400"></i> Redacted Sensitive PII: <strong>${data.pii_masked_items.join(', ')}</strong> before agent processing.`;
                alertBar.classList.remove('hidden');
            }

            renderRequirements(currentRequirements);
            renderCompliance(data.compliance_mappings || []);
            renderSDLC(data.sdlc_info, data.sdlc_workflow || []);
            renderRisks(data.risk_register || []);
            renderClarifications(data.clarifications || [], data.conflicts || []);
            renderArtifacts(data.srs_plan);
            renderAuditTrail(result.audit_trail || []);

            // Build clarification & interview questions HTML
            let questions = data.interview_questions || [];
            if (!questions || questions.length === 0) {
                if (data.clarifications && data.clarifications.length > 0) {
                    questions = data.clarifications.map(c => c.clarification_question || c);
                }
            }
            if (!questions || questions.length === 0) {
                const roleQuestions = {
                    "Business Analyst": [
                        "What are the target peak Transactions Per Second (TPS) and 99th-percentile (p99) latency SLA targets?",
                        "What is the maximum single-transaction limit, and what amount threshold triggers step-up MFA or dual four-eyes approval?",
                        "Which specific messaging protocols or APIs (e.g. ISO 20022 PACS.008 over SWIFT, REST, IBM MQ) connect to legacy core banking?"
                    ],
                    "Compliance Officer": [
                        "Which regulatory jurisdictions apply (e.g., EU GDPR, US BSA/AML, UK FCA, Basel III/IV)?",
                        "What specific customer due diligence (CDD) and Suspicious Activity Report (SAR) triggers are required?",
                        "What are the statutory retention periods and immutable audit logging mandates?"
                    ],
                    "Information-Security Team": [
                        "What encryption standards are required at rest (e.g. AES-256) and in transit (TLS 1.3)?",
                        "What step-up authentication or Hardware Security Module (HSM) controls must be in place?",
                        "What are the disaster recovery RTO and RPO SLA requirements?"
                    ],
                    "Risk-Management Team": [
                        "What risk threshold determines mandatory four-eyes dual authorization?",
                        "What are the operational risk limits and real-time fraud scoring tolerance levels?",
                        "How should systemic liquidity and counterparty risk exposure be monitored?"
                    ]
                };
                questions = roleQuestions[role] || roleQuestions["Business Analyst"];
            }

            let questionsHtml = '';
            if (questions && questions.length > 0) {
                questionsHtml = `
                    <div class="mt-3.5 p-4 rounded-2xl inner-card space-y-3 shadow-md border-blue-600/40">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2 text-blue-600 font-bold text-xs uppercase tracking-wide">
                                <i class="fas fa-clipboard-question"></i>
                                <span>Adaptive Clarification Interview (Stakeholder: ${escapeHTML(role)})</span>
                            </div>
                            <span class="text-[10px] px-2.5 py-0.5 rounded-full badge-blue font-semibold">Input Needed</span>
                        </div>
                        <p class="text-xs text-slate-400 leading-normal">
                            The Clarification & Interaction Agents identified missing parameters and ambiguity. Please clarify the following:
                        </p>
                        <div class="space-y-2">
                            ${questions.slice(0, 3).map((q, idx) => `
                                <div class="p-3 rounded-xl inner-card text-xs">
                                    <div class="font-bold text-blue-600 mb-1 flex items-center gap-1.5">
                                        <i class="fas fa-circle-question text-blue-600 text-xs"></i>
                                        <span>Clarification Question ${idx + 1}:</span>
                                    </div>
                                    <div class="leading-relaxed pl-4 theme-title">${escapeHTML(q)}</div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="pt-2.5 border-t border-slate-700/40">
                            <div class="text-xs text-slate-400 mb-2 flex items-center gap-1.5">
                                <i class="fas fa-lightbulb text-amber-600 text-xs"></i>
                                <span>Quick-fill answer templates (click to pre-fill chat):</span>
                            </div>
                            <div class="flex flex-wrap gap-2">
                                <button type="button" onclick="fillChatInput('Peak throughput is 5,000 TPS with p99 latency < 150ms. Step-up MFA threshold is $10,000. Core banking connects via IBM MQ using ISO 20022 PACS.008.')" class="preset-chip text-xs px-3 py-1.5 rounded-xl transition font-medium cursor-pointer text-left shadow-sm">
                                    ⚡ <strong>Payment SLAs:</strong> 5,000 TPS, &lt;150ms, $10k MFA, IBM MQ
                                </button>
                                <button type="button" onclick="fillChatInput('Statutory retention is 7 years immutable audit trail. Mandatory four-eyes dual authorization for transfers exceeding $50,000.')" class="preset-chip text-xs px-3 py-1.5 rounded-xl transition font-medium cursor-pointer text-left shadow-sm">
                                    🛡️ <strong>Compliance:</strong> 7-yr retention, $50k dual auth
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }

            appendChatMessage('assistant', `
                <div class="space-y-3">
                    <div class="p-3.5 rounded-2xl badge-green text-sm shadow-md font-medium">
                        <i class="fas fa-check-circle mr-1.5 text-emerald-600"></i> <strong>Initial Analysis Complete:</strong> Extracted <strong>${currentRequirements.length}</strong> requirements, mapped <strong>${data.compliance_mappings.length}</strong> regulatory citations, and selected <strong>${data.sdlc_info.recommended_model}</strong>.
                    </div>
                    <p class="text-sm leading-relaxed theme-title">
                        I've structured the baseline across your selected domain (<strong>${escapeHTML(domain)}</strong>).
                        Review the generated requirements in the right panel, and answer the clarification questions below to refine the specifications:
                    </p>
                    ${questionsHtml}
                </div>
            `);
        } else if (result.response) {
            appendChatMessage('assistant', `<div class="text-sm leading-relaxed theme-title">${formatMarkdown(result.response)}</div>`);
            if (result.audit_trail) {
                renderAuditTrail(result.audit_trail);
            }
            if (result.requirements) {
                currentRequirements = Object.values(result.requirements);
                renderRequirements(currentRequirements);
            }
        }

    } catch (err) {
        document.getElementById(loadingId)?.remove();
        setAgentsActive(false);
        document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-red-600"></span> Connection error';
        appendChatMessage('assistant', `❌ Connection failure: Could not reach the FinReq AI backend.`);
    }
}

function appendChatMessage(role, htmlContent, id = null) {
    const chatWindow = document.getElementById('chat-window');
    const wrapper = document.createElement('div');
    wrapper.className = `flex items-start gap-3 ${role === 'user' ? 'justify-end' : 'justify-start'}`;
    if (id) wrapper.id = id;

    if (role === 'user') {
        wrapper.innerHTML = `
            <div class="inner-card p-3.5 max-w-lg text-sm leading-relaxed shadow-md">
                ${escapeHTML(htmlContent)}
            </div>
            <div class="w-9 h-9 rounded-2xl bg-blue-700 flex-shrink-0 flex items-center justify-center text-white text-xs font-bold shadow-md">
                U
            </div>
        `;
    } else {
        wrapper.innerHTML = `
            <div class="w-9 h-9 rounded-2xl bg-slate-700 flex-shrink-0 flex items-center justify-center text-white text-xs font-bold shadow-md">
                AI
            </div>
            <div class="inner-card p-4 max-w-xl text-sm leading-relaxed shadow-md">
                ${htmlContent}
            </div>
        `;
    }

    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const countEl = document.getElementById('chat-count');
    countEl.textContent = chatWindow.children.length;
}

// ---------------------------
// TAB RENDERING FUNCTIONS
// ---------------------------

function renderRequirements(reqs) {
    document.getElementById('req-count').textContent = reqs.length;
    const container = document.getElementById('requirements-list');
    if (!reqs.length) {
        container.innerHTML = `<div class="text-center py-12 text-slate-400 text-sm font-medium">No requirements available in baseline.</div>`;
        return;
    }

    container.innerHTML = reqs.map((r, idx) => {
        const id = r.id || r.req_id || `REQ-${idx + 1}`;
        const isApproved = r.approval_status === 'approved' || r.status === 'approved';
        const isHighPrio = (r.priority || '').toLowerCase() === 'high';
        const prioBadge = isHighPrio
            ? '<span class="text-xs px-2.5 py-0.5 rounded-lg badge-red font-semibold">High Priority</span>'
            : '<span class="text-xs px-2.5 py-0.5 rounded-lg badge-amber font-semibold">Medium Priority</span>';

        const statusBadge = isApproved
            ? '<span class="text-xs px-2.5 py-0.5 rounded-full badge-green font-semibold flex items-center gap-1"><i class="fas fa-circle-check"></i> Approved</span>'
            : '<span class="text-xs px-2.5 py-0.5 rounded-full badge-blue font-medium">Pending Sign-off</span>';

        return `
            <div class="p-4 rounded-2xl inner-card ${isApproved ? '!border-emerald-600' : ''} shadow-md transition space-y-3">
                <div class="flex items-center justify-between flex-wrap gap-2.5">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="font-mono text-xs font-bold badge-blue px-2.5 py-1 rounded-xl">${escapeHTML(id)}</span>
                        <span class="text-xs px-2.5 py-0.5 rounded-full badge-blue font-medium">${escapeHTML(r.category || 'Functional')}</span>
                        ${prioBadge}
                        ${statusBadge}
                        <span class="text-xs text-slate-400">Risk: <strong class="${(r.risk || r.risk_level) === 'High' ? 'text-red-600' : 'text-amber-600'}">${escapeHTML(r.risk || r.risk_level || 'Medium')}</strong></span>
                    </div>

                    <!-- Action Buttons: Approve, Remove, Edit -->
                    <div class="flex items-center gap-2">
                        ${isApproved ? `
                            <button onclick="approveSingleReq('${id}', 'draft')" class="text-xs px-3 py-1.5 rounded-xl bg-emerald-800 hover:bg-emerald-700 text-white font-semibold transition flex items-center gap-1 shadow-sm" title="Click to undo approval">
                                <i class="fas fa-check-double mr-1"></i> Approved
                            </button>
                        ` : `
                            <button onclick="approveSingleReq('${id}', 'approved')" class="btn-approve text-xs px-3 py-1.5 rounded-xl font-semibold transition flex items-center gap-1 shadow-sm" title="Approve this requirement">
                                <i class="fas fa-check mr-1"></i> Approve
                            </button>
                        `}
                        <button onclick="removeSingleReq('${id}')" class="btn-remove text-xs px-3 py-1.5 rounded-xl font-semibold transition flex items-center gap-1 shadow-sm" title="Remove requirement from baseline">
                            <i class="fas fa-trash-can mr-1"></i> Remove
                        </button>
                        <button onclick="openEditModal('${id}')" class="btn-secondary text-xs px-2.5 py-1.5 rounded-xl transition" title="Modify requirement">
                            <i class="fas fa-pen"></i>
                        </button>
                    </div>
                </div>

                <p class="text-sm theme-title leading-relaxed font-normal">${escapeHTML(r.statement)}</p>

                ${r.acceptance_criteria ? `
                    <div class="p-3 rounded-xl inner-card text-xs">
                        <span class="text-blue-600 font-bold font-mono">Acceptance Criteria:</span> ${escapeHTML(Array.isArray(r.acceptance_criteria) ? r.acceptance_criteria.join(' ') : r.acceptance_criteria)}
                    </div>
                ` : ''}

                ${(r.compliance_mapping || r.regulations) && (r.compliance_mapping?.length || r.regulations?.length) ? `
                    <div class="flex items-center gap-1.5 text-xs text-slate-400 flex-wrap">
                        <span class="font-semibold text-slate-400">Regulations:</span>
                        ${(r.compliance_mapping || r.regulations).map(reg => `
                            <span class="font-mono text-xs px-2.5 py-0.5 rounded-lg badge-blue">${escapeHTML(reg)}</span>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function renderCompliance(mappings) {
    const container = document.getElementById('compliance-list');
    if (!mappings.length) {
        container.innerHTML = `<div class="text-center py-16 text-slate-400 text-sm">No compliance mappings available.</div>`;
        return;
    }

    container.innerHTML = mappings.map(c => `
        <div class="p-4 rounded-2xl inner-card space-y-2.5 shadow-md">
            <div class="flex items-center justify-between flex-wrap gap-2">
                <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-bold badge-blue px-2.5 py-1 rounded-xl">${escapeHTML(c.req_id)}</span>
                    <span class="text-xs font-mono px-2.5 py-1 rounded-xl badge-red font-bold">${escapeHTML(c.citation)}</span>
                    <span class="text-xs text-slate-400">${escapeHTML(c.source_doc)}:${c.line_number}</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-xs px-2.5 py-0.5 rounded-lg badge-green font-medium">Coverage: ${escapeHTML(c.coverage)}</span>
                    <span class="text-xs px-2.5 py-0.5 rounded-lg badge-blue font-medium">${Math.round(c.confidence * 100)}% Confidence</span>
                </div>
            </div>
            <p class="text-xs italic inner-card p-3 rounded-xl leading-relaxed">
                "${escapeHTML(c.evidence)}"
            </p>
        </div>
    `).join('');
}

function renderSDLC(info, workflow) {
    if (!info) return;
    document.getElementById('sdlc-top-model').textContent = info.recommended_model;
    document.getElementById('sdlc-rationale').textContent = info.justification;

    // Normalize scores so the sum strictly equals 100%
    let scores = { ...(info.ranked_scores || {}) };
    let totalScore = Object.values(scores).reduce((a, b) => a + b, 0);
    if (totalScore > 0 && totalScore !== 100) {
        let normalized = {};
        for (let [m, s] of Object.entries(scores)) {
            normalized[m] = Math.round((s / totalScore) * 100);
        }
        let currentTotal = Object.values(normalized).reduce((a, b) => a + b, 0);
        let diff = 100 - currentTotal;
        if (diff !== 0) {
            let topKey = Object.keys(normalized)[0];
            normalized[topKey] += diff;
        }
        scores = normalized;
    }

    // Sort descending by score
    const entries = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    const topScore = entries.find(([m]) => m === info.recommended_model)?.[1] || entries[0]?.[1] || 0;
    const badgeEl = document.getElementById('sdlc-top-badge');
    if (badgeEl) {
        badgeEl.textContent = `${topScore}% Weight (Rank #1)`;
    }

    // Render Ranking Bars
    const barsContainer = document.getElementById('sdlc-ranking-bars');
    const barsHtml = entries.map(([model, score]) => {
        const isTop = model === info.recommended_model;
        const barColor = isTop ? 'bg-emerald-600' : 'bg-slate-500';
        return `
            <div>
                <div class="flex justify-between items-center mb-1 text-xs">
                    <span class="${isTop ? 'text-emerald-600 font-bold' : 'text-slate-400'}">${escapeHTML(model)} ${isTop ? '★' : ''}</span>
                    <span class="font-mono ${isTop ? 'text-emerald-600 font-bold' : 'text-slate-400'}">${score}%</span>
                </div>
                <div class="w-full h-2 rounded-full inner-card overflow-hidden">
                    <div class="h-full rounded-full ${barColor}" style="width: ${Math.max(score, 4)}%"></div>
                </div>
            </div>
        `;
    }).join('');

    const sumTotal = entries.reduce((acc, [, s]) => acc + s, 0);
    barsContainer.innerHTML = barsHtml + `
        <div class="pt-2 border-t border-slate-700/40 flex items-center justify-between text-xs">
            <span class="text-slate-400 flex items-center gap-1.5">
                <i class="fas fa-check-circle text-emerald-600"></i> Total Evaluation Weight:
            </span>
            <span class="font-mono font-bold text-emerald-600">${sumTotal}%</span>
        </div>
    `;

    // Render Custom 7-Phase Workflow
    const workflowContainer = document.getElementById('sdlc-workflow-list');
    workflowContainer.innerHTML = workflow.map(w => `
        <div class="p-3.5 rounded-xl inner-card text-xs space-y-2 shadow-sm">
            <div class="flex items-center justify-between">
                <span class="font-bold theme-title text-sm">${escapeHTML(w.phase)}</span>
                <span class="text-xs px-2.5 py-0.5 rounded-lg badge-purple">${escapeHTML(w.roles)}</span>
            </div>
            <div class="text-xs leading-relaxed"><strong class="text-slate-400">Activities:</strong> ${w.activities.map(a => escapeHTML(a)).join(', ')}</div>
            <div class="flex items-center justify-between text-xs pt-1.5 text-slate-400 border-t border-slate-700/30">
                <span><i class="fas fa-shield-halved text-blue-600 mr-1"></i> ${escapeHTML(w.security_controls)}</span>
                <span class="text-emerald-600 font-medium"><i class="fas fa-flag-checkered mr-1"></i> Gate: ${escapeHTML(w.validation_gate)}</span>
            </div>
        </div>
    `).join('');
}

function renderRisks(risks) {
    document.getElementById('risk-count').textContent = risks.length;
    const container = document.getElementById('risk-list');
    if (!risks.length) {
        container.innerHTML = `<div class="text-center py-16 text-slate-400 text-sm">No risks recorded.</div>`;
        return;
    }

    container.innerHTML = risks.map(k => `
        <div class="p-4 rounded-2xl inner-card text-xs space-y-2.5 shadow-md">
            <div class="flex items-center justify-between flex-wrap gap-2">
                <div class="flex items-center gap-2">
                    <span class="font-mono font-bold badge-amber px-2.5 py-1 rounded-xl">${escapeHTML(k.id)}</span>
                    <span class="font-semibold theme-title text-sm">${escapeHTML(k.category)}</span>
                </div>
                <div class="flex items-center gap-2 text-xs">
                    <span class="text-slate-400">Likelihood: <strong class="text-slate-300">${escapeHTML(k.likelihood)}</strong></span>
                    <span class="text-slate-400">Impact: <strong class="text-red-600">${escapeHTML(k.impact)}</strong></span>
                    <span class="px-2.5 py-0.5 rounded-lg badge-amber font-bold font-mono">Score: ${k.score}/10</span>
                </div>
            </div>
            <p class="text-sm leading-relaxed theme-title">${escapeHTML(k.description)}</p>
            <div class="p-3 rounded-xl inner-card text-xs text-emerald-600">
                <strong class="text-emerald-600"><i class="fas fa-shield-heart mr-1"></i> Mitigation:</strong> ${escapeHTML(k.mitigation)}
            </div>
        </div>
    `).join('');
}

function renderClarifications(clarifications, conflicts) {
    const container = document.getElementById('quality-findings-container');
    let html = '';

    if (conflicts && conflicts.length > 0) {
        html += `
            <div class="space-y-3">
                <h4 class="text-xs font-bold text-red-600 uppercase tracking-wider flex items-center gap-1.5">
                    <i class="fas fa-triangle-exclamation"></i> Potential Contradictions & Conflicts Detected (${conflicts.length})
                </h4>
        `;
        conflicts.forEach(c => {
            html += `
                <div class="p-4 rounded-2xl inner-card !border-red-600/50 text-xs space-y-2 shadow-md">
                    <div class="font-bold text-red-600 text-sm flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-red-600"></span>
                        ${escapeHTML(c.type || 'Requirement Contradiction')}
                    </div>
                    <p class="theme-title leading-relaxed">${escapeHTML(c.description || c)}</p>
                    ${c.resolution ? `<div class="p-3 rounded-xl inner-card text-xs text-blue-600"><strong class="text-blue-600">Resolution:</strong> ${escapeHTML(c.resolution)}</div>` : ''}
                </div>
            `;
        });
        html += `</div>`;
    }

    if (clarifications && clarifications.length > 0) {
        html += `
            <div class="space-y-3 mt-4">
                <h4 class="text-xs font-bold text-amber-600 uppercase tracking-wider flex items-center gap-1.5">
                    <i class="fas fa-question-circle"></i> Ambiguity Clarification Questions (${clarifications.length})
                </h4>
        `;
        clarifications.forEach(q => {
            const questionText = q.clarification_question || q;
            html += `
                <div class="p-4 rounded-2xl inner-card !border-amber-600/50 text-xs flex items-start justify-between gap-3 shadow-md">
                    <div class="space-y-1.5">
                        <span class="text-xs uppercase font-bold badge-amber px-2.5 py-0.5 rounded-lg inline-block">Subjective Term: ${escapeHTML(q.term || 'ambiguity')}</span>
                        <p class="theme-title text-sm leading-relaxed">${escapeHTML(questionText)}</p>
                    </div>
                    <button onclick="injectClarificationPrompt('${escapeHTML(questionText).replace(/'/g, "\\'")}')" class="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs whitespace-nowrap transition shadow-sm">
                        Answer in Chat
                    </button>
                </div>
            `;
        });
        html += `</div>`;
    }

    if (!html) {
        html = `
            <div class="p-6 rounded-2xl inner-card !border-emerald-600/60 text-center text-xs text-emerald-600 shadow-md">
                <i class="fas fa-circle-check text-3xl mb-2.5 text-emerald-600"></i>
                <p class="font-bold text-sm theme-title">Quality Gate Passed</p>
                <p class="text-slate-400 text-xs mt-1">Zero contradictions or subjective ambiguities detected in current requirement baseline.</p>
            </div>
        `;
    }

    container.innerHTML = html;
}

function injectClarificationPrompt(question) {
    const input = document.getElementById('user-input');
    input.value = `Regarding clarification: "${question}" -> `;
    input.focus();
}

function renderArtifacts(srsPlan) {
    document.getElementById('srs-preview-box').textContent = srsPlan || "No SRS generated yet.";
}

function renderAuditTrail(trail) {
    const container = document.getElementById('audit-trail-timeline');
    if (!trail || !trail.length) {
        container.innerHTML = `<div class="text-center py-10 text-slate-400 text-xs">No audit events recorded yet.</div>`;
        return;
    }

    container.innerHTML = trail.map(ev => `
        <div class="p-3.5 rounded-xl inner-card text-xs flex items-start gap-3 shadow-sm">
            <span class="font-mono text-slate-400 text-xs mt-0.5 whitespace-nowrap inner-card px-2 py-0.5 rounded-lg">${ev.timestamp.split('T')[1]?.split('.')[0] || 'UTC'}</span>
            <div class="flex-1 space-y-1">
                <div class="flex items-center gap-2">
                    <span class="font-bold text-blue-600">${escapeHTML(ev.agent)}</span>
                    <span class="text-slate-400">➔</span>
                    <span class="theme-title font-semibold">${escapeHTML(ev.action)}</span>
                </div>
                <p class="text-slate-400">${escapeHTML(ev.detail)}</p>
            </div>
        </div>
    `).reverse().join('');
}

// ---------------------------
// APPROVALS & EXPORT ACTIONS
// ---------------------------

async function approveSection(section) {
    if (!currentProjectId) {
        alert("Please start a project first.");
        return;
    }
    const comments = prompt(`Enter remarks for approving section '${section}':`, "Approved by human compliance/architect sign-off");
    if (comments === null) return;

    try {
        const resp = await fetch('/session/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: currentProjectId,
                section: section,
                status: 'approved',
                comments: comments || "Approved by stakeholder"
            })
        });
        const res = await resp.json();
        if (resp.ok) {
            if (section === 'requirements') {
                currentRequirements.forEach(r => {
                    r.approval_status = 'approved';
                    r.status = 'approved';
                });
                renderRequirements(currentRequirements);
            }
            alert(`✅ Section '${section}' has been approved and logged into immutable audit trail.`);
            if (res.audit_trail) renderAuditTrail(res.audit_trail);
            else reloadSessionState();
        } else {
            alert(`Approval failed: ${res.detail}`);
        }
    } catch (e) {
        alert("Error connecting to server.");
    }
}

async function approveSingleReq(reqId, status) {
    if (!currentProjectId) {
        const r = currentRequirements.find(item => (item.id || item.req_id) === reqId);
        if (r) {
            r.approval_status = status;
            r.status = status;
            renderRequirements(currentRequirements);
        }
        return;
    }

    try {
        const resp = await fetch('/session/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: currentProjectId,
                section: 'requirements',
                req_id: reqId,
                status: status,
                comments: `Requirement ${reqId} marked as ${status} by stakeholder.`
            })
        });
        const res = await resp.json();
        if (resp.ok) {
            // Update local state
            const r = currentRequirements.find(item => (item.id || item.req_id) === reqId);
            if (r) {
                r.approval_status = status;
                r.status = status;
            }
            renderRequirements(currentRequirements);
            if (res.audit_trail) renderAuditTrail(res.audit_trail);
            else reloadSessionState();
        } else {
            alert(`Failed to update requirement: ${res.detail || 'Error'}`);
        }
    } catch (e) {
        alert("Failed to update requirement approval.");
    }
}

async function removeSingleReq(reqId) {
    if (!confirm(`Are you sure you want to remove requirement ${reqId} from the baseline?`)) {
        return;
    }

    if (!currentProjectId) {
        currentRequirements = currentRequirements.filter(item => (item.id || item.req_id) !== reqId);
        renderRequirements(currentRequirements);
        return;
    }

    try {
        const resp = await fetch('/session/requirement/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: currentProjectId,
                req_id: reqId,
                reason: "Stakeholder removed requirement via HITL dashboard"
            })
        });
        const result = await resp.json();
        if (resp.ok && result.status === 'success') {
            currentRequirements = currentRequirements.filter(item => (item.id || item.req_id) !== reqId);
            renderRequirements(currentRequirements);
            document.getElementById('req-count').textContent = currentRequirements.length;
            if (result.audit_trail) renderAuditTrail(result.audit_trail);
            else reloadSessionState();
        } else {
            alert(`Failed to remove requirement: ${result.detail || 'Error'}`);
        }
    } catch (e) {
        console.error(e);
        alert("Failed to connect to server to remove requirement.");
    }
}

async function approveAllReqs() {
    approveSection('requirements');
}

function openEditModal(reqId) {
    const r = currentRequirements.find(item => (item.id || item.req_id) === reqId);
    if (!r) return;
    editingReqId = reqId;
    document.getElementById('modal-req-id').textContent = reqId;
    document.getElementById('modal-statement').value = r.statement || '';
    document.getElementById('modal-priority').value = r.priority || 'Medium';
    document.getElementById('modal-status').value = r.status || r.approval_status || 'draft';
    document.getElementById('modal-comments').value = '';
    document.getElementById('edit-modal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.add('hidden');
    editingReqId = null;
}

async function saveEditRequirement() {
    if (!currentProjectId || !editingReqId) return;
    const stmt = document.getElementById('modal-statement').value.trim();
    const prio = document.getElementById('modal-priority').value;
    const stat = document.getElementById('modal-status').value;
    const comm = document.getElementById('modal-comments').value.trim();

    try {
        const resp = await fetch('/session/requirement/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: currentProjectId,
                req_id: editingReqId,
                statement: stmt,
                priority: prio,
                status: stat,
                comments: comm
            })
        });
        if (resp.ok) {
            const r = currentRequirements.find(item => (item.id || item.req_id) === editingReqId);
            if (r) {
                r.statement = stmt;
                r.priority = prio;
                r.status = stat;
                r.approval_status = stat;
            }
            closeEditModal();
            renderRequirements(currentRequirements);
            reloadSessionState();
        } else {
            alert("Error updating requirement.");
        }
    } catch (e) {
        alert("Failed to connect to backend.");
    }
}

function exportArtifact(artifactType) {
    if (!currentProjectId) {
        alert("Please generate a project before exporting artifacts.");
        return;
    }
    window.open(`/session/${currentProjectId}/export/${artifactType}`, '_blank');
}

async function reloadSessionState() {
    if (!currentProjectId) return;
    try {
        const resp = await fetch(`/session/${currentProjectId}`);
        const state = await resp.json();
        if (state.audit_trail) renderAuditTrail(state.audit_trail);
    } catch (e) {
        console.error("Failed to refresh state:", e);
    }
}

function resetSession() {
    if (confirm("Reset current project and start a new session?")) {
        currentProjectId = null;
        projectData = null;
        currentRequirements = [];
        document.getElementById('active-project-tag').textContent = "No Active Session";
        document.getElementById('chat-window').innerHTML = '';
        document.getElementById('user-input').value = '';
        document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-slate-500"></span> Idle - Enter project idea to run pipeline';
        renderRequirements([]);
        renderCompliance([]);
        renderRisks([]);
        renderClarifications([], []);
        renderArtifacts('');
        renderAuditTrail([]);
        setAgentsActive(false);
    }
}
