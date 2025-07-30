import React, { useState } from 'react';
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Space,
  Typography,
  Switch,
  message
} from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  HistoryOutlined,
  MonitorOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MoonOutlined,
  SunOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, darkMode, toggleDarkMode } = useAuth();

  const menuItems = [
    {
      key: '/admin/dashboard',
      icon: <DashboardOutlined />,
      label: '控制台',
    },
    {
      key: '/admin/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/admin/ai-templates',
      icon: <RobotOutlined />,
      label: 'AI模板管理',
    },
    {
      key: '/admin/commits',
      icon: <HistoryOutlined />,
      label: '提交历史',
    },
    {
      key: '/admin/api-monitor',
      icon: <MonitorOutlined />,
      label: 'API监控',
    },
    {
      key: '/admin/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    message.success('已安全退出');
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '账户设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const currentPath = location.pathname;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          background: darkMode ? '#001529' : '#fff',
        }}
      >
        <div
          style={{
            height: 64,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          {!collapsed && (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <img
                src="/logo.png"
                alt="NexCode"
                style={{
                  width: 32,
                  height: 32,
                  marginRight: 12,
                  borderRadius: 6,
                }}
              />
              <Text strong style={{ fontSize: 16 }}>
                NexCode Admin
              </Text>
            </div>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[currentPath]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            border: 'none',
            background: darkMode ? '#001529' : '#fff',
          }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 16px',
            background: darkMode ? '#141414' : '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              width: 64,
              height: 64,
            }}
          />
          
          <Space size="middle">
            <Space>
              {darkMode ? <MoonOutlined /> : <SunOutlined />}
              <Switch
                checked={darkMode}
                onChange={toggleDarkMode}
                size="small"
              />
            </Space>
            
            <Dropdown
              menu={{
                items: userMenuItems,
              }}
              placement="bottomRight"
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.username}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            padding: '24px',
            minHeight: 280,
            background: darkMode ? '#1f1f1f' : '#fff',
            overflow: 'auto',
          }}
          className="admin-content"
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AdminLayout; 