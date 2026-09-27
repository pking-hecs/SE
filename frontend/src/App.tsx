import React, { useState } from 'react';
import { Layout, Menu, ConfigProvider, theme, Button, Space } from 'antd';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Interview from './pages/Interview';
import RequirementsMatrix from './pages/RequirementsMatrix';

const { Header, Sider, Content } = Layout;

const App = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  return (
    <ConfigProvider
      theme={{
        algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <Router>
        <Layout style={{ minHeight: '100vh', background: isDarkMode ? '#141414' : '#f0f2f5' }}>
          <Sider theme="dark" width={260}>
            <div style={{ height: 64, display: 'flex', alignItems: 'center', padding: '0 24px', color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
              FIN-REQ AI
            </div>
            <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']}>
              <Menu.Item key="1" onClick={() => window.location.href='/'}>Dashboard</Menu.Item>
              <Menu.Item key="2" onClick={() => window.location.href='/interview'}>Interview</Menu.Item>
              <Menu.Item key="3" onClick={() => window.location.href='/matrix'}>Requirements</Menu.Item>
            </Menu>
          </Sider>
          <Layout>
            <Header style={{
              background: isDarkMode ? '#1f1f1f' : '#fff',
              padding: '0 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              color: isDarkMode ? 'white' : 'black',
              borderBottom: isDarkMode ? '1px solid #333' : '1px solid #eee'
            }}>
              <h2 style={{ margin: 0 }}>Digital Customer Onboarding</h2>
              <Space>
                <Button
                  icon={isDarkMode ? <SunOutlined /> : <MoonOutlined />}
                  onClick={() => setIsDarkMode(!isDarkMode)}
                >
                  {isDarkMode ? 'Light Mode' : 'Dark Mode'}
                </Button>
                <Button type="primary">Export SRS</Button>
              </Space>
            </Header>
            <Content style={{ padding: '24px' }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/interview" element={<Interview />} />
                <Route path="/matrix" element={<RequirementsMatrix />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </Router>
    </ConfigProvider>
  );
};

export default App;
