/* ════════════════════════════════════════════
   FinReq — Main Script (ArtSox Theme Edition)
   ════════════════════════════════════════════ */

let currentProjectId = null;
let projectData = null;
let currentRequirements = [];
let editingReqId = null;
let currentSessionTitle = null;

// ─── PRESETS ───────────────────────────────────
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

// ─── HELPERS ───────────────────────────────────
function escapeHTML(str) {
    return String(str ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function formatMarkdown(text) {
    if (!text) return '';
    let s = escapeHTML(text);
    s = s.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#fff;font-weight:800;">$1</strong>');
    s = s.replace(/\*(.*?)\*/g, '<em style="color:#a3a3a3;">$1</em>');
    s = s.replace(/`([^`]+)`/g, '<code style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.25);color:#fbbf24;padding:2px 6px;border-radius:4px;font-family:\'JetBrains Mono\',monospace;font-size:14px;">$1</code>');
    s = s.replace(/^[•\-] (.*)$/gm, '<div style="display:flex;align-items:flex-start;gap:8px;margin:4px 0;"><span style="color:#f59e0b;font-weight:900;flex-shrink:0;">•</span><span>$1</span></div>');
    s = s.replace(/^(\d+)\.\s+(.*)$/gm, '<div style="display:flex;align-items:flex-start;gap:8px;margin:4px 0;"><span style="color:#f59e0b;font-family:\'JetBrains Mono\',monospace;font-weight:700;flex-shrink:0;">$1.</span><span>$2</span></div>');
    s = s.replace(/\n/g, '<br>');
    return s;
}

window.fillChatInput = function (text) {
    const inp = document.getElementById('user-input');
    if (inp) { inp.value = text; inp.focus(); }
};

// ─── PII MASKING HIGHLIGHT & VISUALIZATION ─────
function highlightMaskedTokens(text) {
    if (!text) return '';
    let safe = escapeHTML(text);
    const tokens = [
        '[CARD_NUMBER_MASKED]',
        '[SSN_MASKED]',
        '[EMAIL_MASKED]',
        '[ACCOUNT_MASKED]',
        '[PHONE_MASKED]'
    ];
    tokens.forEach(tok => {
        const escaped = escapeHTML(tok);
        const badge = `<span style="background:rgba(239,68,68,0.2);border:1px solid rgba(239,68,68,0.45);color:#fca5a5;padding:2px 7px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:800;display:inline-flex;align-items:center;gap:4px;white-space:nowrap !important;vertical-align:baseline;"><i class="fas fa-shield-halved" style="font-size:11px;color:#ef4444;"></i>${escaped}</span>`;
        safe = safe.split(escaped).join(badge);
    });
    return safe;
}

function updateBubbleWithMaskedPII(bubbleWrapId, safeText, originalText, maskedItems) {
    const wrap = document.getElementById(bubbleWrapId);
    if (!wrap) return;
    const bubble = wrap.querySelector('.chat-bubble-user');
    if (!bubble) return;

    const safeHtml = highlightMaskedTokens(safeText);
    const origHtml = escapeHTML(originalText);
    const uniqueId = 'toggle-' + Math.random().toString(36).substring(2, 8);

    bubble.innerHTML = `
        <div style="font-size:12px;font-family:'JetBrains Mono',monospace;color:#f59e0b;display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid rgba(245,158,11,0.25);">
            <span style="display:flex;align-items:center;gap:6px;">
                <i class="fas fa-shield-halved" style="color:#ef4444;"></i>
                <strong>PII REDACTED BY GUARD</strong>
            </span>
            <button type="button" onclick="const s=document.getElementById('${uniqueId}-safe'), o=document.getElementById('${uniqueId}-orig'); if(s.style.display==='none'){s.style.display='block';o.style.display='none';this.textContent='Show Original';}else{s.style.display='none';o.style.display='block';this.textContent='Show Sanitized';}"
                style="background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.3);color:#fbbf24;padding:2px 8px;border-radius:4px;font-size:11px;cursor:pointer;font-family:'JetBrains Mono',monospace;">
                Show Original
            </button>
        </div>
        <div id="${uniqueId}-safe" style="line-height:1.65;font-size:17.5px;color:#f3f4f6;">
            ${safeHtml}
        </div>
        <div id="${uniqueId}-orig" style="display:none;line-height:1.65;font-size:17.5px;color:#a3a3a3;text-decoration:line-through;">
            ${origHtml}
        </div>
        <div style="margin-top:8px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.06);font-size:12px;color:#737373;font-family:'JetBrains Mono',monospace;">
            <i class="fas fa-lock" style="margin-right:4px;color:#f59e0b;"></i> Masked: <strong style="color:#fca5a5;">${escapeHTML(maskedItems.join(', '))}</strong> (Raw values isolated from AI)
        </div>
    `;
}

// ─── TAB SWITCHING ─────────────────────────────
function switchTab(tabId) {
    ['requirements', 'compliance', 'sdlc', 'risks', 'clarifications', 'traceability', 'admin', 'artifacts', 'audit'].forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const con = document.getElementById(`tab-content-${t}`);
        if (btn) btn.classList.toggle('active', t === tabId);
        if (con) con.classList.toggle('hidden', t !== tabId);
    });
    if (tabId === 'traceability') {
        fetchTraceabilityMatrix();
    } else if (tabId === 'admin') {
        fetchAdminMetrics();
    }
}

// ─── AGENT ANIMATION ───────────────────────────
function setAgentsActive(active) {
    const ids = ['coordinator', 'interaction', 'extraction', 'clarification',
        'classification', 'conflict', 'compliance', 'security',
        'risk', 'sdlc', 'doc', 'validator', 'approval'];
    ids.forEach((id, i) => {
        const el = document.getElementById(`agent-${id}`);
        if (!el) return;
        if (active) {
            setTimeout(() => el.classList.add('active-agent'), i * 40);
        } else {
            el.classList.remove('active-agent');
        }
    });
}

// ─── SEND MESSAGE ──────────────────────────────
async function handleSend(e) {
    if (e) e.preventDefault();
    if (!currentAuthUser?.token) {
        openAuthModal();
        showToast('Please sign in before starting an analysis', 'err');
        return;
    }
    const input = document.getElementById('user-input');
    const prompt = input.value.trim();
    if (!prompt) return;

    input.value = '';
    const userMsgId = 'user-msg-' + Date.now();
    appendChatMessage('user', escapeHTML(prompt), userMsgId);

    const loadingId = 'loading-' + Date.now();
    appendChatMessage('assistant',
        '<div style="display:flex;align-items:center;gap:12px;color:#a3a3a3;font-family:\'JetBrains Mono\',monospace;font-size:18px;">' +
        '<i class="fas fa-circle-notch fa-spin" style="color:#f59e0b;"></i> ORCHESTRATING_13_AGENTS...</div>',
        loadingId
    );

    setAgentsActive(true);
    setPipelineStatus('running', 'PIPELINE_EXECUTING...');

    const domain = document.getElementById('domain-select').value;
    const role = document.getElementById('role-select').value;

    try {
        let endpoint = '/session/chat';
        let body = { project_id: currentProjectId, message: prompt, stakeholder_role: role };

        if (!currentProjectId) {
            endpoint = '/session/start';
            body = { prompt, domain, stakeholder_role: role };
        }

        const response = await authorizedFetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const result = await response.json();
        document.getElementById(loadingId)?.remove();
        setAgentsActive(false);

        if (!response.ok || result.status !== 'success') {
            const code = response.status;
            let errMsg = escapeHTML(result.detail || 'Request failed');
            if (code === 429) {
                errMsg = '⏳ <strong style="color:#fff;">Rate Limit Reached.</strong> Wait 30–60s and retry.';
                setPipelineStatus('warn', 'RATE_LIMITED — WAIT_30S');
            } else if (code === 503) {
                errMsg = '🔄 <strong style="color:#fff;">AI service overloaded.</strong> Retry in a few seconds.';
                setPipelineStatus('warn', 'SERVICE_BUSY');
            } else {
                setPipelineStatus('err', 'ERROR_ENCOUNTERED');
            }
            appendChatMessage('assistant', `<div style="font-size:19px;line-height:1.6;">${errMsg}</div>`);
            return;
        }

        setPipelineStatus('ok', 'PIPELINE_VALIDATED :: READY');

        if (result.project_id && !currentProjectId) {
            currentProjectId = result.project_id;
            currentSessionTitle = `${domain} — ${new Date().toLocaleDateString()}`;
            const tag = document.getElementById('active-project-tag');
            if (tag) {
                tag.innerHTML = `<span style="color:#a78bfa;font-weight:700;"><i class="fas fa-folder-open mr-1"></i>${escapeHTML(currentSessionTitle)}</span>`;
                tag.title = `Project ID: ${currentProjectId}`;
            }
            document.getElementById('session-action-btns').style.display = 'flex';
        }

        // ── Initial Analysis ──
        if (result.initial_analysis) {
            const data = result.initial_analysis;
            projectData = data;
            currentRequirements = data.structured_requirements || [];

            if (data.pii_masked_items?.length) {
                const safePrompt = data.safe_prompt || prompt;
                updateBubbleWithMaskedPII(userMsgId, safePrompt, prompt, data.pii_masked_items);
            }

            renderRequirements(currentRequirements);
            renderCompliance(data.compliance_mappings || []);
            renderSDLC(data.sdlc_info, data.sdlc_workflow || []);
            renderRisks(data.risk_register || []);
            renderClarifications(data.clarifications || [], data.conflicts || []);
            renderArtifacts(data.srs_plan);
            renderAuditTrail(result.audit_trail || []);

            let questions = data.interview_questions || [];
            if (!questions.length && data.clarifications?.length) {
                questions = data.clarifications.map(c => c.clarification_question || c);
            }
            if (!questions.length) {
                const roleQ = {
                    "Business Analyst": [
                        "What are the target peak TPS and p99 latency SLA targets?",
                        "What amount threshold triggers step-up MFA or dual four-eyes approval?",
                        "Which protocols connect to legacy core banking (e.g. ISO 20022, IBM MQ)?"
                    ],
                    "Compliance Officer": [
                        "Which regulatory jurisdictions apply (EU GDPR, US BSA/AML, Basel III/IV)?",
                        "What specific CDD and SAR triggers are required?",
                        "What are the statutory retention periods and audit logging mandates?"
                    ],
                    "Information-Security Team": [
                        "What encryption standards are required (AES-256 at rest, TLS 1.3 in transit)?",
                        "What step-up authentication or HSM controls must be in place?",
                        "What are the disaster recovery RTO and RPO SLA requirements?"
                    ],
                    "Risk-Management Team": [
                        "What risk threshold triggers mandatory four-eyes dual authorization?",
                        "What are the operational risk limits and fraud scoring tolerance levels?",
                        "How should systemic liquidity and counterparty risk be monitored?"
                    ]
                };
                questions = roleQ[role] || roleQ["Business Analyst"];
            }

            let qHtml = '';
            if (questions.length) {
                qHtml = `
                <div style="margin-top:18px;padding:18px;border-radius:8px;background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.25);">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                        <span style="font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:800;letter-spacing:0.06em;color:#f59e0b;">
                            <i class="fas fa-clipboard-question" style="margin-right:8px;"></i>CLARIFICATION_REQUIRED
                        </span>
                        <span style="font-family:'JetBrains Mono',monospace;font-size:13px;background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.3);color:#fbbf24;padding:4px 10px;border-radius:4px;">INPUT_NEEDED</span>
                    </div>
                    <div style="display:flex;flex-direction:column;gap:10px;">
                        ${questions.slice(0, 3).map((q, i) => `
                            <div style="padding:14px 16px;border-radius:6px;background:rgba(0,0,0,0.4);border:1px solid #333;font-size:18px;">
                                <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:#f59e0b;font-weight:800;margin-bottom:6px;">
                                    <i class="fas fa-circle-question" style="margin-right:6px;"></i>ITEM_${i + 1}:
                                </div>
                                <div style="color:#f3f4f6;line-height:1.65;">${escapeHTML(q)}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="margin-top:14px;padding-top:12px;border-top:1px solid #2a2a2a;">
                        <div style="font-size:14px;color:#737373;margin-bottom:8px;font-family:'JetBrains Mono',monospace;font-weight:700;">QUICK_TEMPLATES:</div>
                        <div style="display:flex;flex-wrap:wrap;gap:8px;">
                            <button type="button" onclick="fillChatInput('Peak throughput is 5,000 TPS with p99 latency < 150ms. Step-up MFA threshold is $10,000. Core banking connects via IBM MQ using ISO 20022 PACS.008.')" class="preset-chip" style="padding:10px 14px;font-size:16px;">
                                ⚡ Payment SLAs: 5k TPS, &lt;150ms, $10k MFA
                            </button>
                            <button type="button" onclick="fillChatInput('Statutory retention is 7 years immutable audit trail. Mandatory four-eyes dual authorization for transfers exceeding $50,000.')" class="preset-chip" style="padding:10px 14px;font-size:16px;">
                                🛡️ Compliance: 7yr retention, $50k dual-auth
                            </button>
                        </div>
                    </div>
                </div>`;
            }

            appendChatMessage('assistant', `
                <div style="display:flex;flex-direction:column;gap:14px;">
                    <div style="display:flex;align-items:center;gap:12px;padding:14px 16px;border-radius:6px;background:rgba(22,163,74,0.1);border:1px solid rgba(22,163,74,0.25);">
                        <i class="fas fa-check-circle" style="color:#16a34a;font-size:22px;"></i>
                        <span style="font-size:19px;color:#e5e5e5;line-height:1.6;">
                            <strong style="color:#fff;">Baseline Synthesized:</strong>
                            Extracted <strong style="color:#fbbf24;">${currentRequirements.length}</strong> requirements,
                            mapped <strong style="color:#fbbf24;">${data.compliance_mappings.length}</strong> regulatory citations,
                            recommended <strong style="color:#fbbf24;">${data.sdlc_info.recommended_model}</strong>.
                        </span>
                    </div>
                    <p style="font-size:18px;color:#d1d5db;line-height:1.65;">
                        Structured for domain: <strong style="color:#fff;">${escapeHTML(domain)}</strong>. 
                        Review the Requirements tab and answer clarifications below:
                    </p>
                    ${qHtml}
                </div>
            `);

        } else if (result.response) {
            appendChatMessage('assistant', `<div style="font-size:20px;line-height:1.7;">${formatMarkdown(result.response)}</div>`);
            if (result.audit_trail) renderAuditTrail(result.audit_trail);
            if (result.requirements) {
                currentRequirements = Object.values(result.requirements);
                renderRequirements(currentRequirements);
            }
            if (result.clarifications !== undefined || result.conflicts !== undefined) {
                renderClarifications(result.clarifications || [], result.conflicts || []);
            }
            if (result.pii_masked_items?.length) {
                const safeMsg = result.safe_message || prompt;
                updateBubbleWithMaskedPII(userMsgId, safeMsg, prompt, result.pii_masked_items);
            }
        }

    } catch (err) {
        document.getElementById(loadingId)?.remove();
        setAgentsActive(false);
        setPipelineStatus('err', 'CONNECTION_ERROR');
        appendChatMessage('assistant', `<div style="font-size:19px;color:#f87171;">❌ Connection failure — backend unreachable.</div>`);
    }
}

