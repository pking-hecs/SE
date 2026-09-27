import React, { useState, useEffect } from 'react';
import { Layout, Input, Button, Card, List, Tag, Row, Col, Space, Typography, Spin, message } from 'antd';
import { SendOutlined, FileTextOutlined, LoadingOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Content, Sider } = Layout;
const { Text } = Typography;

// API Base URL
const API_BASE = 'http://localhost:8000/api';

const Interview = () => {
  const [messages, setMessages] = useState<{ role: string, text: string }[]>([]);
  const [input, setInput] = useState('');
  const [requirements, setRequirements] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Replace this with a real token from your auth system
  const token = localStorage.getItem('token') || 'demo-token';

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      // Call the REAL backend API
      const response = await axios.post(
        `${API_BASE}/projects/1/chat`,
        { text: currentInput },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const { requirements, findings } = response.data;

      // Update requirements and findings from the real AI
      setRequirements(prev => {
        // Avoid duplicates by ID
        const existingIds = new Set(prev.map(r => r.requirement_id));
        const uniqueNew = requirements.filter((r: any) => !existingIds.has(r.requirement_id));
        return [...prev, ...uniqueNew];
      });

      setFindings(prev => [...prev, ...findings]);

      // Add AI response to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: `I've analyzed your input. I extracted ${requirements.length} new requirement(s) and found ${findings.length} analysis points.`
      }]);

    } catch (error: any) {
      console.error("API Error:", error);
      message.error("Failed to connect to AI Backend. Ensure the server is running on port 8000.");
      setMessages(prev => [...prev, { role: 'assistant', text: "Sorry, I'm having trouble connecting to the brain. Please check if the backend is running." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ height: 'calc(100vh - 64px)' }}>
      <Content style={{ display: 'flex', padding: '24px', gap: '24px', background: '#f0f2f5' }}>
        {/* Left: Chat Interface */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#fff', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <div style={{ padding: '16px', background: '#001529', color: 'white', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Stakeholder Interview</span>
            {loading && <Spin size="small" />}
          </div>
          <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: '#999', marginTop: '50px' }}>
                <FileTextOutlined style={{ fontSize: '48px', display: 'block', margin: '0 auto 16px' }} />
                <p>Start the conversation to extract requirements.</p>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={{
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                padding: '12px',
                borderRadius: '8px',
                background: m.role === 'user' ? '#1890ff' : '#f0f2f5',
                color: m.role === 'user' ? 'white' : 'black',
                boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
              }}>
                {m.text}
              </div>
            ))}
          </div>
          <div style={{ padding: '16px', borderTop: '1px solid #eee', display: 'flex', gap: '8px' }}>
            <Input.TextArea
              rows={2}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Describe the requirement..."
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            />
            <Button
              type="primary"
              icon={loading ? <LoadingOutlined /> : <SendOutlined />}
              onClick={handleSend}
              loading={loading}
            />
          </div>
        </div>

        {/* Right: Live Extraction Panel */}
        <Sider width={450} theme="light" style={{ background: '#fff', borderRadius: '8px', padding: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', overflowY: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <FileTextOutlined />
            <Text strong>Live Analysis</Text>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>EXTRACTED REQUIREMENTS</Text>
            <List
              dataSource={requirements}
              renderItem={req => (
                <Card size="small" style={{ marginBottom: '12px', borderLeft: '4px solid #1890ff' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <Text strong style={{ fontSize: '12px' }}>{req.requirement_id}</Text>
                    <Tag color={req.priority === 'HIGH' ? 'red' : 'blue'}>{req.priority}</Tag>
                  </div>
                  <Text style={{ fontSize: '13px' }}>{req.statement}</Text>
                  <div style={{ marginTop: '8px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {req.categories?.map((cat: string) => <Tag color="blue" key={cat}>{cat}</Tag>)}
                    <Tag color="orange">{req.approval_status || 'DRAFT'}</Tag>
                  </div>
                </Card>
              )}
            />
          </div>

          <div>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>QUALITY & RISK FINDINGS</Text>
            <List
              dataSource={findings}
              renderItem={finding => (
                <Card size="small" style={{ marginBottom: '12px', borderLeft: '4px solid #faad14' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <Text strong style={{ fontSize: '12px' }}>{finding.issue_type}</Text>
                    <Tag color={finding.severity === 'HIGH' ? 'red' : 'orange'}>{finding.severity}</Tag>
                  </div>
                  <Text style={{ fontSize: '13px' }}>{finding.description}</Text>
                  {finding.suggested_question && (
                    <div style={{ marginTop: '8px', fontStyle: 'italic', fontSize: '12px', color: '#666' }}>
                      Question: {finding.suggested_question}
                    </div>
                  )}
                </Card>
              )}
            />
          </div>
        </Sider>
      </Content>
    </Layout>
  );
};

export default Interview;
