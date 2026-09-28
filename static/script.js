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
        if (icon) icon.className = 'fas fa-moon text-blue-600 text-xs';
        if (text) text.textContent = 'Dark';
    } else {
        document.body.classList.remove('light-theme');
        document.documentElement.classList.remove('light-theme');
        if (icon) icon.className = 'fas fa-sun text-amber-400 text-xs';
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
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-inherit">$1</strong>');
    // Replace *italic* with <em>italic</em>
    safe = safe.replace(/\*(.*?)\*/g, '<em class="text-slate-400">$1</em>');
    // Replace `code` with styled <code>
    safe = safe.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded badge-blue font-mono text-[11px]">$1</code>');
    // Bullet points • or - at line start
    safe = safe.replace(/^[•\-] (.*)$/gm, '<div class="flex items-start gap-2 my-1"><span class="text-blue-400 font-bold">•</span><span>$1</span></div>');
    // Numbered items: 1.
    safe = safe.replace(/^(\d+)\.\s+(.*)$/gm, '<div class="flex items-start gap-2 my-1"><span class="text-blue-400 font-mono font-semibold">$1.</span><span>$2</span></div>');
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
                el.className = "p-2 rounded-lg agent-node active-agent font-medium text-xs transition-all";
            }, index * 40);
        } else {
            el.className = "p-2 rounded-lg agent-node text-xs font-normal transition-all";
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
    appendChatMessage('assistant', '<div class="flex items-center gap-2 text-slate-400 text-xs font-mono"><i class="fas fa-circle-notch fa-spin text-blue-400"></i> Orchestrating 13 specialist agents...</div>', loadingId);

    setAgentsActive(true);
    document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-blue-400 pulse-badge"></span> Multi-Agent Pipeline Executing...';

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
            const statusCode = response.status;
            let errMsg = escapeHTML(result.detail || 'Request failed');
            if (statusCode === 429) {
                errMsg = `⏳ <strong>Gemini API Rate Limit Reached.</strong><br>` +
                    `The free-tier API allows ~15 requests/minute. Please wait <strong>30–60 seconds</strong> and try again.<br>` +
                    `<span class="text-slate-400 text-xs">Tip: The compliance RAG and validation agents always work regardless of quota.</span>`;
                document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> Rate limited – please wait';
            } else if (statusCode === 503) {
                errMsg = `🔄 <strong>Gemini AI is temporarily overloaded.</strong><br>Please retry in a few seconds.`;
                document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> AI service busy – retrying';
            } else {
                document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Error encountered';
            }
            appendChatMessage('assistant', `<div class="space-y-1">${errMsg}</div>`);
            return;
        }

        document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> System Ready &bull; Pipeline Validated';

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
                    <div class="mt-3 p-3.5 rounded-lg inner-card space-y-2.5 border-blue-500/30">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-1.5 text-blue-400 font-semibold text-xs uppercase tracking-wider">
                                <i class="fas fa-clipboard-question"></i>
                                <span>Adaptive Clarification (${escapeHTML(role)})</span>
                            </div>
                            <span class="text-[10px] font-mono px-2 py-0.5 rounded badge-blue">Input Requested</span>
                        </div>
                        <p class="text-xs text-slate-400 leading-normal">
                            The Clarification &amp; Interaction agents identified ambiguity bounds. Clarify the following items:
                        </p>
                        <div class="space-y-2">
                            ${questions.slice(0, 3).map((q, idx) => `
                                <div class="p-2.5 rounded bg-[var(--card-inner)] border border-[var(--card-border-subtle)] text-xs">
                                    <div class="font-mono text-blue-400 mb-1 text-[11px] font-semibold flex items-center gap-1.5">
                                        <i class="fas fa-circle-question text-xs"></i>
                                        <span>Item ${idx + 1}:</span>
                                    </div>
                                    <div class="leading-relaxed theme-title">${escapeHTML(q)}</div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="pt-2 border-t border-[var(--card-border)]">
                            <div class="text-[11px] text-slate-400 mb-1.5 flex items-center gap-1">
                                <i class="fas fa-lightbulb text-amber-400 text-xs"></i>
                                <span>Quick Answer Templates:</span>
                            </div>
                            <div class="flex flex-wrap gap-1.5">
                                <button type="button" onclick="fillChatInput('Peak throughput is 5,000 TPS with p99 latency < 150ms. Step-up MFA threshold is $10,000. Core banking connects via IBM MQ using ISO 20022 PACS.008.')" class="preset-chip text-[11px] px-2.5 py-1 rounded transition text-left">
                                    ⚡ <strong>Payment SLAs:</strong> 5,000 TPS, &lt;150ms, $10k MFA
                                </button>
                                <button type="button" onclick="fillChatInput('Statutory retention is 7 years immutable audit trail. Mandatory four-eyes dual authorization for transfers exceeding $50,000.')" class="preset-chip text-[11px] px-2.5 py-1 rounded transition text-left">
                                    🛡️ <strong>Compliance:</strong> 7-yr retention, $50k dual auth
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }

            appendChatMessage('assistant', `
                <div class="space-y-2.5">
                    <div class="p-2.5 rounded-lg badge-green text-xs font-medium flex items-center gap-2">
                        <i class="fas fa-check-circle text-emerald-400"></i>
                        <span><strong>Baseline Synthesized:</strong> Extracted <strong>${currentRequirements.length}</strong> requirements, mapped <strong>${data.compliance_mappings.length}</strong> regulatory citations, recommended <strong>${data.sdlc_info.recommended_model}</strong>.</span>
                    </div>
                    <p class="text-xs leading-relaxed theme-title">
                        Structured across financial domain (<strong>${escapeHTML(domain)}</strong>). Review requirements ledger in the right panel and answer clarification items below:
                    </p>
                    ${questionsHtml}
                </div>
            `);
        } else if (result.response) {
            appendChatMessage('assistant', `<div class="text-xs leading-relaxed theme-title">${formatMarkdown(result.response)}</div>`);
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
        document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Connection error';
        appendChatMessage('assistant', `❌ Connection failure: Could not reach the FinReq backend.`);
    }
}

function appendChatMessage(role, htmlContent, id = null) {
    const chatWindow = document.getElementById('chat-window');
    const wrapper = document.createElement('div');
    wrapper.className = `flex items-start gap-2.5 ${role === 'user' ? 'justify-end' : 'justify-start'}`;
    if (id) wrapper.id = id;

    if (role === 'user') {
        wrapper.innerHTML = `
            <div class="inner-card p-3 max-w-lg text-xs leading-relaxed border-blue-500/20 bg-blue-950/20 text-slate-200">
                ${escapeHTML(htmlContent)}
            </div>
            <div class="w-7 h-7 rounded-md bg-blue-600/30 border border-blue-500/30 flex-shrink-0 flex items-center justify-center text-blue-300 font-mono text-[11px] font-bold">
                U
            </div>
        `;
    } else {
        wrapper.innerHTML = `
            <div class="w-7 h-7 rounded-md bg-slate-800 border border-slate-700 flex-shrink-0 flex items-center justify-center text-slate-300 font-mono text-[11px] font-bold">
                FR
            </div>
            <div class="inner-card p-3 max-w-xl text-xs leading-relaxed space-y-2">
                ${htmlContent}
            </div>
        `;
    }

    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const countEl = document.getElementById('chat-count');
    if (countEl) countEl.textContent = chatWindow.children.length;
}

// ---------------------------
// TAB RENDERING FUNCTIONS
// ---------------------------

function renderRequirements(reqs) {
    document.getElementById('req-count').textContent = reqs.length;
    const container = document.getElementById('requirements-list');
    if (!reqs.length) {
        container.innerHTML = `<div class="text-center py-12 text-slate-400 text-xs font-medium">No requirements available in baseline.</div>`;
        return;
    }

    container.innerHTML = reqs.map((r, idx) => {
        const id = r.id || r.req_id || `REQ-${idx + 1}`;
        const isApproved = r.approval_status === 'approved' || r.status === 'approved';
        const isHighPrio = (r.priority || '').toLowerCase() === 'high';
        const prioBadge = isHighPrio
            ? '<span class="text-[10px] font-mono px-2 py-0.5 rounded badge-red font-semibold">High Priority</span>'
            : '<span class="text-[10px] font-mono px-2 py-0.5 rounded badge-amber font-semibold">Medium Priority</span>';

        const statusBadge = isApproved
            ? '<span class="text-[10px] font-mono px-2 py-0.5 rounded badge-green font-semibold flex items-center gap-1"><i class="fas fa-check"></i> Approved</span>'
            : '<span class="text-[10px] font-mono px-2 py-0.5 rounded badge-blue font-medium">Pending Review</span>';

        return `
            <div class="p-3.5 rounded-lg inner-card ${isApproved ? '!border-emerald-500/40' : ''} space-y-2.5 transition">
                <div class="flex items-center justify-between flex-wrap gap-2">
                    <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">${escapeHTML(id)}</span>
                        <span class="text-[10px] font-mono px-2 py-0.5 rounded badge-blue">${escapeHTML(r.category || 'Functional')}</span>
                        ${prioBadge}
                        ${statusBadge}
                        <span class="text-[11px] text-slate-400">Risk: <strong class="${(r.risk || r.risk_level) === 'High' ? 'text-red-400' : 'text-amber-400'} font-medium">${escapeHTML(r.risk || r.risk_level || 'Medium')}</strong></span>
                    </div>

                    <!-- Action Buttons -->
                    <div class="flex items-center gap-1.5">
                        ${isApproved ? `
                            <button onclick="approveSingleReq('${id}', 'draft')" class="text-xs px-2.5 py-1 rounded bg-emerald-700/30 border border-emerald-500/40 text-emerald-300 font-medium transition flex items-center gap-1 hover:bg-emerald-700/50" title="Click to undo approval">
                                <i class="fas fa-check-double text-[11px]"></i> Approved
                            </button>
                        ` : `
                            <button onclick="approveSingleReq('${id}', 'approved')" class="btn-approve text-xs px-2.5 py-1 rounded font-medium transition flex items-center gap-1" title="Approve requirement">
                                <i class="fas fa-check text-[11px]"></i> Approve
                            </button>
                        `}
                        <button onclick="removeSingleReq('${id}')" class="btn-remove text-xs px-2.5 py-1 rounded font-medium transition flex items-center gap-1" title="Remove requirement">
                            <i class="fas fa-trash text-[11px]"></i>
                        </button>
                        <button onclick="openEditModal('${id}')" class="btn-secondary text-xs px-2 py-1 rounded transition" title="Modify requirement">
                            <i class="fas fa-pen text-[11px]"></i>
                        </button>
                    </div>
                </div>

                <p class="text-xs text-slate-200 leading-relaxed font-normal">${escapeHTML(r.statement)}</p>

                ${r.acceptance_criteria ? `
                    <div class="p-2.5 rounded bg-[var(--card-inner)] border border-[var(--card-border-subtle)] text-[11px] text-slate-300">
                        <span class="text-blue-400 font-semibold font-mono text-[10px] uppercase tracking-wider block mb-0.5">Acceptance Criteria:</span>
                        <span class="leading-relaxed">${escapeHTML(Array.isArray(r.acceptance_criteria) ? r.acceptance_criteria.join(' ') : r.acceptance_criteria)}</span>
                    </div>
                ` : ''}

                ${(r.compliance_mapping || r.regulations) && (r.compliance_mapping?.length || r.regulations?.length) ? `
                    <div class="flex items-center gap-1 text-[11px] text-slate-400 flex-wrap pt-0.5">
                        <span class="text-[10px] font-mono text-slate-400 uppercase">Citations:</span>
                        ${(r.compliance_mapping || r.regulations).map(reg => `
                            <span class="font-mono text-[10px] px-1.5 py-0.2 rounded badge-blue">${escapeHTML(reg)}</span>
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
        container.innerHTML = `<div class="text-center py-16 text-slate-400 text-xs">No compliance mappings available.</div>`;
        return;
    }

    container.innerHTML = mappings.map(c => `
        <div class="p-3.5 rounded-lg inner-card space-y-2">
            <div class="flex items-center justify-between flex-wrap gap-2">
                <div class="flex items-center gap-1.5">
                    <span class="text-[10px] font-mono font-bold badge-blue px-2 py-0.5 rounded">${escapeHTML(c.req_id)}</span>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded badge-red font-semibold">${escapeHTML(c.citation)}</span>
                    <span class="text-[11px] text-slate-400 font-mono">${escapeHTML(c.source_doc)}:${c.line_number}</span>
                </div>
                <div class="flex items-center gap-1.5">
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded badge-green font-medium">Coverage: ${escapeHTML(c.coverage)}</span>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded badge-blue font-medium">${Math.round(c.confidence * 100)}% Confidence</span>
                </div>
            </div>
            <p class="text-xs text-slate-300 italic p-2.5 rounded bg-[var(--card-inner)] border border-[var(--card-border-subtle)] leading-relaxed font-mono">
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
        const barColor = isTop ? 'bg-emerald-500' : 'bg-slate-600';
        return `
            <div>
                <div class="flex justify-between items-center mb-1 text-xs">
                    <span class="${isTop ? 'text-emerald-400 font-semibold' : 'text-slate-400'}">${escapeHTML(model)} ${isTop ? '★' : ''}</span>
                    <span class="font-mono ${isTop ? 'text-emerald-400 font-semibold' : 'text-slate-400'}">${score}%</span>
                </div>
                <div class="w-full h-1.5 rounded-full bg-[var(--card-inner)] border border-[var(--card-border-subtle)] overflow-hidden">
                    <div class="h-full rounded-full ${barColor} transition-all duration-500" style="width: ${Math.max(score, 4)}%"></div>
                </div>
            </div>
        `;
    }).join('');

    const sumTotal = entries.reduce((acc, [, s]) => acc + s, 0);
    barsContainer.innerHTML = barsHtml + `
        <div class="pt-2 border-t border-[var(--card-border)] flex items-center justify-between text-xs">
            <span class="text-slate-400 flex items-center gap-1">
                <i class="fas fa-check-circle text-emerald-400 text-xs"></i> Total Weight:
            </span>
            <span class="font-mono font-semibold text-emerald-400">${sumTotal}%</span>
        </div>
    `;

    // Render Custom 7-Phase Workflow
    const workflowContainer = document.getElementById('sdlc-workflow-list');
    workflowContainer.innerHTML = workflow.map(w => `
        <div class="p-3 rounded-lg inner-card text-xs space-y-1.5">
            <div class="flex items-center justify-between">
                <span class="font-bold theme-title text-xs">${escapeHTML(w.phase)}</span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded badge-purple">${escapeHTML(w.roles)}</span>
            </div>
            <div class="text-xs text-slate-300 leading-relaxed"><strong class="text-slate-400 font-normal">Activities:</strong> ${w.activities.map(a => escapeHTML(a)).join(', ')}</div>
            <div class="flex items-center justify-between text-[11px] pt-1 text-slate-400 border-t border-[var(--card-border-subtle)]">
                <span><i class="fas fa-shield-halved text-blue-400 mr-1"></i> ${escapeHTML(w.security_controls)}</span>
                <span class="text-emerald-400 font-medium"><i class="fas fa-flag-checkered mr-1"></i> Gate: ${escapeHTML(w.validation_gate)}</span>
            </div>
        </div>
    `).join('');
}

function renderRisks(risks) {
    document.getElementById('risk-count').textContent = risks.length;
    const container = document.getElementById('risk-list');
    if (!risks.length) {
        container.innerHTML = `<div class="text-center py-16 text-slate-400 text-xs">No risks recorded.</div>`;
        return;
    }

    container.innerHTML = risks.map(k => `
        <div class="p-3.5 rounded-lg inner-card text-xs space-y-2">
            <div class="flex items-center justify-between flex-wrap gap-2">
                <div class="flex items-center gap-1.5">
                    <span class="font-mono font-bold badge-amber px-2 py-0.5 rounded text-[10px]">${escapeHTML(k.id)}</span>
                    <span class="font-semibold theme-title text-xs">${escapeHTML(k.category)}</span>
                </div>
                <div class="flex items-center gap-2 text-[11px]">
                    <span class="text-slate-400">Likelihood: <strong class="text-slate-300">${escapeHTML(k.likelihood)}</strong></span>
                    <span class="text-slate-400">Impact: <strong class="text-red-400">${escapeHTML(k.impact)}</strong></span>
                    <span class="px-2 py-0.5 rounded badge-amber font-semibold font-mono text-[10px]">Score: ${k.score}/10</span>
                </div>
            </div>
            <p class="text-xs leading-relaxed text-slate-200">${escapeHTML(k.description)}</p>
            <div class="p-2.5 rounded bg-[var(--card-inner)] border border-[var(--card-border-subtle)] text-[11px] text-emerald-400">
                <strong class="font-semibold text-emerald-400"><i class="fas fa-shield-heart mr-1"></i> Mitigation:</strong> ${escapeHTML(k.mitigation)}
            </div>
        </div>
    `).join('');
}

function renderClarifications(clarifications, conflicts) {
    const container = document.getElementById('quality-findings-container');
    let html = '';

    if (conflicts && conflicts.length > 0) {
        html += `
            <div class="space-y-2.5">
                <h4 class="text-[11px] font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                    <i class="fas fa-triangle-exclamation"></i> Contradictions &amp; Conflicts Detected (${conflicts.length})
                </h4>
        `;
        conflicts.forEach(c => {
            html += `
                <div class="p-3.5 rounded-lg inner-card !border-rose-500/40 text-xs space-y-1.5">
                    <div class="font-bold text-rose-400 text-xs flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                        ${escapeHTML(c.type || 'Requirement Contradiction')}
                    </div>
                    <p class="text-xs text-slate-200 leading-relaxed">${escapeHTML(c.description || c)}</p>
                    ${c.resolution ? `<div class="p-2.5 rounded bg-[var(--card-inner)] border border-[var(--card-border-subtle)] text-[11px] text-blue-400"><strong class="font-semibold text-blue-400">Resolution:</strong> ${escapeHTML(c.resolution)}</div>` : ''}
                </div>
            `;
        });
        html += `</div>`;
    }

    if (clarifications && clarifications.length > 0) {
        html += `
            <div class="space-y-2.5 mt-3">
                <h4 class="text-[11px] font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                    <i class="fas fa-circle-question"></i> Ambiguity Clarification Questions (${clarifications.length})
                </h4>
        `;
        clarifications.forEach(q => {
            const questionText = q.clarification_question || q;
            html += `
                <div class="p-3.5 rounded-lg inner-card !border-amber-500/40 text-xs flex items-start justify-between gap-3">
                    <div class="space-y-1">
                        <span class="text-[10px] font-mono uppercase font-bold badge-amber px-2 py-0.5 rounded inline-block">Subjective Term: ${escapeHTML(q.term || 'ambiguity')}</span>
                        <p class="text-xs text-slate-200 leading-relaxed">${escapeHTML(questionText)}</p>
                    </div>
                    <button onclick="injectClarificationPrompt('${escapeHTML(questionText).replace(/'/g, "\\'")}')" class="px-2.5 py-1 rounded bg-amber-500/20 border border-amber-500/40 hover:bg-amber-500/30 text-amber-300 font-medium text-xs whitespace-nowrap transition">
                        Answer
                    </button>
                </div>
            `;
        });
        html += `</div>`;
    }

    if (!html) {
        html = `
            <div class="p-6 rounded-lg inner-card !border-emerald-500/40 text-center text-xs text-emerald-400">
                <i class="fas fa-circle-check text-2xl mb-2 text-emerald-400 block"></i>
                <p class="font-bold text-xs theme-title">Quality Gate Passed</p>
                <p class="text-slate-400 text-[11px] mt-0.5">Zero contradictions or subjective ambiguities detected in current baseline.</p>
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
        <div class="p-2.5 rounded-lg inner-card text-xs flex items-start gap-2.5">
            <span class="font-mono text-slate-400 text-[10px] mt-0.5 whitespace-nowrap px-1.5 py-0.5 rounded bg-[var(--card-inner)] border border-[var(--card-border-subtle)]">${ev.timestamp.split('T')[1]?.split('.')[0] || 'UTC'}</span>
            <div class="flex-1 space-y-0.5">
                <div class="flex items-center gap-1.5">
                    <span class="font-mono font-semibold text-blue-400 text-[11px]">${escapeHTML(ev.agent)}</span>
                    <span class="text-slate-500 text-[10px]">➔</span>
                    <span class="theme-title font-medium text-xs">${escapeHTML(ev.action)}</span>
                </div>
                <p class="text-[11px] text-slate-400">${escapeHTML(ev.detail)}</p>
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
        document.getElementById('pipeline-status').innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-slate-500"></span> System Idle &bull; Ready for Input';
        renderRequirements([]);
        renderCompliance([]);
        renderRisks([]);
        renderClarifications([], []);
        renderArtifacts('');
        renderAuditTrail([]);
        setAgentsActive(false);
    }
}
