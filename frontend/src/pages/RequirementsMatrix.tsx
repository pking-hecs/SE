import React from 'react';
import { Table, Tag, Button, Space, Card, Typography } from 'antd';
import { CheckCircleOutlined, WarningOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

const RequirementsMatrix = () => {
  const data = [
    { key: '1', id: 'FR-ONB-001', statement: 'Verify customer identity via OTP', category: 'SECURITY', priority: 'HIGH', risk: 'LOW', confidence: '94%', compliance: 'FULL', status: 'APPROVED' },
    { key: '2', id: 'FR-ONB-002', statement: 'Onboarding time < 2 mins', category: 'PERFORMANCE', priority: 'MEDIUM', risk: 'MEDIUM', confidence: '82%', compliance: 'PARTIAL', status: 'VALIDATED' },
    { key: '3', id: 'FR-ONB-003', statement: 'Store PII in encrypted vault', category: 'PRIVACY', priority: 'HIGH', risk: 'HIGH', confidence: '91%', compliance: 'NONE', status: 'DRAFT' },
  ];

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 100 },
    { title: 'Statement', dataIndex: 'statement', key: 'statement', render: (text: string) => <Text ellipsis style={{ width: 300 }}>{text}</Text> },
    { title: 'Category', dataIndex: 'category', key: 'category', render: (cat: string) => <Tag color="blue">{cat}</Tag> },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', render: (p: string) => <Tag color={p === 'HIGH' ? 'red' : 'orange'}>{p}</Tag> },
    { title: 'Risk', dataIndex: 'risk', key: 'risk', render: (r: string) => <Tag color={r === 'HIGH' ? 'red' : 'gold'}>{r}</Tag> },
    { title: 'Confidence', dataIndex: 'confidence', key: 'confidence' },
    { title: 'Compliance', dataIndex: 'compliance', key: 'compliance', render: (c: string) => (
      <Tag color={c === 'FULL' ? 'green' : c === 'PARTIAL' ? 'orange' : 'red'}>{c}</Tag>
    )},
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'APPROVED' ? 'green' : 'blue'}>{s}</Tag> },
    { title: 'Action', key: 'action', render: () => <Button type="link" size="small">Details</Button> },
  ];

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Card title="Requirements Traceability Matrix" bordered={false} style={{ borderRadius: '8px' }}>
        <Table columns={columns} dataSource={data} pagination={false} />
      </Card>
    </div>
  );
};

export default RequirementsMatrix;
