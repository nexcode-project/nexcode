import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  message,
  Space,
  Divider,
  Spin,
  Alert,
} from 'antd';
import { UserOutlined, LockOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;

interface LoginFormData {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [casEnabled, setCasEnabled] = useState(true); // 从API获取CAS配置状态
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loginWithCAS, isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/admin/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const onFinish = async (values: LoginFormData) => {
    setLoading(true);
    try {
      const success = await login(values.username, values.password);
      if (success) {
        const from = (location.state as any)?.from?.pathname || '/admin/dashboard';
        navigate(from, { replace: true });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCASLogin = async () => {
    setLoading(true);
    try {
      await loginWithCAS();
    } catch (error) {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center' 
      }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: 400,
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
          borderRadius: '10px'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <img
            src="/logo.png"
            alt="NexCode"
            style={{
              width: 64,
              height: 64,
              borderRadius: 12,
              marginBottom: 16
            }}
          />
          <Title level={2} style={{ margin: 0, color: '#1a1a1a' }}>
            NexCode Admin
          </Title>
          <Text type="secondary">管理后台登录</Text>
        </div>

        {/* 检查是否有错误参数 */}
        {new URLSearchParams(location.search).get('error') && (
          <Alert
            message="认证失败"
            description="CAS认证失败，请重试或使用密码登录"
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* CAS登录 */}
        {casEnabled && (
          <>
            <Button
              type="primary"
              size="large"
              icon={<SafetyOutlined />}
              onClick={handleCASLogin}
              loading={loading}
              block
              style={{
                height: 50,
                fontSize: 16,
                marginBottom: 16,
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                border: 'none'
              }}
            >
              使用 CAS 单点登录
            </Button>
            
            <Divider>
              <Text type="secondary">或者</Text>
            </Divider>
          </>
        )}

        {/* 密码登录 */}
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              style={{ height: 50 }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              style={{ height: 50 }}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: 50,
                fontSize: 16,
                background: '#1890ff',
                border: 'none'
              }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Space direction="vertical" size="small">
            <Text type="secondary" style={{ fontSize: 12 }}>
              默认管理员账户: admin / admin
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              NexCode AIOps Platform v2.0.0
            </Text>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default Login; 