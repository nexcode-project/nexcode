import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Button,
  Switch,
  Space,
  Typography,
  Divider,
  message,
  Alert,
  Spin,
  Select,
} from 'antd';
import {
  SettingOutlined,
  ExperimentOutlined,
  SaveOutlined,
  ReloadOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { systemAPI } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface SystemSettings {
  site_name: string;
  site_description: string;
  admin_email: string;
  max_file_size: number;
  session_timeout: number;
  enable_registration: boolean;
  enable_email_verification: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_use_tls: boolean;
}

interface CASConfig {
  enabled: boolean;
  server_url: string;
  service_url: string;
  logout_url: string;
  attributes_mapping: Record<string, string>;
}

const SystemSettings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [casConfig, setCasConfig] = useState<CASConfig | null>(null);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [settings, setSettings] = useState<SystemSettings>({
    site_name: 'NexCode Admin',
    site_description: 'AI驱动的开发工具管理平台',
    admin_email: 'admin@nexcode.local',
    max_file_size: 10485760, // Assuming a default value
    session_timeout: 24,
    enable_registration: false,
    enable_email_verification: false,
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_use_tls: true,
  });

  useEffect(() => {
    loadCASConfig();
  }, []);

  const loadCASConfig = async () => {
    setLoading(true);
    try {
      const config = await systemAPI.getCASConfig();
      setCasConfig(config);
      form.setFieldsValue(config);
    } catch (error) {
      console.error('Failed to load CAS config:', error);
      message.error('加载CAS配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values: SystemSettings) => {
    setLoading(true);
    try {
      // 模拟保存API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSettings(values);
      message.success('设置保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.setFieldsValue(settings);
    message.info('已重置为当前保存的设置');
  };

  const handleTestEmail = async () => {
    try {
      // 模拟邮件测试
      message.loading('正在发送测试邮件...', 2);
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success('测试邮件发送成功');
    } catch (error) {
      message.error('邮件发送失败');
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await systemAPI.testCASConnection();
      setTestResult(result);
      if (result.success) {
        message.success('CAS连接测试成功');
      } else {
        message.error('CAS连接测试失败');
      }
    } catch (error) {
      console.error('CAS connection test failed:', error);
      setTestResult({
        success: false,
        message: '测试连接时发生错误'
      });
      message.error('测试连接失败');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div>
      <Title level={2}>
        <SettingOutlined /> 系统设置
      </Title>
      
      <Alert
        message="重要提醒"
        description="修改系统设置可能会影响系统运行，请谨慎操作。某些设置需要重启服务才能生效。"
        type="warning"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        initialValues={settings}
        onFinish={handleSave}
      >
        {/* 基础设置 */}
        <Card title="基础设置" style={{ marginBottom: 16 }}>
          <Form.Item
            name="site_name"
            label="站点名称"
            rules={[{ required: true, message: '请输入站点名称' }]}
          >
            <Input placeholder="输入站点名称" />
          </Form.Item>

          <Form.Item
            name="site_description"
            label="站点描述"
          >
            <TextArea placeholder="输入站点描述" rows={3} />
          </Form.Item>

          <Form.Item
            name="admin_email"
            label="管理员邮箱"
            rules={[
              { required: true, message: '请输入管理员邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="输入管理员邮箱" />
          </Form.Item>
        </Card>

        {/* API设置 */}
        <Card title="API设置" style={{ marginBottom: 16 }}>
          <Form.Item
            name="max_file_size"
            label="最大文件大小（字节）"
            rules={[{ required: true, message: '请输入最大文件大小' }]}
          >
            <InputNumber min={1048576} max={104857600} placeholder="10485760" style={{ width: '100%' }} />
          </Form.Item>
        </Card>

        {/* 安全设置 */}
        <Card title="安全设置" style={{ marginBottom: 16 }}>
          <Form.Item name="enable_registration" label="允许用户注册" valuePropName="checked">
            <Switch checkedChildren="允许" unCheckedChildren="禁止" />
          </Form.Item>

          <Form.Item name="enable_email_verification" label="启用邮箱验证" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Card>

        {/* 邮件设置 */}
        <Card title="邮件设置" style={{ marginBottom: 24 }}>
          <Form.Item
            name="smtp_host"
            label="SMTP服务器"
          >
            <Input placeholder="smtp.example.com" />
          </Form.Item>

          <Form.Item
            name="smtp_port"
            label="SMTP端口"
          >
            <InputNumber min={1} max={65535} placeholder="587" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="smtp_username"
            label="SMTP用户名"
          >
            <Input placeholder="输入SMTP用户名" />
          </Form.Item>

          <Form.Item
            name="smtp_password"
            label="SMTP密码"
          >
            <Input.Password placeholder="输入SMTP密码" />
          </Form.Item>

          <Form.Item name="smtp_use_tls" label="使用TLS加密" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item>
            <Button type="dashed" onClick={handleTestEmail}>
              发送测试邮件
            </Button>
          </Form.Item>
        </Card>

        {/* 操作按钮 */}
        <Card>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
            >
              保存设置
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
            >
              重置
            </Button>
          </Space>
        </Card>
      </Form>

      <Card title="CAS单点登录配置" style={{ marginBottom: 24 }}>
        <Spin spinning={loading}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            initialValues={{
              enabled: false,
              server_url: '',
              service_url: '',
              logout_url: '',
              attributes_mapping: {
                username: 'uid',
                email: 'mail',
                full_name: 'displayName',
              },
            }}
          >
            <Form.Item
              name="enabled"
              label="启用CAS认证"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              name="server_url"
              label="CAS服务器URL"
              rules={[
                { required: true, message: '请输入CAS服务器URL' },
                { type: 'url', message: '请输入有效的URL' },
              ]}
            >
              <Input placeholder="https://cas.example.com" />
            </Form.Item>

            <Form.Item
              name="service_url"
              label="服务回调URL"
              rules={[
                { required: true, message: '请输入服务回调URL' },
                { type: 'url', message: '请输入有效的URL' },
              ]}
            >
              <Input placeholder="http://localhost:8000/auth/cas/callback" />
            </Form.Item>

            <Form.Item
              name="logout_url"
              label="登出URL"
            >
              <Input placeholder="https://cas.example.com/logout" />
            </Form.Item>

            <Divider>属性映射</Divider>
            <Paragraph type="secondary">
              配置CAS返回的用户属性与系统字段的映射关系
            </Paragraph>

            <Form.Item
              name={['attributes_mapping', 'username']}
              label="用户名字段"
              rules={[{ required: true, message: '请输入用户名字段映射' }]}
            >
              <Input placeholder="uid" />
            </Form.Item>

            <Form.Item
              name={['attributes_mapping', 'email']}
              label="邮箱字段"
              rules={[{ required: true, message: '请输入邮箱字段映射' }]}
            >
              <Input placeholder="mail" />
            </Form.Item>

            <Form.Item
              name={['attributes_mapping', 'full_name']}
              label="姓名字段"
            >
              <Input placeholder="displayName" />
            </Form.Item>

            <Divider />

            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={loading}
              >
                保存配置
              </Button>

              <Button
                icon={testing ? <LoadingOutlined /> : <ExperimentOutlined />}
                loading={testing}
                onClick={handleTestConnection}
                disabled={!casConfig?.server_url}
              >
                测试连接
              </Button>
            </Space>

            {testResult && (
              <Alert
                style={{ marginTop: 16 }}
                type={testResult.success ? 'success' : 'error'}
                message={testResult.success ? '连接测试成功' : '连接测试失败'}
                description={testResult.message}
                showIcon
              />
            )}
          </Form>
        </Spin>
      </Card>

      <Card title="聊天服务配置">
        <Paragraph type="secondary">
          配置与聊天服务的集成，确保CAS认证后能正确访问聊天功能
        </Paragraph>

        <Form layout="vertical">
          <Form.Item
            label="聊天服务URL"
            name="chat_service_url"
          >
            <Input 
              placeholder="http://localhost:3000" 
              defaultValue="http://localhost:3000"
            />
          </Form.Item>

          <Form.Item
            label="聊天服务CAS回调"
            name="chat_cas_callback"
          >
            <Input 
              placeholder="http://localhost:3000/auth/cas/callback" 
              defaultValue="http://localhost:3000/auth/cas/callback"
            />
          </Form.Item>

          <Form.Item>
            <Alert
              type="info"
              message="配置说明"
              description={
                <div>
                  <p>• 聊天服务URL: NexCode Web聊天界面的访问地址</p>
                  <p>• CAS回调地址: 用户CAS认证成功后的跳转地址</p>
                  <p>• 确保两个服务的CAS配置保持一致</p>
                </div>
              }
              showIcon
            />
          </Form.Item>

          <Button type="primary" icon={<SaveOutlined />}>
            保存聊天服务配置
          </Button>
        </Form>
      </Card>
    </div>
  );
};

export default SystemSettings; 