// ─── CHAT MESSAGE APPEND ───────────────────────
function appendChatMessage(role, htmlContent, id = null) {
    const win = document.getElementById('chat-window');
    const wrap = document.createElement('div');
    wrap.style.cssText = `display:flex;align-items:flex-start;gap:14px;${role === 'user' ? 'justify-content:flex-end;' : ''}`;
    if (id) wrap.id = id;

    if (role === 'user') {
        wrap.innerHTML = `
            <div class="chat-bubble-user" style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);border-radius:8px;padding:16px 20px;max-width:580px;font-size:20px;line-height:1.7;color:#f3f4f6;">${htmlContent}</div>
            <div style="width:44px;height:44px;border-radius:6px;background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.3);flex-shrink:0;display:flex;align-items:center;justify-content:center;color:#fbbf24;font-family:'JetBrains Mono',monospace;font-weight:900;font-size:14px;">U</div>
        `;
    } else {
        wrap.innerHTML = `
            <div style="width:44px;height:44px;border-radius:6px;background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.3);flex-shrink:0;display:flex;align-items:center;justify-content:center;color:#fbbf24;font-family:'JetBrains Mono',monospace;font-weight:900;font-size:14px;">FR</div>
            <div class="chat-bubble-assistant" style="background:#181818;border:1px solid #2a2a2a;border-radius:8px;padding:16px 20px;max-width:650px;font-size:20px;line-height:1.7;color:#f3f4f6;">${htmlContent}</div>
        `;
    }

    win.appendChild(wrap);
    win.scrollTop = win.scrollHeight;
    const c = document.getElementById('chat-count');
    if (c) c.textContent = win.children.length;
}

// ─── PIPELINE STATUS ───────────────────────────
function setPipelineStatus(state, text) {
    const el = document.getElementById('pipeline-status');
    if (!el) return;
    const colors = { ok: '#16a34a', warn: '#f59e0b', err: '#dc2626', running: '#3b82f6' };
    const col = colors[state] || '#525252';
    el.innerHTML = `<span style="width:7px;height:7px;border-radius:50%;background:${col};flex-shrink:0;display:inline-block;margin-right:8px;"></span>${text}`;
}

// ─── RENDER: REQUIREMENTS ─────────────────────
function renderRequirements(reqs) {
    currentRequirements = reqs;
    document.getElementById('req-count').textContent = reqs.length;
    filterRequirements();
}

