import React from 'react';
import { ConfigProvider } from 'antd';
import { BrowserRouter as Router, Link, Route, Routes } from 'react-router-dom';
import { CircleUserRound, Menu } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Interview from './pages/Interview';
import RequirementsMatrix from './pages/RequirementsMatrix';

const App = () => <ConfigProvider theme={{ token: { colorPrimary: '#ef8600', borderRadius: 0, fontFamily: 'Inter, Arial, sans-serif' } }}><Router><div className="app-shell"><header className="security-nav"><Link to="/" className="brand">FINREQ <small>AT SECURITY</small></Link><nav><Link to="/">OVERVIEW</Link><Link to="/interview">INTERVIEW</Link><Link to="/matrix">REQUIREMENTS</Link></nav><div className="nav-actions"><button><CircleUserRound size={17} /></button><button><Menu size={17} /></button></div></header><Routes><Route path="/" element={<Dashboard />} /><Route path="/interview" element={<Interview />} /><Route path="/matrix" element={<RequirementsMatrix />} /></Routes></div></Router></ConfigProvider>;
export default App;
