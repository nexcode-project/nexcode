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
} from 'antd';
import {
  SearchOutlined,
  BranchesOutlined,
  UserOutlined,
  CalendarOutlined,
  ReloadOutlined,
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
  repository_name: string;
  repository_url?: string;
  branch_name: string;
  commit_hash?: string;
  ai_generated_message?: string;
  final_commit_message: string;
  commit_style: string;
  lines_added: number;
  lines_deleted: number;
  files_changed: string[];
  ai_model_used?: string;
  generation_time_ms?: number;
  user_rating?: number;
  status: string;
  created_at: string;
  committed_at?: string;
}

const CommitHistory: React.FC = () => {
  const [commits, setCommits] = useState<CommitRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedRepository, setSelectedRepository] = useState<string>();
  const [selectedUser, setSelectedUser] = useState<string>();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });

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
      render: (text: string, record: CommitRecord) => (
        <div>
          <div>
            <BranchesOutlined style={{ marginRight: 4 }} />
            {text}
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
              {record.files_changed.length} 个文件
              <span style={{ margin: '0 8px' }}>•</span>
              <span style={{ color: '#52c41a' }}>+{record.lines_added}</span>
              <span style={{ margin: '0 4px' }}>/</span>
              <span style={{ color: '#ff4d4f' }}>-{record.lines_deleted}</span>
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
  ];

  const filteredCommits = commits.filter(commit => {
    const matchesSearch = !searchText || 
      commit.final_commit_message.toLowerCase().includes(searchText.toLowerCase()) ||
      commit.username.toLowerCase().includes(searchText.toLowerCase()) ||
      commit.repository_name.toLowerCase().includes(searchText.toLowerCase());

    return matchesSearch;
  });

  const repositories = [...new Set(commits.map(c => c.repository_name))];
  const users = [...new Set(commits.map(c => c.username))];

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
    </div>
  );
};

export default CommitHistory; 