function filterRequirements() {
    const q = (document.getElementById('req-search-input')?.value || '').toLowerCase();
    const cat = (document.getElementById('req-category-filter')?.value || '').toLowerCase();
    const prio = (document.getElementById('req-priority-filter')?.value || '').toLowerCase();
    const stat = (document.getElementById('req-status-filter')?.value || '').toLowerCase();

    const filtered = (currentRequirements || []).filter(r => {
        const id = (r.id || r.req_id || '').toLowerCase();
        const stmt = (r.statement || '').toLowerCase();
        const rCat = (r.category || '').toLowerCase();
        const rPrio = (r.priority || '').toLowerCase();
        const rStat = (r.approval_status || r.status || '').toLowerCase();

        if (q && !id.includes(q) && !stmt.includes(q)) return false;
        if (cat && !rCat.includes(cat)) return false;
        if (prio && !rPrio.includes(prio)) return false;
        if (stat && !rStat.includes(stat)) return false;
        return true;
    });

    renderFilteredRequirements(filtered);
}

function renderFilteredRequirements(reqs) {
    const c = document.getElementById('requirements-list');
    if (!reqs.length) {
        c.innerHTML = `<div style="text-align:center;padding:60px 0;color:#525252;font-size:15px;">No requirements matching current filter criteria.</div>`;
        return;
    }
    c.innerHTML = reqs.map((r, idx) => {
        const id = r.id || r.req_id || `REQ-${idx + 1}`;
        const ok = r.approval_status === 'approved' || r.status === 'approved';
        const hi = (r.priority || '').toLowerCase() === 'high';

        return `
        <div style="padding:16px;border-radius:8px;background:#181818;border:1px solid ${ok ? 'rgba(22,163,74,0.3)' : '#2a2a2a'};margin-bottom:10px;transition:border-color 0.15s;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:10px;">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <span class="font-mono cursor-pointer" onclick="openReqDetailModal('${id}')" title="Click to view full requirement details"
                          style="font-size:14px;font-weight:800;color:#fbbf24;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);padding:3px 10px;border-radius:4px;">${escapeHTML(id)}</span>
                    <span style="font-size:13px;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);color:#93c5fd;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">${escapeHTML(r.category || 'Functional')}</span>
                    <span style="font-size:13px;background:${hi ? 'rgba(220,38,38,0.1)' : 'rgba(245,158,11,0.08)'};border:1px solid ${hi ? 'rgba(220,38,38,0.3)' : 'rgba(245,158,11,0.2)'};color:${hi ? '#fca5a5' : '#fbbf24'};padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-weight:700;">${hi ? 'HIGH' : 'MEDIUM'}</span>
                    ${ok
                ? `<span style="font-size:13px;background:rgba(22,163,74,0.1);border:1px solid rgba(22,163,74,0.3);color:#6ee7b7;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-weight:700;display:flex;align-items:center;gap:5px;"><i class="fas fa-check" style="font-size:11px;"></i> APPROVED</span>`
                : `<span style="font-size:13px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);color:#93c5fd;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">PENDING</span>`}
                    <span style="font-size:13px;color:#525252;">Risk: <strong style="color:${(r.risk || r.risk_level) === 'High' ? '#f87171' : '#fbbf24'};">${escapeHTML(r.risk || r.risk_level || 'Medium')}</strong></span>
                </div>
                <div style="display:flex;align-items:center;gap:6px;">
                    <button onclick="openReqDetailModal('${id}')" class="btn-secondary" style="padding:6px 10px;border-radius:5px;font-size:13px;cursor:pointer;" title="View Detail Modal">
                        <i class="fas fa-eye text-amber-400 mr-1"></i> Details
                    </button>
                    ${ok
                ? `<button onclick="approveSingleReq('${id}','draft')" style="font-size:13px;padding:6px 12px;border-radius:5px;background:rgba(22,163,74,0.15);border:1px solid rgba(22,163,74,0.35);color:#6ee7b7;font-weight:800;cursor:pointer;display:flex;align-items:center;gap:6px;"><i class="fas fa-check-double"></i> Approved</button>`
                : `<button onclick="approveSingleReq('${id}','approved')" style="font-size:13px;padding:6px 12px;border-radius:5px;background:#16a34a;border:none;color:#fff;font-weight:800;cursor:pointer;display:flex;align-items:center;gap:6px;"><i class="fas fa-check"></i> Approve</button>`}
                    <button onclick="removeSingleReq('${id}')" class="btn-remove" style="padding:6px 10px;border-radius:5px;font-size:13px;cursor:pointer;"><i class="fas fa-trash"></i></button>
                    <button onclick="openEditModal('${id}')" class="btn-secondary" style="padding:6px 10px;border-radius:5px;font-size:13px;cursor:pointer;"><i class="fas fa-pen"></i></button>
                </div>
            </div>
            <p onclick="openReqDetailModal('${id}')" class="cursor-pointer hover:text-white" style="font-size:15px;color:#e5e5e5;line-height:1.65;">${escapeHTML(r.statement)}</p>
            ${r.acceptance_criteria ? `
            <div style="margin-top:10px;padding:10px 12px;border-radius:5px;background:#111;border:1px solid #1f1f1f;font-size:14px;color:#a3a3a3;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:800;color:#f59e0b;display:block;margin-bottom:4px;">ACCEPTANCE_CRITERIA:</span>
                ${escapeHTML(Array.isArray(r.acceptance_criteria) ? r.acceptance_criteria.join(' ') : r.acceptance_criteria)}
            </div>` : ''}
            ${(r.compliance_mapping || r.regulations)?.length ? `
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:8px;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#525252;">CITATIONS:</span>
                ${(r.compliance_mapping || r.regulations).map(reg => `<span style="font-family:'JetBrains Mono',monospace;font-size:12px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);color:#93c5fd;padding:2px 7px;border-radius:3px;">${escapeHTML(reg)}</span>`).join('')}
            </div>` : ''}
        </div>`;
    }).join('');
}

// ─── RENDER: COMPLIANCE ────────────────────────
function renderCompliance(mappings) {
    const c = document.getElementById('compliance-list');
    if (!mappings.length) {
        c.innerHTML = `<div style="text-align:center;padding:60px 0;color:#525252;font-size:15px;">No compliance mappings.</div>`;
        return;
    }
    c.innerHTML = mappings.map(m => `
        <div style="padding:14px;border-radius:7px;background:#181818;border:1px solid #2a2a2a;margin-bottom:10px;">
            <div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:800;color:#fbbf24;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);padding:3px 8px;border-radius:4px;">${escapeHTML(m.req_id)}</span>
                <span style="font-size:13px;background:rgba(220,38,38,0.1);border:1px solid rgba(220,38,38,0.3);color:#fca5a5;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-weight:700;">${escapeHTML(m.citation)}</span>
                <span class="font-mono" style="font-size:13px;color:#525252;">${escapeHTML(m.source_doc)}:${m.line_number}</span>
                <span style="font-size:13px;background:rgba(22,163,74,0.1);border:1px solid rgba(22,163,74,0.25);color:#6ee7b7;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-weight:700;">${escapeHTML(m.coverage)}</span>
                <span style="font-size:13px;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);color:#93c5fd;padding:3px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">${Math.round(m.confidence * 100)}% CONF</span>
            </div>
            <p style="font-size:14px;color:#a3a3a3;font-family:'JetBrains Mono',monospace;line-height:1.6;padding:10px;background:#111;border-radius:4px;border:1px solid #1f1f1f;">"${escapeHTML(m.evidence)}"</p>
        </div>`).join('');
}

