import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Switch,
  message,
  Popconfirm,
  Typography,
  Avatar,
  Drawer,
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  KeyOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { usersAPI, type User, type APIKey as APIKeyType } from '../services/api';

const { Title, Text } = Typography;

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [apiKeysVisible, setApiKeysVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedUserKeys, setSelectedUserKeys] = useState<APIKeyType[]>([]);
  const [apiKeyLoading, setApiKeyLoading] = useState(false);
  const [form] = Form.useForm();
  const [apiKeyForm] = Form.useForm();
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [apiKeyModalVisible, setApiKeyModalVisible] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    fetchUsers();
  }, [pagination.current, pagination.pageSize, searchText]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: searchText || undefined,
      };
      const apiUsers = await usersAPI.getAllUsers(params.skip, params.limit);
      const enriched: User[] = await Promise.all(apiUsers.map(async (u: User) => {
        let apiKeysCount = 0;
        try {
          const keys = await usersAPI.getUserAPIKeys(u.id);
          apiKeysCount = keys.length;
        } catch (e) {
          // ignore if fails
        }
        return { ...u, updated_at: u.updated_at, api_keys_count: apiKeysCount };
      }));
      setUsers(enriched);
      setPagination((prev) => ({ ...prev, total: apiUsers.length }));
    } catch (error) {
      console.error('加载用户失败:', error);
      message.error('加载用户失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      is_active: user.is_active,
      is_superuser: user.is_superuser,
    });
    setModalVisible(true);
  };

  const handleDelete = async (userId: number) => {
    try {
      await usersAPI.deleteUser(userId);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingUser) {
        await usersAPI.updateUser(editingUser.id, values);
        message.success('用户更新成功');
      } else {
        await usersAPI.createUser(values);
        message.success('用户创建成功');
      }
      setModalVisible(false);
      fetchUsers();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleViewAPIKeys = async (user: User) => {
    setSelectedUser(user);
    setApiKeysVisible(true);
    setApiKeyLoading(true);
    try {
      const keys = await usersAPI.getUserAPIKeys(user.id);
      setSelectedUserKeys(keys || []);
    } catch (error) {
      message.error('加载API密钥失败');
    } finally {
      setApiKeyLoading(false);
    }
  };

  const handleCreateApiKey = async (values: { name: string }) => {
    if (!selectedUser) return;
    setApiKeyLoading(true);
    try {
      const result = await usersAPI.createAPIKey(selectedUser.id, values.name);
      message.success('API密钥创建成功');
      setNewApiKey(result.key); // The raw key is in result.key
      setApiKeyModalVisible(true);
      await handleViewAPIKeys(selectedUser); // Reload list
    } catch (error) {
      message.error('创建API密钥失败');
    } finally {
      setApiKeyLoading(false);
      apiKeyForm.resetFields();
    }
  };

  const handleDeleteApiKey = async (apiKeyId: number) => {
    if (!selectedUser) return;
    setApiKeyLoading(true);
    try {
      await usersAPI.deleteAPIKey(selectedUser.id, apiKeyId);
      message.success('API密钥删除成功');
      await handleViewAPIKeys(selectedUser); // Reload list
    } catch (error) {
      message.error('删除API密钥失败');
    } finally {
      setApiKeyLoading(false);
    }
  };

  const columns = [
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 'bold' }}>{text}</div>
            <div style={{ color: '#999', fontSize: '12px' }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '激活' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '权限',
      dataIndex: 'is_superuser',
      key: 'is_superuser',
      render: (isSuperuser: boolean) => (
        <Tag color={isSuperuser ? 'purple' : 'blue'}>
          {isSuperuser ? '管理员' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: 'API密钥',
      dataIndex: 'api_keys_count',
      key: 'api_keys_count',
      render: (count: number) => count || 0,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString('zh-CN'),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date?: string) => 
        date ? new Date(date).toLocaleDateString('zh-CN') : '从未登录',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            icon={<KeyOutlined />}
            onClick={() => handleViewAPIKeys(record)}
          >
            API密钥
          </Button>
          <Popconfirm
            title="确定删除此用户吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const apiKeyColumns = [
    {
      title: '密钥名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '密钥前缀',
      dataIndex: 'key_prefix',
      key: 'key_prefix',
      render: (text: string) => <code>{text}</code>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '激活' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
    },
    {
      title: '最后使用',
      dataIndex: 'last_used',
      key: 'last_used',
      render: (date?: string) => 
        date ? new Date(date).toLocaleDateString('zh-CN') : '从未使用',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: APIKeyType) => (
        <Popconfirm
          title="确定要删除这个API密钥吗？"
          onConfirm={() => handleDeleteApiKey(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="link" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>用户管理</Title>
        <Space>
          <Input.Search
            placeholder="搜索用户名/邮箱"
            allowClear
            enterButton
            onSearch={(value) => {
              setSearchText(value.trim());
              setPagination((prev) => ({ ...prev, current: 1 }));
            }}
            style={{ width: 240 }}
          />
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          添加用户
        </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 用户编辑/创建模态框 */}
      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="输入用户名" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="输入邮箱地址" />
          </Form.Item>

          {/* 仅在添加模式显示密码输入 */}
          {!editingUser && (
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入初始密码' }]}
            >
              <Input.Password placeholder="输入初始密码" />
            </Form.Item>
          )}

          <Form.Item name="is_active" label="账户状态" valuePropName="checked">
            <Switch checkedChildren="激活" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item name="is_superuser" label="管理员权限" valuePropName="checked">
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingUser ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* API密钥抽屉 */}
      <Drawer
        title={`${selectedUser?.username} 的 API密钥管理`}
        placement="right"
        width={600}
        open={apiKeysVisible}
        onClose={() => setApiKeysVisible(false)}
      >
        <Form form={apiKeyForm} onFinish={handleCreateApiKey} layout="inline" style={{ marginBottom: 16 }}>
          <Form.Item
            name="name"
            rules={[{ required: true, message: '请输入密钥名称' }]}
            style={{ flex: 1 }}
          >
            <Input placeholder="为新密钥命名" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={apiKeyLoading}>
              创建新密钥
            </Button>
          </Form.Item>
        </Form>
        <Table
          columns={apiKeyColumns}
          dataSource={selectedUserKeys}
          rowKey="id"
          loading={apiKeyLoading}
          size="small"
          pagination={false}
        />
      </Drawer>

      {/* 显示新创建的API Key Modal */}
      <Modal
        title="API密钥创建成功"
        open={apiKeyModalVisible}
        onOk={() => setApiKeyModalVisible(false)}
        onCancel={() => setApiKeyModalVisible(false)}
        footer={[
          <Button key="ok" type="primary" onClick={() => setApiKeyModalVisible(false)}>
            好的
          </Button>,
        ]}
      >
        <p>请复制并妥善保存您的新API密钥，此密钥仅显示一次：</p>
        <Text code copyable style={{ fontSize: '16px' }}>
          {newApiKey}
        </Text>
      </Modal>
    </div>
  );
};

export default UserManagement; 