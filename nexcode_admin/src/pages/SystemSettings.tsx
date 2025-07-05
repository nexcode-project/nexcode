import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Switch,
  Space,
  Typography,
  Divider,
  message,
  Alert,
  Tabs,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  InputNumber,
} from 'antd';
import {
  SettingOutlined,
  SecurityScanOutlined,
  CloudServerOutlined,
  ApiOutlined,
  UserOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  SaveOutlined,
} from '@ant-design/icons';
import { systemAPI, type SystemSettings as SystemSettingsType } from '../services/api';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface CASConfig {
  enabled: boolean;
  server_url: string;
  service_url: string;
  logout_url: string;
  attributes_mapping: Record<string, string>;
}

interface SystemStats {
  total_users: number;
  active_users: number;
  total_commits: number;
  commits_today: number;
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
}

const SystemSettings: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState<SystemSettingsType | null>(null);
  const [casConfig, setCasConfig] = useState<CASConfig | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats>({
    total_users: 0,
    active_users: 0,
    total_commits: 0,
    commits_today: 0,
  });
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionResult, setConnectionResult] = useState<any>(null);

  const [settingsForm] = Form.useForm();
  const [casForm] = Form.useForm();

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    setLoading(true);
    try {
      const [settingsData, casConfigData, statsData] = await Promise.all([
        systemAPI.getSystemSettings().catch(() => null),
        systemAPI.getCASConfig().catch(() => casConfig),
        systemAPI.getSystemStats().catch(() => systemStats),
      ]);
      
      if (settingsData) {
        setSettings(settingsData);
        settingsForm.setFieldsValue(settingsData);
      }
      setCasConfig(casConfigData);
      setSystemStats(statsData);
      if (casConfigData) {
        casForm.setFieldsValue(casConfigData);
      }
    } catch (error) {
      message.error('加载系统配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values: SystemSettingsType) => {
    setLoading(true);
    try {
      const updatedSettings = await systemAPI.updateSystemSettings(values);
      setSettings(updatedSettings);
      message.success('设置保存成功');
    } catch (error) {
      console.error('保存系统设置失败:', error);
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionResult(null);
    try {
      const result = await systemAPI.testCASConnection();
      setConnectionResult(result);
      if (result.success) {
        message.success('CAS连接测试成功');
      } else {
        message.error('CAS连接测试失败');
      }
    } catch (error) {
      console.error('CAS connection test failed:', error);
      setConnectionResult({
        success: false,
        message: '测试连接时发生错误'
      });
      message.error('测试连接失败');
    } finally {
      setTestingConnection(false);
    }
  };

  const handleCASConfigSave = async () => {
    try {
      const values = await casForm.validateFields();
      setLoading(true);
      
      await systemAPI.updateCASConfig(values);
      setCasConfig(values);
      message.success('CAS配置保存成功');
    } catch (error) {
      message.error('保存CAS配置失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (usage?: number): "success" | "normal" | "exception" | "active" | undefined => {
    if (!usage) return undefined;
    if (usage < 50) return 'success';
    if (usage < 80) return 'normal';
    return 'exception';
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <SettingOutlined style={{ marginRight: 8 }} />
        系统设置
      </Title>

      <Tabs defaultActiveKey="overview" type="card">
        <TabPane tab={<><CloudServerOutlined />系统概览</>} key="overview">
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总用户数"
                  value={systemStats.total_users}
                  prefix={<UserOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="活跃用户"
                  value={systemStats.active_users}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总提交数"
                  value={systemStats.total_commits}
                  prefix={<ApiOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="今日提交"
                  value={systemStats.commits_today}
                  prefix={<SyncOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={8}>
              <Card title="CPU使用率" size="small">
                <Progress
                  percent={systemStats.cpu_usage || 0}
                  status={getStatusColor(systemStats.cpu_usage)}
                  format={(percent) => `${percent?.toFixed(1)}%`}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="内存使用率" size="small">
                <Progress
                  percent={systemStats.memory_usage || 0}
                  status={getStatusColor(systemStats.memory_usage)}
                  format={(percent) => `${percent?.toFixed(1)}%`}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="磁盘使用率" size="small">
                <Progress
                  percent={systemStats.disk_usage || 0}
                  status={getStatusColor(systemStats.disk_usage)}
                  format={(percent) => `${percent?.toFixed(1)}%`}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab={<><SettingOutlined />基本设置</>} key="settings">
          <Card title="系统基本设置" loading={loading}>
            <Alert
              message="系统设置说明"
              description="这些设置将影响整个系统的行为。修改后立即生效，请谨慎操作。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form
              form={settingsForm}
              layout="vertical"
              onFinish={handleSave}
              initialValues={settings || undefined}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="site_name"
                    label="站点名称"
                    rules={[{ required: true, message: '请输入站点名称' }]}
                  >
                    <Input placeholder="NexCode" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="admin_email"
                    label="管理员邮箱"
                    rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
                  >
                    <Input placeholder="admin@example.com" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="site_description"
                label="站点描述"
              >
                <Input.TextArea 
                  placeholder="智能代码提交助手"
                  rows={3}
                />
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="max_file_size"
                    label="最大文件大小 (字节)"
                    rules={[{ required: true, message: '请输入最大文件大小' }]}
                  >
                                         <InputNumber
                       min={1024}
                       max={104857600}
                       placeholder="10485760"
                       style={{ width: '100%' }}
                       formatter={(value) => `${((value || 0) / 1024 / 1024).toFixed(1)} MB`}
                                              parser={(value) => {
                         const num = parseFloat(value?.replace(' MB', '') || '0');
                          const result = Math.round(num * 1024 * 1024);
                          return Math.max(1024, Math.min(104857600, result)) as any;
                       }}
                     />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="session_timeout"
                    label="会话超时时间 (秒)"
                    rules={[{ required: true, message: '请输入会话超时时间' }]}
                  >
                                         <InputNumber
                       min={300}
                       max={86400}
                       placeholder="1800"
                       style={{ width: '100%' }}
                       formatter={(value) => `${Math.round((value || 0) / 60)} 分钟`}
                       parser={(value) => {
                         const num = parseFloat(value?.replace(' 分钟', '') || '0');
                         const result = Math.round(num * 60);
                         return Math.max(300, Math.min(86400, result)) as any;
                       }}
                     />
                  </Form.Item>
                </Col>
              </Row>

              <Divider orientation="left">用户注册设置</Divider>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="enable_registration"
                    label="允许用户注册"
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="启用"
                      unCheckedChildren="禁用"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="enable_email_verification"
                    label="邮箱验证"
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="启用"
                      unCheckedChildren="禁用"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider orientation="left">SMTP邮件配置</Divider>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="smtp_host"
                    label="SMTP服务器"
                  >
                    <Input placeholder="smtp.gmail.com" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="smtp_port"
                    label="SMTP端口"
                    rules={[{ required: true, message: '请输入SMTP端口' }]}
                  >
                    <InputNumber
                      min={1}
                      max={65535}
                      placeholder="587"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="smtp_username"
                    label="SMTP用户名"
                  >
                    <Input placeholder="username@example.com" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="smtp_password"
                    label="SMTP密码"
                  >
                    <Input.Password placeholder="邮箱密码或应用密码" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="smtp_use_tls"
                label="使用TLS加密"
                valuePropName="checked"
              >
                <Switch
                  checkedChildren="启用"
                  unCheckedChildren="禁用"
                />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    icon={<SaveOutlined />}
                  >
                    保存设置
                  </Button>
                  <Button
                    onClick={() => settingsForm.resetFields()}
                    disabled={loading}
                  >
                    重置
                  </Button>
                  <Button
                    icon={<SyncOutlined />}
                    onClick={loadSystemData}
                    disabled={loading}
                  >
                    刷新
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane tab={<><SecurityScanOutlined />CAS认证</>} key="cas">
          <Card title="CAS认证配置" loading={loading}>
            <Alert
              message="CAS配置说明"
              description="配置CAS单点登录，支持Web端和Admin端统一认证。修改配置后需要重启服务才能生效。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form
              form={casForm}
              layout="vertical"
              initialValues={casConfig || undefined}
              onFinish={handleCASConfigSave}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="enabled"
                    label="启用CAS认证"
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="启用"
                      unCheckedChildren="禁用"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <div style={{ textAlign: 'right', paddingTop: 30 }}>
                    <Space>
                      <Button
                        icon={<SyncOutlined />}
                        onClick={loadSystemData}
                        disabled={loading}
                      >
                        刷新配置
                      </Button>
                      <Button
                        type="primary"
                        icon={<CheckCircleOutlined />}
                        onClick={handleTestConnection}
                        loading={testingConnection}
                        disabled={!casForm.getFieldValue('enabled')}
                      >
                        测试连接
                      </Button>
                    </Space>
                  </div>
                </Col>
              </Row>

              <Divider />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="server_url"
                    label="CAS服务器地址"
                    rules={[
                      {
                        required: true,
                        message: '请输入CAS服务器地址',
                      },
                      {
                        type: 'url',
                        message: '请输入有效的URL地址',
                      },
                    ]}
                  >
                    <Input
                      placeholder="https://cas.example.com"
                      prefix={<CloudServerOutlined />}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="service_url"
                    label="服务回调地址"
                    rules={[
                      {
                        required: true,
                        message: '请输入服务回调地址',
                      },
                    ]}
                  >
                    <Input
                      placeholder="http://localhost:8000/v1/auth/cas/callback"
                      prefix={<ApiOutlined />}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="logout_url"
                label="登出地址"
              >
                <Input
                  placeholder="https://cas.example.com/logout"
                  prefix={<ExclamationCircleOutlined />}
                />
              </Form.Item>

              <Divider orientation="left">属性映射配置</Divider>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name={['attributes_mapping', 'username']}
                    label="用户名字段"
                    rules={[{ required: true, message: '请输入用户名字段' }]}
                  >
                    <Input placeholder="uid" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['attributes_mapping', 'email']}
                    label="邮箱字段"
                    rules={[{ required: true, message: '请输入邮箱字段' }]}
                  >
                    <Input placeholder="mail" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['attributes_mapping', 'full_name']}
                    label="姓名字段"
                    rules={[{ required: true, message: '请输入姓名字段' }]}
                  >
                    <Input placeholder="displayName" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    icon={<SettingOutlined />}
                  >
                    保存配置
                  </Button>
                  <Button
                    onClick={() => casForm.resetFields()}
                    disabled={loading}
                  >
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>

            {/* 连接测试结果 */}
            {connectionResult && (
              <Card
                title="连接测试结果"
                style={{ marginTop: 16 }}
                size="small"
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>状态: </Text>
                    <Tag color={connectionResult.success ? 'success' : 'error'}>
                      {connectionResult.success ? '成功' : '失败'}
                    </Tag>
                  </div>
                  <div>
                    <Text strong>消息: </Text>
                    <Text>{connectionResult.message}</Text>
                  </div>
                  {connectionResult.server_url && (
                    <div>
                      <Text strong>服务器地址: </Text>
                      <Text code>{connectionResult.server_url}</Text>
                    </div>
                  )}
                  {connectionResult.status_code && (
                    <div>
                      <Text strong>HTTP状态码: </Text>
                      <Tag>{connectionResult.status_code}</Tag>
                    </div>
                  )}
                  {connectionResult.response_time && (
                    <div>
                      <Text strong>响应时间: </Text>
                      <Text>{connectionResult.response_time}</Text>
                    </div>
                  )}
                  {connectionResult.error && (
                    <Alert
                      message="错误详情"
                      description={connectionResult.error}
                      type="error"
                    />
                  )}
                </Space>
              </Card>
            )}
          </Card>
        </TabPane>

        <TabPane tab={<><ApiOutlined />Web端配置</>} key="web">
          <Card title="Web端CAS配置">
            <Alert
              message="Web端配置"
              description="配置Web应用的CAS单点登录，包括前端重定向地址和登录流程。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />
            
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Web端登录地址">
                    <Input
                      value={`${window.location.origin}/login`}
                      readOnly
                      addonBefore="登录页面"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Web端回调地址">
                    <Input
                      value={`${window.location.origin}/cas/callback`}                     
                      readOnly
                      addonBefore="CAS回调"/>
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item label="CAS登录流程">
                <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                  <ol>
                    <li>用户访问Web应用</li>
                    <li>点击"CAS登录"按钮</li>
                    <li>重定向到CAS服务器进行认证</li>
                    <li>认证成功后回调到Web应用</li>
                    <li>Web应用验证ticket并创建会话</li>
                  </ol>
                </div>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane tab={<><UserOutlined />Admin端配置</>} key="admin">
          <Card title="Admin端CAS配置">
            <Alert
              message="Admin端配置"
              description="配置管理后台的CAS单点登录，确保管理员可以通过CAS进行安全认证。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />
            
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Admin端登录地址">
                    <Input
                      value={`${window.location.origin}/admin/login`}
                      readOnly
                      addonBefore="管理登录"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Admin端回调地址">
                    <Input
                      value={`${window.location.origin}/admin/cas/callback`}
                      readOnly
                      addonBefore="管理回调"
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item label="权限要求">
                <Alert
                  message="管理员权限"
                  description="通过CAS登录的用户需要具有超级用户权限才能访问管理后台。系统会自动检查用户的is_superuser字段。"
                  type="warning"
                  showIcon
                />
              </Form.Item>
              
              <Form.Item label="安全配置">
                <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                  <ul>
                    <li><strong>会话超时:</strong> 24小时</li>
                    <li><strong>强制HTTPS:</strong> 生产环境启用</li>
                    <li><strong>Cookie安全:</strong> HttpOnly, SameSite</li>
                    <li><strong>权限验证:</strong> 每个请求都验证超级用户权限</li>
                  </ul>
                </div>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default SystemSettings;