// ─── RENDER: SDLC ─────────────────────────────
function renderSDLC(info, workflow) {
    if (!info) return;
    if (typeof info === 'string') {
        info = {
            recommended_model: info,
            justification: 'Selected baseline SDLC model for governance and compliance.',
            ranked_scores: { [info]: 88, 'DevSecOps': 82, 'V-Model': 76, 'Agile': 70, 'Spiral': 65, 'Waterfall': 35 }
        };
    }
    document.getElementById('sdlc-top-model').textContent = info.recommended_model || 'Agile–DevSecOps hybrid';
    document.getElementById('sdlc-rationale').textContent = info.justification || 'Governed financial engineering model.';

    let scores = { ...(info.ranked_scores || {}) };
    const entries = Object.entries(scores).sort((a, b) => b[1] - a[1]);
    const top = entries.find(([m]) => m === info.recommended_model)?.[1] || entries[0]?.[1] || 0;
    const badge = document.getElementById('sdlc-top-badge');
    if (badge) badge.textContent = `${top}% FIT #1`;

    const bars = document.getElementById('sdlc-ranking-bars');
    bars.innerHTML = entries.map(([model, score]) => {
        const isTop = model === info.recommended_model;
        return `
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;font-size:15px;">
                <span style="font-weight:${isTop ? '800' : '500'};color:${isTop ? '#fbbf24' : '#a3a3a3'};">${escapeHTML(model)}${isTop ? ' ★' : ''}</span>
                <span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:${isTop ? '#fbbf24' : '#525252'};">${score}%</span>
            </div>
            <div style="width:100%;height:6px;border-radius:3px;background:#1f1f1f;overflow:hidden;">
                <div style="height:100%;border-radius:3px;background:${isTop ? '#f59e0b' : '#2a2a2a'};width:${Math.max(score, 3)}%;transition:width 0.6s;"></div>
            </div>
        </div>`;
    }).join('');

    const wf = document.getElementById('sdlc-workflow-list');
    wf.innerHTML = (workflow || []).map((w, idx) => {
        if (typeof w === 'string') {
            const parts = w.split(':');
            const title = parts[0] || `Phase ${idx + 1}`;
            const desc = parts.slice(1).join(':').trim() || w;
            return `
            <div style="padding:14px;border-radius:7px;background:#181818;border:1px solid #2a2a2a;margin-bottom:8px;font-size:15px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-weight:800;color:#fff;">${escapeHTML(title)}</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:13px;background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.25);color:#c4b5fd;padding:3px 8px;border-radius:4px;">PHASE ${idx + 1}</span>
                </div>
                <div style="color:#a3a3a3;line-height:1.6;">${escapeHTML(desc)}</div>
            </div>`;
        }
        return `
        <div style="padding:14px;border-radius:7px;background:#181818;border:1px solid #2a2a2a;margin-bottom:8px;font-size:15px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="font-weight:800;color:#fff;">${escapeHTML(w.phase || `Phase ${idx + 1}`)}</span>
                <span style="font-family:'JetBrains Mono',monospace;font-size:13px;background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.25);color:#c4b5fd;padding:3px 8px;border-radius:4px;">${escapeHTML(w.roles || 'Engineering')}</span>
            </div>
            <div style="color:#a3a3a3;line-height:1.6;">Activities: ${Array.isArray(w.activities) ? w.activities.map(a => escapeHTML(a)).join(', ') : escapeHTML(w.activities || '')}</div>
            <div style="display:flex;justify-content:space-between;margin-top:8px;padding-top:8px;border-top:1px solid #1f1f1f;font-size:14px;">
                <span style="color:#525252;"><i class="fas fa-shield-halved" style="color:#3b82f6;margin-right:5px;"></i>${escapeHTML(w.security_controls || 'Security Baseline')}</span>
                <span style="color:#16a34a;font-weight:700;"><i class="fas fa-flag-checkered" style="margin-right:5px;"></i>Gate: ${escapeHTML(w.validation_gate || 'Quality Gate')}</span>
            </div>
        </div>`;
    }).join('');
}

// ─── RENDER: RISKS ─────────────────────────────
function renderRisks(risks) {
    document.getElementById('risk-count').textContent = risks.length;
    const c = document.getElementById('risk-list');
    if (!risks.length) {
        c.innerHTML = `<div style="text-align:center;padding:60px 0;color:#525252;font-size:15px;">No risks recorded.</div>`;
        return;
    }
    c.innerHTML = risks.map(k => `
        <div style="padding:14px;border-radius:7px;background:#181818;border:1px solid #2a2a2a;margin-bottom:10px;font-size:15px;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:800;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);color:#fbbf24;padding:3px 8px;border-radius:4px;">${escapeHTML(k.id)}</span>
                    <span style="font-weight:700;color:#fff;">${escapeHTML(k.category)}</span>
                </div>
                <div style="display:flex;align-items:center;gap:10px;font-size:14px;color:#525252;">
                    <span>Likelihood: <strong style="color:#e5e5e5;">${escapeHTML(k.likelihood)}</strong></span>
                    <span>Impact: <strong style="color:#f87171;">${escapeHTML(k.impact)}</strong></span>
                    <span style="font-family:'JetBrains Mono',monospace;font-weight:800;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);color:#fbbf24;padding:2px 8px;border-radius:4px;">SCORE: ${k.score}/10</span>
                </div>
            </div>
            <p style="color:#e5e5e5;line-height:1.65;">${escapeHTML(k.description)}</p>
            <div style="margin-top:10px;padding:10px 12px;border-radius:5px;background:#111;border:1px solid rgba(22,163,74,0.2);font-size:14px;color:#6ee7b7;">
                <strong style="font-family:'JetBrains Mono',monospace;font-size:12px;display:block;margin-bottom:4px;"><i class="fas fa-shield-heart" style="margin-right:5px;"></i>MITIGATION:</strong>
                ${escapeHTML(k.mitigation)}
            </div>
        </div>`).join('');
}

// ─── RENDER: CLARIFICATIONS ────────────────────
function renderClarifications(clarifications, conflicts) {
    const c = document.getElementById('quality-findings-container');
    let html = '';

    if (conflicts?.length) {
        html += `
        <div style="margin-bottom:16px;">
            <h4 style="font-size:15px;font-weight:800;color:#f87171;letter-spacing:0.05em;font-family:'JetBrains Mono',monospace;margin-bottom:10px;">
                <i class="fas fa-triangle-exclamation" style="margin-right:6px;"></i>CONTRADICTIONS_DETECTED (${conflicts.length})
            </h4>`;
        conflicts.forEach(cf => {
            html += `
            <div style="padding:14px;border-radius:7px;background:#181818;border:1px solid rgba(220,38,38,0.3);margin-bottom:8px;font-size:15px;">
                <div style="font-weight:800;color:#f87171;display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#dc2626;flex-shrink:0;"></span>
                    ${escapeHTML(cf.type || 'Requirement Contradiction')}
                </div>
                <p style="color:#e5e5e5;line-height:1.65;">${escapeHTML(cf.description || cf)}</p>
                ${cf.resolution ? `<div style="margin-top:8px;padding:10px;border-radius:5px;background:#111;border:1px solid rgba(59,130,246,0.2);font-size:14px;color:#93c5fd;"><strong>Resolution:</strong> ${escapeHTML(cf.resolution)}</div>` : ''}
            </div>`;
        });
        html += '</div>';
    }

    if (clarifications?.length) {
        html += `
        <div>
            <h4 style="font-size:15px;font-weight:800;color:#fbbf24;letter-spacing:0.05em;font-family:'JetBrains Mono',monospace;margin-bottom:10px;">
                <i class="fas fa-circle-question" style="margin-right:6px;"></i>AMBIGUITY_FLAGS (${clarifications.length})
            </h4>`;
        clarifications.forEach(q => {
            const qText = q.clarification_question || q;
            html += `
            <div style="padding:14px;border-radius:7px;background:#181818;border:1px solid rgba(245,158,11,0.25);margin-bottom:8px;font-size:15px;display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
                <div>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:800;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);color:#fbbf24;padding:2px 8px;border-radius:4px;display:inline-block;margin-bottom:8px;">TERM: ${escapeHTML(q.term || 'ambiguity')}</span>
                    <p style="color:#e5e5e5;line-height:1.65;">${escapeHTML(qText)}</p>
                </div>
                <button onclick="injectClarificationPrompt('${escapeHTML(qText).replace(/'/g, "\\'")}')"
                    style="padding:8px 14px;border-radius:5px;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);color:#fbbf24;font-weight:800;font-size:14px;cursor:pointer;white-space:nowrap;flex-shrink:0;">
                    Answer
                </button>
            </div>`;
        });
        html += '</div>';
    }

    if (!html) {
        html = `
        <div style="padding:24px;border-radius:7px;background:#181818;border:1px solid rgba(22,163,74,0.3);text-align:center;">
            <i class="fas fa-circle-check" style="font-size:32px;color:#16a34a;display:block;margin-bottom:12px;"></i>
            <p style="font-size:16px;font-weight:800;color:#fff;">QUALITY_GATE_PASSED</p>
            <p style="font-size:14px;color:#525252;margin-top:4px;">Zero contradictions or ambiguities detected.</p>
        </div>`;
    }

    c.innerHTML = html;
}

function injectClarificationPrompt(question) {
    const inp = document.getElementById('user-input');
    inp.value = `Regarding: "${question}" → `;
    inp.focus();
}

// ─── RENDER: ARTIFACTS ─────────────────────────
function renderArtifacts(srsPlan) {
    document.getElementById('srs-preview-box').textContent = srsPlan || 'No SRS generated yet.';
}

// ─── RENDER: AUDIT TRAIL ───────────────────────
function renderAuditTrail(trail) {
    const c = document.getElementById('audit-trail-timeline');
    if (!trail?.length) {
        c.innerHTML = `<div style="text-align:center;padding:60px 0;color:#525252;font-size:15px;">No audit events yet.</div>`;
        return;
    }
    c.innerHTML = [...trail].reverse().map(ev => `
        <div style="padding:12px;border-radius:6px;background:#181818;border:1px solid #2a2a2a;margin-bottom:8px;display:flex;align-items:flex-start;gap:12px;font-size:15px;">
            <span class="font-mono" style="font-size:13px;color:#525252;white-space:nowrap;background:#111;border:1px solid #1f1f1f;padding:4px 8px;border-radius:4px;flex-shrink:0;">
                ${(ev.timestamp || ev.created_at || '').split('T')[1]?.split('.')[0] || 'UTC'}
            </span>
            <div>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span class="font-mono" style="font-size:14px;font-weight:700;color:#fbbf24;">${escapeHTML(ev.agent)}</span>
                    <span style="color:#2a2a2a;">→</span>
                    <span style="font-weight:600;color:#e5e5e5;">${escapeHTML(ev.action)}</span>
                </div>
                <p style="font-size:14px;color:#525252;">${escapeHTML(ev.detail)}</p>
            </div>
        </div>`).join('');
}

