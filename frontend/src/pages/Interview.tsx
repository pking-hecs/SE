import React, { useEffect, useState } from 'react';
import { Button, Input, message } from 'antd';
import { ArrowRightOutlined, DeleteOutlined, HistoryOutlined, PlusOutlined, SendOutlined } from '@ant-design/icons';
import axios from 'axios';

const API = 'http://localhost:8000/api';
type Chat = { role: string; text: string };
type History = { id: string; title: string; updated_at: string; message_count: number };
const makeId = () => globalThis.crypto?.randomUUID?.() || `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`;

export default function Interview() {
  const [view, setView] = useState<'chat' | 'history'>('chat');
  const [chat, setChat] = useState<Chat[]>([]); const [input, setInput] = useState(''); const [history, setHistory] = useState<History[]>([]);
  const [active, setActive] = useState<string | null>(null); const [loading, setLoading] = useState(false); const [stats, setStats] = useState({ requirements: 0, findings: 0 });
  const token = localStorage.getItem('token') || 'demo-token';
  const loadHistory = async () => { try { setHistory((await axios.get(`${API}/history/`)).data.conversations || []); } catch { message.error('History service is unavailable. Restart the backend.'); } };
  useEffect(() => { if (view === 'history') loadHistory(); }, [view]);
  const newChat = () => { setActive(null); setChat([]); setStats({ requirements: 0, findings: 0 }); setView('chat'); };
  const save = (id: string, role: string, text: string) => axios.post(`${API}/history/conversations/${id}/messages`, { role, text });
  const send = async () => {
    const text = input.trim(); if (!text || loading) return;
    setInput(''); setChat(v => [...v, { role: 'user', text }]); setLoading(true);
    try {
      let id = active;
      if (!id) { id = makeId(); await axios.post(`${API}/history/conversations`, { id, title: text.slice(0, 70), project_id: 1 }); setActive(id); }
      await save(id, 'user', text);
      const result = (await axios.post(`${API}/projects/1/chat`, { text }, { headers: { Authorization: `Bearer ${token}` } })).data;
      const reply = `Analysis complete: ${result.requirements.length} requirements extracted; ${result.findings.length} findings detected.`;
      setStats({ requirements: result.requirements.length, findings: result.findings.length }); setChat(v => [...v, { role: 'assistant', text: reply }]); await save(id, 'assistant', reply);
    } catch { setChat(v => [...v, { role: 'assistant', text: 'Processing failed. Check that the backend is running.' }]); message.error('Message could not be saved.'); }
    finally { setLoading(false); }
  };
  const open = async (id: string) => { try { const c = (await axios.get(`${API}/history/conversations/${id}`)).data; setChat(c.messages || []); setActive(id); setView('chat'); } catch { message.error('Could not open chat.'); } };
  const remove = async (id: string) => { try { await axios.delete(`${API}/history/conversations/${id}`); if (active === id) newChat(); loadHistory(); } catch { message.error('Could not delete chat.'); } };
  return <><main className="threat-layout"><section className="threat-column"><span className="eyebrow">FINANCIAL REQUIREMENTS / 01</span><h1 className="threat-title">Adaptive<br />Risk<br />Guard</h1><hr className="hairline" /><p className="intro-copy">AI-assisted requirements analysis that detects ambiguity, identifies compliance gaps, and protects your financial platform before delivery.</p><p className="trust-line">● ● ● &nbsp; TRUSTED BY MODERN FINANCE TEAMS.</p><div><Button className="amber-button" type="primary" onClick={newChat}>Start analysis</Button><Button className="text-button">Explore platform <ArrowRightOutlined /></Button></div>
    <div className="chat-console"><div className="console-tabs"><div><Button className={view === 'chat' ? 'selected' : ''} onClick={() => setView('chat')}>CHAT</Button><Button className={view === 'history' ? 'selected' : ''} onClick={() => setView('history')} icon={<HistoryOutlined />}>HISTORY</Button></div><Button icon={<PlusOutlined />} onClick={newChat}>NEW</Button></div>
      {view === 'history' ? <div className="message-area">{history.length === 0 ? <span className="trust-line">NO SAVED CHATS. SEND A MESSAGE TO CREATE ONE.</span> : history.map(h => <div className="history-row" key={h.id}><strong>{h.title}</strong><small>{h.message_count} MESSAGES · {new Date(h.updated_at).toLocaleString()}</small><br /><Button size="small" type="primary" onClick={() => open(h.id)}>OPEN</Button><Button size="small" danger icon={<DeleteOutlined />} onClick={() => remove(h.id)}>DELETE</Button></div>)}</div> : <><div className="message-area">{chat.length === 0 ? <span className="trust-line">SYSTEM READY. START A SECURE INTERVIEW.</span> : chat.map((m, i) => <div className={`bubble ${m.role}`} key={i}>{m.text}</div>)}</div><Input.TextArea className="chat-input" value={input} onChange={e => setInput(e.target.value)} onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); send(); } }} placeholder="Describe the requirement…" autoSize={{ minRows: 2, maxRows: 3 }} /><Button className="amber-button" type="primary" loading={loading} onClick={send} style={{ marginTop: 8 }}>Send <SendOutlined /></Button></>}</div>
  </section><section className="threat-column center-console"><div className="scan-panel" /><div className="console-footer"><span>STABLE_NODE_ACK &nbsp; SECURITY AT THE CORE</span><Button size="small">ABOUT US</Button></div></section><section className="threat-column"><span className="eyebrow">LIVE ENGINE / v2.4</span><div className="mode-stack">Detect<br />Track<br /><span className="active">Predict</span><br />Respond</div><hr className="hairline" /><div className="technical-box">TECHNICAL SIDE<br />◉ RISK_SIGNAL_TRACE_INIT<br />▣ REQUIREMENTS: {stats.requirements}<br />▣ FINDINGS: {stats.findings}<br />△ ANOMALY_DETECTED: NULL</div></section></main><footer className="bottom-status">FINREQ DEFENSE TRAINED TO DETECT AMBIGUITY BEFORE IT SPREADS.</footer></>;
}
