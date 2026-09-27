import React from 'react';
import { Layout, Menu, Card, Row, Col, Statistic, Progress, Table, Tag, Button, List } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  UserOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const Dashboard = () => {
  const stats = [
    { title: 'Total Requirements', value: 42, icon: <FileTextOutlined />, color: '#1890ff' },
    { title: 'Approved', value: 31, icon: <CheckCircleOutlined />, color: '#52c41a' },
    { title: 'Pending Approval', value: 7, icon: <WarningOutlined />, color: '#faad14' },
    { title: 'Clarification Needed', value: 4, icon: <ThunderboltOutlined />, color: '#f5222d' },
  ];

  const recentActivity = [
    { id: 1, action: 'Requirement approved', req: 'FR-ONB-001', time: '2 mins ago', status: 'success' },
    { id: 2, action: 'Compliance gap detected', req: 'FR-SEC-004', time: '15 mins ago', status: 'warning' },
    { id: 3, action: 'Stakeholder interview completed', req: 'Project Baseline', time: '1 hour ago', status: 'info' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={260}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', padding: '0 24px', color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
          FIN-REQ AI
        </div>
        <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']}>
          <Menu.Item key="1" icon={<DashboardOutlined />}>Dashboard</Menu.Item>
          <Menu.Item key="2" icon={<FileTextOutlined />}>Requirements</Menu.Item>
          <Menu.Item key="3" icon={<CheckCircleOutlined />}>Approvals</Menu.Item>
          <Menu.Item key="4" icon={<RocketOutlined />}>SDLC Advisor</Menu.Item>
          <Menu.Item key="5" icon={<UserOutlined />}>Account</Menu.Item>
        </Menu>
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0 }}>Digital Customer Onboarding</h2>
          <Button type="primary">Export SRS</Button>
        </Header>
        <Content style={{ margin: '24px', background: '#f0f2f5', padding: '24px' }}>
          <Row gutter={[16, 16]}>
            {stats.map((s, i) => (
              <Col span={6} key={i}>
                <Card bordered={false}>
                  <Statistic
                    title={s.title}
                    value={s.value}
                    prefix={s.icon}
                    valueStyle={{ color: s.color }}
                  />
                </Card>
              </Col>
            ))}
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
            <Col span={16}>
              <Card title="Requirement Analysis Progress" bordered={false}>
                <div style={{ marginBottom: '20px' }}>
                  <span>Extraction</span>
                  <Progress percent={100} status="success" size="small" strokeColor="#52c41a" />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <span>Compliance Mapping</span>
                  <Progress percent={87} status="active" size="small" />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <span>Risk Assessment</span>
                  <Progress percent={100} status="success" size="small" strokeColor="#52c41a" />
                </div>
                <div>
                  <span>Human Approval</span>
                  <Progress percent={74} status="active" size="small" />
                </div>
              </Card>
            </Col>
            <Col span={8}>
              <Card title="Recent Activity" bordered={false}>
                <List
                  dataSource={recentActivity}
                  renderItem={item => (
                    <List.Item>
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <span>{item.action} <strong>{item.req}</strong></span>
                        <span style={{ fontSize: '12px', color: '#999' }}>{item.time}</span>
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