// ─── APPROVALS ─────────────────────────────────
async function approveSection(section) {
    if (!currentProjectId) { alert('Please start a project first.'); return; }
    const comments = prompt(`Remarks for approving '${section}':`, 'Approved by stakeholder sign-off');
    if (comments === null) return;
    try {
        const r = await authorizedFetch('/session/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: currentProjectId, section, status: 'approved', comments: comments || 'Approved' })
        });
        const res = await r.json();
        if (r.ok) {
            if (section === 'requirements') {
                currentRequirements.forEach(req => { req.approval_status = 'approved'; req.status = 'approved'; });
                renderRequirements(currentRequirements);
            }
            showToast(`Section '${section}' approved ✓`);
            if (res.audit_trail) renderAuditTrail(res.audit_trail);
        } else { alert(`Approval failed: ${res.detail}`); }
    } catch { alert('Error connecting to server.'); }
}

async function approveSingleReq(reqId, status) {
    const r = currentRequirements.find(i => (i.id || i.req_id) === reqId);
    if (!currentProjectId) {
        if (r) { r.approval_status = status; r.status = status; renderRequirements(currentRequirements); }
        return;
    }
    try {
        const resp = await authorizedFetch('/session/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: currentProjectId, section: 'requirements', req_id: reqId, status, comments: `${reqId} marked ${status}` })
        });
        const res = await resp.json();
        if (resp.ok) {
            if (r) { r.approval_status = status; r.status = status; }
            renderRequirements(currentRequirements);
            if (res.audit_trail) renderAuditTrail(res.audit_trail);
        }
    } catch { alert('Failed to update.'); }
}

async function removeSingleReq(reqId) {
    if (!confirm(`Remove requirement ${reqId}?`)) return;
    if (!currentProjectId) {
        currentRequirements = currentRequirements.filter(i => (i.id || i.req_id) !== reqId);
        renderRequirements(currentRequirements);
        return;
    }
    try {
        const r = await authorizedFetch('/session/requirement/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: currentProjectId, req_id: reqId, reason: 'Removed via dashboard' })
        });
        const res = await r.json();
        if (r.ok && res.status === 'success') {
            currentRequirements = currentRequirements.filter(i => (i.id || i.req_id) !== reqId);
            renderRequirements(currentRequirements);
            if (res.audit_trail) renderAuditTrail(res.audit_trail);
        }
    } catch { alert('Failed to remove.'); }
}

function approveAllReqs() { approveSection('requirements'); }

// ─── EDIT MODAL ────────────────────────────────
function openEditModal(reqId) {
    const r = currentRequirements.find(i => (i.id || i.req_id) === reqId);
    if (!r) return;
    editingReqId = reqId;
    document.getElementById('modal-req-id').textContent = reqId;
    document.getElementById('modal-statement').value = r.statement || '';
    document.getElementById('modal-priority').value = r.priority || 'Medium';
    document.getElementById('modal-status').value = r.status || r.approval_status || 'draft';
    document.getElementById('modal-comments').value = '';
    const m = document.getElementById('edit-modal');
    m.classList.remove('hidden');
    m.style.display = 'flex';
}

function closeEditModal() {
    const m = document.getElementById('edit-modal');
    m.classList.add('hidden');
    m.style.display = 'none';
    editingReqId = null;
}

async function saveEditRequirement() {
    if (!editingReqId) return;
    const stmt = document.getElementById('modal-statement').value.trim();
    const prio = document.getElementById('modal-priority').value;
    const stat = document.getElementById('modal-status').value;
    const comm = document.getElementById('modal-comments').value.trim();

    if (currentProjectId) {
        try {
            await authorizedFetch('/session/requirement/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: currentProjectId, req_id: editingReqId, statement: stmt, priority: prio, status: stat, comments: comm })
            });
        } catch { }
    }
    const r = currentRequirements.find(i => (i.id || i.req_id) === editingReqId);
    if (r) { r.statement = stmt; r.priority = prio; r.status = stat; r.approval_status = stat; }
    closeEditModal();
    renderRequirements(currentRequirements);
}

// ─── EXPORT ────────────────────────────────────
function exportArtifact(type) {
    if (!currentProjectId) { alert('Generate a project first.'); return; }
    window.open(`/session/${currentProjectId}/export/${type}`, '_blank');
}

// ─── SESSION ───────────────────────────────────
async function reloadSessionState() {
    if (!currentProjectId) return;
    try {
        const r = await authorizedFetch(`/session/${currentProjectId}`);
        const s = await r.json();
        if (s.audit_trail) renderAuditTrail(s.audit_trail);
    } catch { }
}

function resetSession() {
    if (!confirm('Reset current project and start a new session?')) return;
    currentProjectId = null;
    currentSessionTitle = null;
    projectData = null;
    currentRequirements = [];
    document.getElementById('active-project-tag').innerHTML = 'NO ACTIVE SESSION';
    document.getElementById('active-project-tag').removeAttribute('title');
    document.getElementById('session-action-btns').style.display = 'none';
    document.getElementById('chat-window').innerHTML = '';
    document.getElementById('user-input').value = '';
    setPipelineStatus('', 'SYSTEM_IDLE :: READY_FOR_INPUT');
    renderRequirements([]);
    renderCompliance([]);
    renderRisks([]);
    renderClarifications([], []);
    renderArtifacts('');
    renderAuditTrail([]);
    setAgentsActive(false);
}

// ─────────────────────────────────────────────────────────────────────────────
// CHAT HISTORY & RESTORATION MANAGEMENT
// ─────────────────────────────────────────────────────────────────────────────
let cachedHistorySessions = [];

function openHistoryModal() {
    const m = document.getElementById('history-modal');
    if (!m) return;
    m.classList.remove('hidden');
    m.style.display = 'flex';
    refreshHistoryList();
}

function closeHistoryModal() {
    const m = document.getElementById('history-modal');
    if (!m) return;
    m.classList.add('hidden');
    m.style.display = 'none';
}

async function refreshHistoryList() {
    const listEl = document.getElementById('history-list');
    const badge = document.getElementById('history-count-badge');
    if (!listEl) return;

    listEl.innerHTML = `
        <div style="text-align:center;padding:36px;color:#a3a3a3;font-family:'JetBrains Mono',monospace;">
            <i class="fas fa-circle-notch fa-spin text-purple-400 mr-2"></i> Loading saved chats...
        </div>`;

    try {
        const res = await fetch('/history');
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            listEl.innerHTML = `<div style="text-align:center;padding:30px;color:#f87171;">Failed to load saved history: ${escapeHTML(data.detail || 'Server error')}</div>`;
            return;
        }

        cachedHistorySessions = data.sessions || [];
        if (badge) badge.textContent = `${cachedHistorySessions.length} session${cachedHistorySessions.length === 1 ? '' : 's'}`;
        filterHistoryList();
    } catch (err) {
        listEl.innerHTML = `<div style="text-align:center;padding:30px;color:#f87171;">Error connecting to server.</div>`;
    }
}

function filterHistoryList() {
    const q = (document.getElementById('history-search-input')?.value || '').trim().toLowerCase();
    const filtered = cachedHistorySessions.filter(s => {
        if (!q) return true;
        const title = (s.title || '').toLowerCase();
        const domain = (s.domain || '').toLowerCase();
        const role = (s.role || '').toLowerCase();
        const id = (s.id || '').toLowerCase();
        return title.includes(q) || domain.includes(q) || role.includes(q) || id.includes(q);
    });
    renderHistoryItems(filtered);
}

