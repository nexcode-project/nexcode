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
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  last_login?: string;
  api_keys_count: number;
}

interface APIKey {
  id: number;
  key_name: string;
  key_prefix: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  last_used?: string;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [apiKeysVisible, setApiKeysVisible] = useState(false);
  const [selectedUserKeys, setSelectedUserKeys] = useState<APIKey[]>([]);
  const [form] = Form.useForm();

  // 模拟数据加载
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    // 模拟API调用
    setTimeout(() => {
      const mockUsers: User[] = [
        {
          id: 1,
          username: 'admin',
          email: 'admin@nexcode.local',
          is_active: true,
          is_superuser: true,
          created_at: '2024-01-15T10:30:00Z',
          last_login: '2024-01-20T15:22:00Z',
          api_keys_count: 2,
        },
        {
          id: 2,
          username: 'developer1',
          email: 'dev1@company.com',
          is_active: true,
          is_superuser: false,
          created_at: '2024-01-16T09:15:00Z',
          last_login: '2024-01-19T14:30:00Z',
          api_keys_count: 1,
        },
        {
          id: 3,
          username: 'testuser',
          email: 'test@company.com',
          is_active: false,
          is_superuser: false,
          created_at: '2024-01-17T11:45:00Z',
          api_keys_count: 0,
        },
      ];
      setUsers(mockUsers);
      setLoading(false);
    }, 1000);
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
      // 模拟删除API调用
      setUsers(users.filter(user => user.id !== userId));
      message.success('用户删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingUser) {
        // 更新用户
        const updatedUsers = users.map(user =>
          user.id === editingUser.id ? { ...user, ...values } : user
        );
        setUsers(updatedUsers);
        message.success('用户更新成功');
      } else {
        // 创建新用户
        const newUser: User = {
          id: Date.now(),
          ...values,
          created_at: new Date().toISOString(),
          api_keys_count: 0,
        };
        setUsers([...users, newUser]);
        message.success('用户创建成功');
      }
      setModalVisible(false);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleViewAPIKeys = (user: User) => {
    // 模拟API密钥数据
    const mockAPIKeys: APIKey[] = [
      {
        id: 1,
        key_name: 'Development Key',
        key_prefix: 'nex_dev_****',
        is_active: true,
        usage_count: 1250,
        created_at: '2024-01-15T10:30:00Z',
        last_used: '2024-01-20T15:22:00Z',
      },
      {
        id: 2,
        key_name: 'Production Key',
        key_prefix: 'nex_prod_****',
        is_active: false,
        usage_count: 89,
        created_at: '2024-01-16T09:15:00Z',
        last_used: '2024-01-18T11:30:00Z',
      },
    ];
    setSelectedUserKeys(mockAPIKeys);
    setApiKeysVisible(true);
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
      dataIndex: 'key_name',
      key: 'key_name',
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
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>用户管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          添加用户
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            total: users.length,
            pageSize: 10,
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
        title="API密钥管理"
        placement="right"
        width={800}
        open={apiKeysVisible}
        onClose={() => setApiKeysVisible(false)}
      >
        <Table
          columns={apiKeyColumns}
          dataSource={selectedUserKeys}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Drawer>
    </div>
  );
};

export default UserManagement; 