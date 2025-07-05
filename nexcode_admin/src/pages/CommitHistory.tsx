import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Tag,
  Space,
  Typography,
  Input,
  DatePicker,
  Select,
  Button,
  Tooltip,
  message,
  Spin,
  Modal,
  Form,
  Input as AntInput,
  Rate,
  Popconfirm,
  Drawer,
} from 'antd';
import {
  SearchOutlined,
  BranchesOutlined,
  UserOutlined,
  CalendarOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import { commitsAPI } from '../services/api';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Search } = Input;
const { RangePicker } = DatePicker;

interface CommitRecord {
  id: number;
  user_id: number;
  username: string;
  repository_name: string | null;
  repository_url?: string;
  branch_name: string | null;
  commit_hash?: string;
  ai_generated_message?: string;
  final_commit_message: string;
  commit_style: string;
  lines_added: number;
  lines_deleted: number;
  files_changed: string[] | null;
  ai_model_used?: string;
  generation_time_ms?: number;
  user_rating?: number;
  status: string;
  created_at: string;
  committed_at?: string;
  user_feedback?: string;
  diff_content?: string;
}

const CommitHistory: React.FC = () => {
  const [commits, setCommits] = useState<CommitRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedRepository, setSelectedRepository] = useState<string>();
  const [selectedUser, setSelectedUser] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });

  // 新增状态
  const [diffDrawerVisible, setDiffDrawerVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedCommit, setSelectedCommit] = useState<CommitRecord | null>(null);
  const [editForm] = Form.useForm();

  useEffect(() => {
    loadCommits();
  }, [pagination.current, pagination.pageSize]);

  const loadCommits = async () => {
    setLoading(true);
    try {
      const params: any = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      };

      if (selectedRepository) {
        params.repository_name = selectedRepository;
      }
      if (selectedUser) {
        params.username = selectedUser;
      }
      if (dateRange) {
        params.start_date = dateRange[0].toISOString();
        params.end_date = dateRange[1].toISOString();
      }

      const response = await commitsAPI.getAllCommits(params);
      setCommits(response.commits);
      setPagination(prev => ({
        ...prev,
        total: response.total,
      }));
    } catch (error) {
      console.error('Failed to load commits:', error);
      message.error('加载提交记录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }));
    loadCommits();
  };

  const handleReset = () => {
    setSearchText('');
    setSelectedRepository(undefined);
    setSelectedUser(undefined);
    setDateRange(null);
    setPagination(prev => ({ ...prev, current: 1 }));
    setTimeout(loadCommits, 100);
  };

  const getQualityColor = (quality?: number) => {
    if (!quality) return 'default';
    if (quality >= 4) return 'green';
    if (quality >= 3) return 'orange';
    return 'red';
  };

  const getQualityText = (quality?: number) => {
    if (!quality) return '未评分';
    if (quality >= 4) return '优秀';
    if (quality >= 3) return '良好';
    return '需改进';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'committed': return 'green';
      case 'draft': return 'blue';
      case 'failed': return 'red';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'committed': return '已提交';
      case 'draft': return '草稿';
      case 'failed': return '失败';
      default: return status;
    }
  };

  // 查看diff详情
  const handleViewDiff = (commit: CommitRecord) => {
    setSelectedCommit(commit);
    setDiffDrawerVisible(true);
  };

  // 编辑commit信息
  const handleEditCommit = (commit: CommitRecord) => {
    setSelectedCommit(commit);
    editForm.setFieldsValue({
      final_commit_message: commit.final_commit_message,
      user_rating: commit.user_rating,
      user_feedback: commit.user_feedback,
      status: commit.status,
    });
    setEditModalVisible(true);
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    try {
      const values = await editForm.validateFields();
      if (!selectedCommit) return;

      // 调用API更新commit信息
      await commitsAPI.updateCommit(selectedCommit.id, values);
      message.success('提交信息更新成功');
      setEditModalVisible(false);
      loadCommits(); // 重新加载数据
    } catch (error) {
      message.error('更新失败');
    }
  };

  // 删除commit
  const handleDeleteCommit = async (commitId: number) => {
    try {
      await commitsAPI.deleteCommit(commitId);
      message.success('提交记录删除成功');
      loadCommits(); // 重新加载数据
    } catch (error) {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (text: string) => (
        <Space>
          <UserOutlined />
          {text}
        </Space>
      ),
    },
    {
      title: '仓库',
      dataIndex: 'repository_name',
      key: 'repository_name',
      width: 200,
      render: (text: string | null, record: CommitRecord) => (
        <div>
          <div>
            <BranchesOutlined style={{ marginRight: 4 }} />
            {text || '未知仓库'}
          </div>
          {record.branch_name && (
            <div style={{ fontSize: '12px', color: '#999' }}>
              分支: {record.branch_name}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '提交信息',
      dataIndex: 'final_commit_message',
      key: 'final_commit_message',
      ellipsis: {
        showTitle: false,
      },
      render: (text: string, record: CommitRecord) => (
        <Tooltip title={text}>
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{text}</div>
            <div style={{ fontSize: '12px', color: '#999' }}>
              {record.commit_hash && (
                <>
                  <code>{record.commit_hash.substring(0, 8)}</code>
                  <span style={{ margin: '0 8px' }}>•</span>
                </>
              )}
              {(record.files_changed || []).length} 个文件
              <span style={{ margin: '0 8px' }}>•</span>
              <span style={{ color: '#52c41a' }}>+{record.lines_added || 0}</span>
              <span style={{ margin: '0 4px' }}>/</span>
              <span style={{ color: '#ff4d4f' }}>-{record.lines_deleted || 0}</span>
            </div>
          </div>
        </Tooltip>
      ),
    },
    {
      title: '风格',
      dataIndex: 'commit_style',
      key: 'commit_style',
      width: 80,
      render: (style: string) => (
        <Tag color={style === 'conventional' ? 'blue' : 'green'}>
          {style === 'conventional' ? '规范' : style}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '质量评分',
      dataIndex: 'user_rating',
      key: 'user_rating',
      width: 100,
      render: (rating?: number) => (
        <Tag color={getQualityColor(rating)}>
          {rating ? `${rating}/5 - ${getQualityText(rating)}` : '未评分'}
        </Tag>
      ),
    },
    {
      title: 'AI模型',
      dataIndex: 'ai_model_used',
      key: 'ai_model_used',
      width: 120,
      render: (model?: string) => model || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => (
        <Space>
          <CalendarOutlined />
          {dayjs(date).format('YYYY-MM-DD HH:mm:ss')}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: CommitRecord) => (
        <Space>
          <Tooltip title="查看Diff">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDiff(record)}
              size="small"
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditCommit(record)}
              size="small"
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这条提交记录吗？"
              onConfirm={() => handleDeleteCommit(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                icon={<DeleteOutlined />}
                danger
                size="small"
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  const filteredCommits = commits.filter(commit => {
    const matchesSearch = !searchText || 
      commit.final_commit_message.toLowerCase().includes(searchText.toLowerCase()) ||
      commit.username.toLowerCase().includes(searchText.toLowerCase()) ||
      (commit.repository_name && commit.repository_name.toLowerCase().includes(searchText.toLowerCase())) ||
      (commit.branch_name && commit.branch_name.toLowerCase().includes(searchText.toLowerCase()));

    return matchesSearch;
  });

  const repositories = [...new Set(commits.map(c => c.repository_name).filter(Boolean))];
  const users = [...new Set(commits.map(c => c.username).filter(Boolean))];

  const handleTableChange = (page: number, pageSize?: number) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize || prev.pageSize,
    }));
  };

  return (
    <div>
      <Title level={2}>提交历史</Title>
      
      {/* 筛选器 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Search
            placeholder="搜索提交信息、用户名或仓库名"
            allowClear
            style={{ width: 300 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={handleSearch}
          />
          
          <Select
            placeholder="选择仓库"
            allowClear
            style={{ width: 200 }}
            value={selectedRepository}
            onChange={setSelectedRepository}
          >
            {repositories.map(repo => (
              <Select.Option key={repo} value={repo}>
                {repo}
              </Select.Option>
            ))}
          </Select>

          <Select
            placeholder="选择用户"
            allowClear
            style={{ width: 150 }}
            value={selectedUser}
            onChange={setSelectedUser}
          >
            {users.map(user => (
              <Select.Option key={user} value={user}>
                {user}
              </Select.Option>
            ))}
          </Select>
          
          <RangePicker 
            placeholder={['开始日期', '结束日期']} 
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
          />
          
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            搜索
          </Button>

          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </Space>
      </Card>

      {/* 提交记录表格 */}
      <Card>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={filteredCommits}
            rowKey="id"
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              onChange: handleTableChange,
              onShowSizeChange: (current, size) => handleTableChange(current, size),
            }}
            scroll={{ x: 1200 }}
          />
        </Spin>
      </Card>

      {/* Diff查看抽屉 */}
      <Drawer
        title={
          <Space>
            <CodeOutlined />
            Diff 详情
            {selectedCommit && (
              <Tag color="blue">
                {selectedCommit.commit_hash?.substring(0, 8)}
              </Tag>
            )}
          </Space>
        }
        placement="right"
        size="large"
        onClose={() => setDiffDrawerVisible(false)}
        open={diffDrawerVisible}
        width="60%"
      >
        {selectedCommit && (
          <div>
            <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div><strong>仓库:</strong> {selectedCommit.repository_name || '未知'}</div>
                <div><strong>分支:</strong> {selectedCommit.branch_name || '未知'}</div>
                <div><strong>提交哈希:</strong> <code>{selectedCommit.commit_hash || '无'}</code></div>
                <div><strong>提交消息:</strong> {selectedCommit.final_commit_message}</div>
                <div><strong>用户:</strong> {selectedCommit.username}</div>
                <div><strong>状态:</strong> 
                  <Tag color={getStatusColor(selectedCommit.status)} style={{ marginLeft: 8 }}>
                    {getStatusText(selectedCommit.status)}
                  </Tag>
                </div>
                <div><strong>创建时间:</strong> {dayjs(selectedCommit.created_at).format('YYYY-MM-DD HH:mm:ss')}</div>
              </Space>
            </Card>
            
            <Card title="Diff 内容" size="small">
              <pre style={{ 
                background: '#f6f8fa', 
                padding: '16px', 
                borderRadius: '6px',
                overflow: 'auto',
                maxHeight: '60vh',
                fontSize: '13px',
                lineHeight: '1.45',
                fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace'
              }}>
                {selectedCommit.diff_content || '无diff内容'}
              </pre>
            </Card>
          </div>
        )}
      </Drawer>

      {/* 编辑Modal */}
      <Modal
        title="编辑提交信息"
        open={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={() => setEditModalVisible(false)}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={editForm}
          layout="vertical"
        >
          <Form.Item
            label="提交消息"
            name="final_commit_message"
            rules={[{ required: true, message: '请输入提交消息' }]}
          >
            <AntInput.TextArea rows={3} />
          </Form.Item>
          
          <Form.Item
            label="状态"
            name="status"
          >
            <Select>
              <Select.Option value="draft">草稿</Select.Option>
              <Select.Option value="committed">已提交</Select.Option>
              <Select.Option value="failed">失败</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="质量评分"
            name="user_rating"
          >
            <Rate />
          </Form.Item>
          
          <Form.Item
            label="用户反馈"
            name="user_feedback"
          >
            <AntInput.TextArea rows={3} placeholder="可选的用户反馈..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CommitHistory; 