function renderHistoryItems(sessions) {
    const listEl = document.getElementById('history-list');
    if (!listEl) return;

    if (!sessions || sessions.length === 0) {
        listEl.innerHTML = `
            <div style="text-align:center;padding:48px 20px;border-radius:8px;background:#141414;border:1px dashed #333;">
                <i class="fas fa-box-open" style="font-size:36px;color:#525252;margin-bottom:12px;display:block;"></i>
                <div style="font-size:16px;font-weight:700;color:#e5e5e5;">No Saved Chats Found</div>
                <div style="font-size:13px;color:#737373;margin-top:6px;max-width:400px;margin-left:auto;margin-right:auto;">
                    Start a project in the workspace, run your interview or analysis, and click <strong>Save Chat</strong> to preserve everything under a custom name.
                </div>
            </div>`;
        return;
    }

    listEl.innerHTML = sessions.map(s => {
        const isActive = (s.id === currentProjectId);
        const title = s.title || `${s.domain || 'Project'} — ${s.id}`;
        const updated = s.updated_at ? new Date(s.updated_at).toLocaleString() : (s.created_at ? new Date(s.created_at).toLocaleString() : 'N/A');
        const msgs = s.message_count || 0;
        const reqs = s.requirement_count !== undefined ? s.requirement_count : null;

        return `
        <div style="padding:16px 18px;border-radius:8px;background:${isActive ? 'rgba(124,58,237,0.08)' : '#161616'};border:1px solid ${isActive ? 'rgba(124,58,237,0.45)' : '#262626'};display:flex;flex-direction:column;gap:12px;transition:all 0.15s;">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;">
                <div style="flex:1;min-width:240px;">
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px;">
                        <span style="font-size:16px;font-weight:800;color:#fff;display:flex;align-items:center;gap:8px;">
                            <i class="fas fa-comments" style="color:#a78bfa;"></i>
                            ${escapeHTML(title)}
                        </span>
                        ${isActive ? `<span style="font-size:11px;font-family:'JetBrains Mono',monospace;background:rgba(22,163,74,0.18);border:1px solid rgba(22,163,74,0.4);color:#4ade80;padding:2px 7px;border-radius:4px;font-weight:700;">CURRENT ACTIVE</span>` : ''}
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12.5px;">
                        <span style="background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.3);color:#93c5fd;padding:2px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">
                            <i class="fas fa-briefcase mr-1"></i>${escapeHTML(s.domain || 'General')}
                        </span>
                        <span style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);color:#fbbf24;padding:2px 8px;border-radius:4px;font-family:'JetBrains Mono',monospace;">
                            <i class="fas fa-user-tag mr-1"></i>${escapeHTML(s.role || 'Analyst')}
                        </span>
                        <span style="color:#888;font-family:'JetBrains Mono',monospace;font-size:12px;">
                            <i class="fas fa-comment-dots mr-1 text-purple-400"></i>${msgs} message${msgs === 1 ? '' : 's'}
                        </span>
                        ${reqs !== null ? `
                        <span style="color:#888;font-family:'JetBrains Mono',monospace;font-size:12px;">
                            <i class="fas fa-list-check mr-1 text-amber-400"></i>${reqs} reqs
                        </span>` : ''}
                        <span style="color:#666;font-size:12px;margin-left:auto;">
                            <i class="fas fa-calendar-day mr-1"></i>${escapeHTML(updated)}
                        </span>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                    <button onclick="loadHistorySession('${s.id}')" 
                            style="background:#7c3aed;color:#fff;border:none;padding:7px 14px;border-radius:5px;font-size:13.5px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;transition:opacity 0.15s;"
                            title="Load all chat messages, requirements, and compliance records">
                        <i class="fas fa-folder-open"></i> Load Workspace
                    </button>
                    <button onclick="openRenameModal('${s.id}', '${escapeHTML(title).replace(/'/g, "\\'")}')" 
                            class="theme-btn px-2.5 py-1.5 rounded" style="font-size:13px;" title="Rename Chat">
                        <i class="fas fa-pen text-purple-300"></i>
                    </button>
                    <button onclick="deleteHistorySession('${s.id}', '${escapeHTML(title).replace(/'/g, "\\'")}')" 
                            class="theme-btn px-2.5 py-1.5 rounded" style="font-size:13px;" title="Delete Chat">
                        <i class="fas fa-trash text-red-400"></i>
                    </button>
                </div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#525252;display:flex;justify-content:space-between;">
                <span>ID: ${escapeHTML(s.id)}</span>
            </div>
        </div>`;
    }).join('');
}

async function loadHistorySession(sessionId) {
    if (!sessionId) return;
    showToast('Loading saved chat workspace...');

    try {
        const res = await fetch(`/history/${sessionId}`);
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            showToast(data.detail || 'Failed to load chat session', 'err');
            return;
        }

        const session = data.session;
        if (!session) {
            showToast('Session data not found', 'err');
            return;
        }

        currentProjectId = session.id;
        currentSessionTitle = session.title || session.id;

        // Update Header Session Display
        const tag = document.getElementById('active-project-tag');
        if (tag) {
            tag.innerHTML = `<span style="color:#a78bfa;font-weight:700;"><i class="fas fa-folder-open mr-1"></i>${escapeHTML(currentSessionTitle)}</span>`;
            tag.title = `Project ID: ${session.id}`;
        }
        const actionBtns = document.getElementById('session-action-btns');
        if (actionBtns) actionBtns.style.display = 'flex';

        // Restore Selectors
        if (session.domain) {
            const domSelect = document.getElementById('domain-select');
            if (domSelect) domSelect.value = session.domain;
        }
        if (session.role) {
            const roleSelect = document.getElementById('role-select');
            if (roleSelect) roleSelect.value = session.role;
        }

        // Restore Chat Window Messages
        const win = document.getElementById('chat-window');
        if (win) {
            win.innerHTML = '';
            const messages = session.messages || [];
            if (messages.length > 0) {
                messages.forEach(m => {
                    const content = m.html || formatMarkdown(m.content || m.text || '');
                    appendChatMessage(m.role || 'assistant', content);
                });
            } else if (session.snapshot?.initial_prompt) {
                appendChatMessage('user', escapeHTML(session.snapshot.initial_prompt));
                appendChatMessage('assistant', `
                    <div style="display:flex;flex-direction:column;gap:10px;">
                        <div style="display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:6px;background:rgba(22,163,74,0.1);border:1px solid rgba(22,163,74,0.25);">
                            <i class="fas fa-check-circle" style="color:#16a34a;font-size:19px;"></i>
                            <span style="font-size:16.5px;color:#e5e5e5;">
                                <strong style="color:#fff;">Restored Workspace:</strong> Loaded saved chat 
                                <strong style="color:#fbbf24;">${escapeHTML(currentSessionTitle)}</strong>.
                            </span>
                        </div>
                    </div>
                `);
            }
            const chatCount = document.getElementById('chat-count');
            if (chatCount) chatCount.textContent = win.children.length;
        }

        // Snapshot and Data Extraction
        const snapshot = session.snapshot || {};
        projectData = snapshot;

        // Restore Requirements
        let reqs = session.requirements || snapshot.requirements || [];
        if (reqs && !Array.isArray(reqs) && typeof reqs === 'object') {
            reqs = Object.values(reqs);
        }
        reqs = (reqs || []).map(r => ({
            ...r,
            id: r.id || r.req_id || 'REQ-?',
            statement: r.statement || r.description || '',
            category: r.category || 'Functional',
            priority: r.priority || 'Medium',
            approval_status: r.approval_status || r.status || 'draft',
            risk_level: r.risk_level || r.risk || 'Medium',
        }));
        currentRequirements = reqs;
        renderRequirements(currentRequirements);

        // Restore Compliance
        const compliance = session.compliance_mappings || snapshot.compliance_mappings || snapshot.compliance || [];
        renderCompliance(compliance);

        // Restore SDLC
        const sdlcInfo = snapshot.sdlc_info || snapshot.sdlc;
        const sdlcWorkflow = snapshot.sdlc_workflow || [];
        renderSDLC(sdlcInfo, sdlcWorkflow);

        // Restore Risks
        const risks = session.risks || snapshot.risk_register || snapshot.risks || [];
        renderRisks(risks);

        // Restore Clarifications & Conflicts
        const clarifications = snapshot.clarifications || [];
        const conflicts = session.conflicts || snapshot.conflicts || [];
        renderClarifications(clarifications, conflicts);

        // Restore Artifacts
        const srsPlan = snapshot.final_srs || snapshot.srs || snapshot.srs_plan || '';
        renderArtifacts(srsPlan);

        // Restore Audit Trail
        const audit = session.audit_logs || snapshot.audit_trail || [];
        renderAuditTrail(audit);

        // Close History Modal and Notify
        closeHistoryModal();
        setPipelineStatus('ok', `WORKSPACE_LOADED :: ${currentSessionTitle}`);
        showToast(`Loaded chat "${currentSessionTitle}" with ${currentRequirements.length} requirements! ✓`);
        switchTab('requirements');

    } catch (err) {
        showToast('Error loading chat session', 'err');
    }
}

// ─── SAVE CHAT WORKSPACE ──────────────────────
function saveChatSession() {
    if (!currentProjectId) { showToast('No active session to save', 'err'); return; }
    const m = document.getElementById('save-chat-modal');
    const input = document.getElementById('save-chat-title-input');
    if (!m || !input) return;

    const defaultTitle = currentSessionTitle || `${document.getElementById('domain-select').value} — ${new Date().toLocaleDateString()}`;
    input.value = defaultTitle;
    m.classList.remove('hidden');
    m.style.display = 'flex';
    input.focus();
    input.select();
}

function closeSaveChatModal() {
    const m = document.getElementById('save-chat-modal');
    if (!m) return;
    m.classList.add('hidden');
    m.style.display = 'none';
}

