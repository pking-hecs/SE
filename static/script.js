let currentProjectId = null;

async function sendMessage() {
    const inputField = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');
    const prompt = inputField.value.trim();

    if (!prompt) return;

    // Append User Message (Gemini style)
    appendMessage('user', prompt);
    inputField.value = '';

    const loadingId = 'loading-' + Date.now();
    appendMessage('assistant', '<div class="flex gap-2 items-center text-slate-400 text-sm"><i class="fas fa-circle-notch fa-spin"></i> Thinking...</div>', loadingId);

    try {
        let endpoint = 'http://localhost:8000/session/chat';
        let body = {
            project_id: currentProjectId,
            message: prompt
        };

        if (!currentProjectId) {
            endpoint = 'http://localhost:8000/session/start';
            body = { prompt: prompt };
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const result = await response.json();
        document.getElementById(loadingId).remove();

        if (result.status === 'success') {
            if (!currentProjectId) {
                currentProjectId = result.project_id;
            }

            if (result.initial_analysis) {
                const data = result.initial_analysis;
                const formattedResponse = `
                    <div class="space-y-6">
                        <div class="p-4 bg-slate-900/50 border border-blue-500/20 rounded-2xl shadow-inner">
                            <div class="flex justify-between items-center mb-3">
                                <h4 class="text-blue-400 font-semibold flex items-center gap-2"><i class="fas fa-list"></i> Requirements</h4>
                                <button onclick="approveSection('${currentProjectId}', 'requirements')" class="text-xs bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 px-3 py-1 rounded-full transition border border-blue-500/30">Approve</button>
                            </div>
                            <p class="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">${data.requirements}</p>
                        </div>
                        <div class="p-4 bg-slate-900/50 border border-red-500/20 rounded-2xl shadow-inner">
                            <div class="flex justify-between items-center mb-3">
                                <h4 class="text-red-400 font-semibold flex items-center gap-2"><i class="fas fa-balance-scale"></i> Compliance</h4>
                                <button onclick="approveSection('${currentProjectId}', 'compliance')" class="text-xs bg-red-600/20 hover:bg-red-600/40 text-red-300 px-3 py-1 rounded-full transition border border-red-500/30">Approve</button>
                            </div>
                            <p class="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">${data.compliance}</p>
                        </div>
                        <div class="p-4 bg-slate-900/50 border border-green-500/20 rounded-2xl shadow-inner">
                            <div class="flex justify-between items-center mb-3">
                                <h4 class="text-green-400 font-semibold flex items-center gap-2"><i class="fas fa-rocket"></i> SDLC</h4>
                                <button onclick="approveSection('${currentProjectId}', 'sdlc')" class="text-xs bg-green-600/20 hover:bg-green-600/40 text-green-300 px-3 py-1 rounded-full transition border border-green-500/30">Approve</button>
                            </div>
                            <p class="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">${data.sdlc}</p>
                        </div>
                        <div class="p-4 bg-slate-900/50 border border-purple-500/20 rounded-2xl shadow-inner">
                            <div class="flex justify-between items-center mb-3">
                                <h4 class="text-purple-400 font-semibold flex items-center gap-2"><i class="fas fa-file-alt"></i> SRS Plan</h4>
                                <button onclick="approveSection('${currentProjectId}', 'srs')" class="text-xs bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 px-3 py-1 rounded-full transition border border-purple-500/30">Approve</button>
                            </div>
                            <p class="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">${data.srs_plan}</p>
                        </div>
                        <div class="mt-2 text-xs text-slate-500 italic flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-blue-500"></span> Current Phase: ${result.current_phase}
                        </div>
                    </div>
                `;
                appendMessage('assistant', formattedResponse);
            } else if (result.response) {
                appendMessage('assistant', `<div class="space-y-2">
                    <p class="text-sm text-slate-300 leading-relaxed">${result.response}</p>
                    <div class="text-xs text-slate-500 italic flex items-center gap-2 mt-2">
                        <span class="w-2 h-2 rounded-full bg-blue-500"></span> Current Phase: ${result.current_phase}
                    </div>
                </div>`);
            }
        } else {
            appendMessage('assistant', '❌ Error: ' + result.detail);
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        appendMessage('assistant', '❌ System Error: Could not connect to Backend.');
    }
}

async function approveSection(projectId, section) {
    const comments = prompt("Add approval comments (optional):");
    if (comments === null) return;

    try {
        const response = await fetch('http://localhost:8000/session/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: projectId,
                section: section,
                content: "",
                status: "approved",
                comments: comments || "Approved by user"
            })
        });

        if (response.ok) {
            alert(`Section ${section} has been officially approved and logged.`);
        } else {
            alert("Approval failed.");
        }
    } catch (error) {
        alert("Error connecting to server.");
    }
}

function appendMessage(role, content, id = null) {
    const chatWindow = document.getElementById('chat-window');
    const div = document.createElement('div');
    div.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} w-full`;
    if (id) div.id = id;

    const inner = document.createElement('div');
    if (role === 'user') {
        inner.className = 'user-msg p-4 max-w-2xl shadow-md';
    } else {
        inner.className = 'ai-msg p-4 max-w-3xl';
        inner.innerHTML = `
            <div class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center text-[10px] text-white font-bold">AI</div>
                <div class="flex-1">${content}</div>
            </div>
        `;
    }

    if (role === 'user') {
        inner.innerHTML = content;
    }

    div.appendChild(inner);
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