async function confirmSaveChatSession() {
    if (!currentProjectId) { showToast('No active session', 'err'); return; }
    const input = document.getElementById('save-chat-title-input');
    const title = (input?.value || '').trim() || `${document.getElementById('domain-select').value} — ${new Date().toLocaleDateString()}`;

    const win = document.getElementById('chat-window');
    const messages = [];
    if (win) {
        win.querySelectorAll('div[style*="display:flex"]').forEach(wrap => {
            const userBubble = wrap.querySelector('.chat-bubble-user');
            const asstBubble = wrap.querySelector('.chat-bubble-assistant');
            if (userBubble) {
                messages.push({ role: 'user', html: userBubble.innerHTML, created_at: new Date().toISOString() });
            } else if (asstBubble) {
                messages.push({ role: 'assistant', html: asstBubble.innerHTML, created_at: new Date().toISOString() });
            }
        });
    }

    try {
        const res = await authorizedFetch('/history/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: currentProjectId, title, messages })
        });
        const data = await res.json();
        if (res.ok) {
            currentSessionTitle = title;
            const tag = document.getElementById('active-project-tag');
            if (tag) {
                tag.innerHTML = `<span style="color:#a78bfa;font-weight:700;"><i class="fas fa-folder-open mr-1"></i>${escapeHTML(title)}</span>`;
            }
            closeSaveChatModal();
            showToast(`Chat "${title}" saved ✓`);
            const btn = document.getElementById('save-chat-btn');
            if (btn) {
                btn.innerHTML = '<i class="fas fa-check"></i> Saved';
                setTimeout(() => { btn.innerHTML = '<i class="fas fa-floppy-disk"></i> Save Chat'; }, 2500);
            }
        } else {
            showToast(data.detail || 'Save failed', 'err');
        }
    } catch {
        showToast('Server unreachable', 'err');
    }
}

// ─── RENAME CHAT ──────────────────────────────
function openRenameModal(sessionId, currentTitle) {
    const m = document.getElementById('rename-chat-modal');
    const idInput = document.getElementById('rename-session-id');
    const titleInput = document.getElementById('rename-title-input');
    if (!m || !idInput || !titleInput) return;

    idInput.value = sessionId;
    titleInput.value = currentTitle;
    m.classList.remove('hidden');
    m.style.display = 'flex';
    titleInput.focus();
    titleInput.select();
}

function closeRenameModal() {
    const m = document.getElementById('rename-chat-modal');
    if (!m) return;
    m.classList.add('hidden');
    m.style.display = 'none';
}

async function confirmRenameSession() {
    const sessionId = document.getElementById('rename-session-id')?.value;
    const newTitle = (document.getElementById('rename-title-input')?.value || '').trim();
    if (!sessionId || !newTitle) { showToast('Please enter a valid title', 'err'); return; }

    try {
        const res = await fetch(`/history/${sessionId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        const data = await res.json();
        if (res.ok) {
            closeRenameModal();
            showToast('Chat renamed ✓');
            if (currentProjectId === sessionId) {
                currentSessionTitle = newTitle;
                const tag = document.getElementById('active-project-tag');
                if (tag) {
                    tag.innerHTML = `<span style="color:#a78bfa;font-weight:700;"><i class="fas fa-folder-open mr-1"></i>${escapeHTML(newTitle)}</span>`;
                }
            }
            refreshHistoryList();
        } else {
            showToast(data.detail || 'Rename failed', 'err');
        }
    } catch {
        showToast('Server unreachable', 'err');
    }
}

// ─── DELETE CHAT ──────────────────────────────
async function deleteHistorySession(sessionId, title) {
    if (!confirm(`Delete saved chat "${title || sessionId}"?\nThis cannot be undone.`)) return;

    try {
        const res = await fetch(`/history/${sessionId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
            showToast('Saved chat deleted ✓');
            refreshHistoryList();
        } else {
            showToast(data.detail || 'Delete failed', 'err');
        }
    } catch {
        showToast('Server unreachable', 'err');
    }
}

function discardChatSession() {
    if (!confirm('Discard this chat? It will NOT be saved.')) return;
    resetSession();
    showToast('Chat discarded.');
}

// ─── TOAST ─────────────────────────────────────
function showToast(msg, type = 'ok') {
    const el = document.getElementById('toast-msg');
    if (!el) return;
    el.textContent = msg;
    el.style.background = type === 'err' ? 'rgba(220,38,38,0.95)' : 'rgba(22,163,74,0.95)';
    el.style.opacity = '1';
    el.style.pointerEvents = 'auto';
    setTimeout(() => { el.style.opacity = '0'; el.style.pointerEvents = 'none'; }, 3000);
}

// ─────────────────────────────────────────────────────────────────────────────
// AUTHENTICATION, RBAC & MFA STATE
// ─────────────────────────────────────────────────────────────────────────────
let currentAuthUser = (() => {
    try { return JSON.parse(sessionStorage.getItem('finreq.authUser') || 'null'); }
    catch { return null; }
})();
let pendingLoginEmail = '';
let selectedUploadFile = null;
let detailActiveReqId = null;
let activeConflictId = null;

function openAuthModal() {
    const m = document.getElementById('auth-modal');
    if (!m) return;
    m.classList.remove('hidden');
    m.style.display = 'flex';
    document.getElementById('auth-login-view').classList.remove('hidden');
    document.getElementById('auth-mfa-view').classList.add('hidden');
}

function closeAuthModal() {
    const m = document.getElementById('auth-modal');
    if (!m) return;
    m.classList.add('hidden');
    m.style.display = 'none';
}

function quickLogin(email, role) {
    document.getElementById('auth-email-input').value = email;
    // Demo personas use the seeded development password shown in the form.
    document.getElementById('auth-password-input').value = 'FinReq2026!';
    submitLogin(email);
}

async function authorizedFetch(url, options = {}) {
    if (!currentAuthUser?.token) {
        openAuthModal();
        throw new Error('Sign in required');
    }
    const headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${currentAuthUser.token}`);
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        currentAuthUser = null;
        sessionStorage.removeItem('finreq.authUser');
        openAuthModal();
        showToast('Your session expired. Please sign in again.', 'err');
    }
    return response;
}

async function submitLogin(forcedEmail = null) {
    const email = forcedEmail || document.getElementById('auth-email-input').value.trim();
    const password = document.getElementById('auth-password-input').value.trim();
    if (!email || !password) {
        showToast('Please enter email and password', 'err');
        return;
    }
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || 'Authentication failed', 'err');
            return;
        }

        if (data.status === 'mfa_required') {
            pendingLoginEmail = data.email;
            document.getElementById('auth-login-view').classList.add('hidden');
            document.getElementById('auth-mfa-view').classList.remove('hidden');
            document.getElementById('auth-mfa-code').focus();
            showToast('MFA code required', 'ok');
        } else if (data.status === 'success') {
            setAuthenticatedUser(data.user, data.token);
            closeAuthModal();
            showToast(`Logged in as ${data.user.role}`, 'ok');
        }
    } catch (e) {
        showToast('Auth server unreachable', 'err');
    }
}

async function submitMFA() {
    const code = document.getElementById('auth-mfa-code').value.trim();
    if (!code) {
        showToast('Enter 6-digit TOTP code', 'err');
        return;
    }
    try {
        const res = await fetch('/api/auth/mfa/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: pendingLoginEmail, code })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || 'Invalid MFA code', 'err');
            return;
        }
        setAuthenticatedUser(data.user, data.token);
        closeAuthModal();
        showToast(`MFA Verified: Logged in as ${data.user.role}`, 'ok');
    } catch (e) {
        showToast('MFA verification error', 'err');
    }
}

function setAuthenticatedUser(user, token) {
    currentAuthUser = { ...user, token };
    // Keep the bearer token only for this browser tab. It is restored after a
    // refresh, but disappears when the tab/session is closed.
    sessionStorage.setItem('finreq.authUser', JSON.stringify(currentAuthUser));
    const label = document.getElementById('current-user-label');
    if (label) {
        const roleName = user.role.replace('_', ' ');
        label.textContent = `${roleName} (MFA Active)`;
    }
    // Also align persona selector
    const roleSelect = document.getElementById('role-select');
    if (roleSelect) {
        const roleMap = {
            'ANALYST': 'Business Analyst',
            'COMPLIANCE_OFFICER': 'Compliance Officer',
            'SECURITY_LEAD': 'Information-Security Team',
            'APPROVER': 'Software Architect',
            'STAKEHOLDER': 'Customer',
            'ADMIN': 'Product Owner'
        };
        if (roleMap[user.role]) roleSelect.value = roleMap[user.role];
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// DOCUMENT UPLOAD HANDLING
// ─────────────────────────────────────────────────────────────────────────────
function openUploadModal() {
    const m = document.getElementById('upload-modal');
    if (!m) return;
    m.classList.remove('hidden');
    m.style.display = 'flex';
    document.getElementById('upload-status').classList.add('hidden');
    selectedUploadFile = null;
    document.getElementById('upload-submit-btn').disabled = true;
    const dz = document.getElementById('drop-zone');
    if (dz) {
        dz.onclick = () => document.getElementById('file-upload-input').click();
    }
}

function closeUploadModal() {
    const m = document.getElementById('upload-modal');
    if (!m) return;
    m.classList.add('hidden');
    m.style.display = 'none';
}

function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    selectedUploadFile = file;
    const dz = document.getElementById('drop-zone');
    if (dz) {
        dz.innerHTML = `
            <i class="fas fa-file-check text-3xl text-emerald-400 mb-2"></i>
            <p class="text-sm font-bold text-white">${escapeHTML(file.name)}</p>
            <p class="text-xs text-neutral-400 mt-1">${(file.size / 1024).toFixed(1)} KB — Ready to Ingest</p>
        `;
    }
    document.getElementById('upload-submit-btn').disabled = false;
}

async function executeUpload() {
    if (!selectedUploadFile) return;
    const btn = document.getElementById('upload-submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Ingesting...';

    const statusEl = document.getElementById('upload-status');
    statusEl.classList.remove('hidden');
    statusEl.innerHTML = '<span class="text-amber-400">Extracting text & computing pgvector embeddings...</span>';

    const formData = new FormData();
    formData.append('file', selectedUploadFile);
    if (currentProjectId) formData.append('project_id', currentProjectId);

    try {
        const res = await authorizedFetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (!res.ok) {
            statusEl.innerHTML = `<span class="text-red-400">Error: ${escapeHTML(data.detail || 'Upload failed')}</span>`;
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-upload mr-1"></i> Ingest Document';
            return;
        }

        statusEl.innerHTML = `<span class="text-emerald-400">✓ Ingested: ${data.characters_extracted} chars, ${data.chunks_indexed} vectors embedded into pgvector.</span>`;
        showToast('Document indexed into pgvector knowledge base ✓');

        // Populate prompt input with document preview if empty
        const input = document.getElementById('user-input');
        if (input && !input.value.trim() && data.preview) {
            input.value = `Analysis based on uploaded document ${data.filename}:\n${data.preview}`;
        }

        setTimeout(() => {
            closeUploadModal();
        }, 1500);
    } catch (e) {
        statusEl.innerHTML = '<span class="text-red-400">Upload connection failed.</span>';
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-upload mr-1"></i> Ingest Document';
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// REQUIREMENT DETAIL MODAL & GOVERNANCE
// ─────────────────────────────────────────────────────────────────────────────
function openReqDetailModal(reqId) {
    const req = (currentRequirements || []).find(r => (r.id || r.req_id) === reqId);
    if (!req) return;
    detailActiveReqId = reqId;

    document.getElementById('detail-req-id').textContent = reqId;
    document.getElementById('detail-category').textContent = req.category || 'Functional';
    document.getElementById('detail-statement').textContent = req.statement || '';
    document.getElementById('detail-source').textContent = req.source || 'Business Analyst';
    document.getElementById('detail-risk').textContent = req.risk || req.risk_level || 'Medium';
    document.getElementById('detail-confidence').textContent = `${Math.round((req.confidence || 0.94) * 100)}%`;

    const ac = req.acceptance_criteria;
    const acText = Array.isArray(ac) ? ac.join(' ') : (ac || 'Given standard preconditions When processed Then verify state transition.');
    document.getElementById('detail-acceptance').textContent = acText;

    const regs = req.compliance_mapping || req.regulations || ['KB-REG-ISO-27001'];
    const regContainer = document.getElementById('detail-regulations');
    regContainer.innerHTML = regs.map(r => `
        <span class="badge-amber text-xs font-mono px-2 py-0.5 rounded">${escapeHTML(r)}</span>
    `).join('');

    const modal = document.getElementById('req-detail-modal');
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
}

function closeReqDetailModal() {
    const m = document.getElementById('req-detail-modal');
    if (!m) return;
    m.classList.add('hidden');
    m.style.display = 'none';
}

function handleDetailAction(status) {
    if (!detailActiveReqId) return;
    approveSingleReq(detailActiveReqId, status);
    closeReqDetailModal();
}

function openEditFromDetail() {
    if (!detailActiveReqId) return;
    const reqId = detailActiveReqId;
    closeReqDetailModal();
    openEditModal(reqId);
}

// ─────────────────────────────────────────────────────────────────────────────
// CONFLICT RESOLUTION MODAL
// ─────────────────────────────────────────────────────────────────────────────
function openConflictModal(conflictId, req1, req2, desc) {
    activeConflictId = conflictId;
    document.getElementById('conflict-modal-desc').textContent = desc || `Conflict between requirements ${req1} and ${req2}`;
    const m = document.getElementById('conflict-modal');
    m.classList.remove('hidden');
    m.style.display = 'flex';
}

function closeConflictModal() {
    const m = document.getElementById('conflict-modal');
    if (!m) return;
    m.classList.add('hidden');
    m.style.display = 'none';
}

async function submitConflictResolution() {
    const resolution = document.getElementById('conflict-resolution-text').value.trim();
    if (!resolution) {
        showToast('Please enter resolution explanation', 'err');
        return;
    }
    try {
        const res = await authorizedFetch('/api/conflicts/resolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: currentProjectId || 'DEFAULT',
                conflict_id: activeConflictId,
                resolution
            })
        });
        if (res.ok) {
            showToast('Conflict resolved and logged to audit trail ✓');
            closeConflictModal();
            refreshAuditTrail();
        } else {
            showToast('Conflict resolution failed', 'err');
        }
    } catch {
        showToast('Server unreachable', 'err');
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// TRACEABILITY MATRIX (RTM)
// ─────────────────────────────────────────────────────────────────────────────
async function fetchTraceabilityMatrix() {
    const tbody = document.getElementById('rtm-table-body');
    if (!currentProjectId) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:#525252;">No active session. Submit requirements to generate RTM.</td></tr>`;
        return;
    }
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:#a3a3a3;"><i class="fas fa-spinner fa-spin mr-2"></i> Loading Traceability Matrix...</td></tr>`;

    try {
        const res = await authorizedFetch(`/session/${currentProjectId}/rtm_matrix`);
        const data = await res.json();
        if (!res.ok || !data.matrix?.length) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:30px;color:#525252;">No matrix rows found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.matrix.map((row, idx) => {
            const isApproved = row.approval_status === 'approved';
            return `
                <tr style="border-bottom:1px solid #1f1f1f;background:${idx % 2 === 0 ? 'transparent' : '#0f0f0f'};">
                    <td style="padding:10px 8px;color:#fbbf24;font-weight:700;">${escapeHTML(row.req_id)}</td>
                    <td style="padding:10px 8px;color:#e5e5e5;max-width:240px;line-height:1.4;">${escapeHTML(row.statement)}</td>
                    <td style="padding:10px 8px;color:#93c5fd;">${escapeHTML(row.source_stakeholder)}</td>
                    <td style="padding:10px 8px;color:#fca5a5;">${escapeHTML(row.regulation)}</td>
                    <td style="padding:10px 8px;color:#c084fc;">${escapeHTML(row.control)}</td>
                    <td style="padding:10px 8px;color:#a3a3a3;max-width:200px;">${escapeHTML(row.test_scenario)}</td>
                    <td style="padding:10px 8px;">
                        <span style="font-size:11px;padding:2px 6px;border-radius:3px;background:${isApproved ? 'rgba(22,163,74,0.15)' : 'rgba(245,158,11,0.1)'};color:${isApproved ? '#6ee7b7' : '#fbbf24'};border:1px solid ${isApproved ? 'rgba(22,163,74,0.3)' : 'rgba(245,158,11,0.3)'};">
                            ${isApproved ? 'APPROVED' : 'PENDING'}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
    } catch {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:30px;color:#f87171;">Failed to load traceability matrix.</td></tr>`;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// ADMIN & MONITORING TELEMETRY
// ─────────────────────────────────────────────────────────────────────────────
async function fetchAdminMetrics() {
    try {
        const res = await authorizedFetch('/api/admin/metrics');
        const data = await res.json();
        if (!res.ok || !data.metrics) return;
        const m = data.metrics;

        document.getElementById('metric-db').textContent = m.database || 'PostgreSQL + pgvector';
        const redisStatus = m.cache?.status === 'connected' ? 'Connected (6379)' : 'In-Memory Fallback';
        document.getElementById('metric-redis').textContent = redisStatus;
        document.getElementById('metric-reqs').textContent = m.total_requirements || '0';
        document.getElementById('metric-runs').textContent = m.agent_executions || '0';

        const runsTbody = document.getElementById('admin-runs-body');
        if (m.recent_agent_runs && m.recent_agent_runs.length) {
            runsTbody.innerHTML = m.recent_agent_runs.map((run, idx) => `
                <tr style="border-bottom:1px solid #1f1f1f;background:${idx % 2 === 0 ? 'transparent' : '#0f0f0f'};">
                    <td style="padding:8px;color:#fff;font-weight:700;">${escapeHTML(run.agent)}</td>
                    <td style="padding:8px;"><span class="text-emerald-400">✓ ${escapeHTML(run.status)}</span></td>
                    <td style="padding:8px;color:#fbbf24;">${run.duration_ms} ms</td>
                    <td style="padding:8px;color:#525252;">${escapeHTML(run.time)}</td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error('Failed to load admin telemetry:', e);
    }
}

// The workspace remains visible for orientation, but no action can be taken
// until the user completes the login + MFA flow.
window.addEventListener('DOMContentLoaded', () => {
    if (currentAuthUser?.token) {
        setAuthenticatedUser(currentAuthUser, currentAuthUser.token);
    } else {
        openAuthModal();
    }
});

window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeHistoryModal();
        closeSaveChatModal();
        closeRenameModal();
        if (typeof closeUploadModal === 'function') closeUploadModal();
        if (typeof closeReqDetailModal === 'function') closeReqDetailModal();
        if (typeof closeConflictModal === 'function') closeConflictModal();
        if (currentAuthUser?.token && typeof closeAuthModal === 'function') closeAuthModal();
    }
});

