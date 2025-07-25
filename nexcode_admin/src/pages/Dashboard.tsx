import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Typography,
  Table,
  Tag,
  Space,
  Progress,
  Avatar,
  Spin,
  Alert,
} from 'antd';
import {
  UserOutlined,
  CodeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  StarOutlined,
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { systemAPI, commitsAPI, type SystemStats } from '../services/api';

// 错误边界组件
class ChartErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Chart error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Typography.Text type="secondary">图表加载失败</Typography.Text>
        </div>
      );
    }

    return this.props.children;
  }
}

const { Title, Text } = Typography;

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

interface DashboardStats extends Omit<SystemStats, 'avg_rating'> {
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
  avg_rating?: number;
}

interface CommitAnalytics {
  daily_trends: Array<{ date: string; commit_count: number }>;
  user_activity: Array<{ username: string; commit_count: number }>;
  repository_activity: Array<{ repository_name: string; commit_count: number }>;
  model_usage: Array<{ model_name: string; usage_count: number }>;
  commit_style_distribution: Array<{ style: string; count: number }>;
}

interface RecentActivity {
  id: string;
  user: string;
  action: string;
  time: string;
  status: 'success' | 'warning' | 'error';
}

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

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [commitAnalytics, setCommitAnalytics] = useState<CommitAnalytics | null>(null);
  const [, setRecentActivities] = useState<RecentActivity[]>([]);
  const [recentCommits, setRecentCommits] = useState<CommitRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行获取系统统计和最近提交
      const [systemStats, commitsResponse, analyticsData] = await Promise.all([
        systemAPI.getSystemStats(),
        commitsAPI.getAllCommits({ skip: 0, limit: 10 }).catch(() => ({ commits: [], total: 0, skip: 0, limit: 10 })),
        commitsAPI.getCommitAnalytics(30).catch(() => null)
      ]);

      // 验证和清理分析数据
      const cleanedAnalytics = analyticsData ? {
        ...analyticsData,
        daily_trends: (analyticsData.daily_trends || []).filter(item => 
          item && typeof item.date === 'string' && typeof item.commit_count === 'number'
        ),
        commit_style_distribution: (analyticsData.commit_style_distribution || []).filter(item => 
          item && typeof item.style === 'string' && typeof item.count === 'number' && item.count > 0
        )
      } : null;

      // 尝试获取健康检查数据（可选）
      let healthData: any = null;
      try {
        const health = await systemAPI.getHealthCheck();
        healthData = health;
      } catch (error) {
        console.log('健康检查API暂时不可用');
      }

      // 合并系统统计和健康数据
      const combinedStats: DashboardStats = {
        ...systemStats,
        cpu_usage: healthData?.cpu_usage,
        memory_usage: healthData?.memory_usage,
        disk_usage: healthData?.disk_usage,
        avg_rating: healthData?.avg_rating
      };

      setStats(combinedStats);
      setCommitAnalytics(cleanedAnalytics);
      setRecentActivities([
        {
          id: '1',
          user: 'zhangsan',
          action: '生成提交消息',
          time: '2分钟前',
          status: 'success',
        },
        {
          id: '2',
          user: 'lisi',
          action: '代码质量检查',
          time: '5分钟前',
          status: 'success',
        },
        {
          id: '3',
          user: 'wangwu',
          action: 'Git错误分析',
          time: '8分钟前',
          status: 'warning',
        },
        {
          id: '4',
          user: 'admin',
          action: '用户管理',
          time: '15分钟前',
          status: 'success',
        },
      ]);

      // 处理最近提交
      const formattedCommits = (commitsResponse.commits || []).map((commit) => ({
        ...commit,
        created_at: new Date(commit.created_at).toLocaleString('zh-CN'),
      }));
      setRecentCommits(formattedCommits);
    } catch (err: any) {
      console.error('获取Dashboard数据失败:', err);
      setError(err.message || '获取数据失败');
      // 设置默认值避免错误
      setRecentCommits([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // 每5分钟刷新一次数据
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const columns = [
    {
      title: '仓库',
      dataIndex: 'repository_name',
      key: 'repository_name',
      render: (text: string) => (
        <Space>
          <CodeOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      render: (username: string) => (
        <Space>
          <Avatar size="small" icon={<UserOutlined />} />
          {username || '未知用户'}
        </Space>
      ),
    },
    {
      title: '提交风格',
      dataIndex: 'commit_style',
      key: 'commit_style',
      render: (style: string) => (
        <Tag color="blue">{style}</Tag>
      ),
    },
    {
      title: '评分',
      dataIndex: 'user_rating',
      key: 'user_rating',
      render: (rating: number | null) => (
        rating ? (
          <Space>
            <StarOutlined style={{ color: '#faad14' }} />
            {rating.toFixed(1)}
          </Space>
        ) : (
          <Text type="secondary">未评分</Text>
        )
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          'completed': { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
          'pending': { color: 'processing', icon: <ClockCircleOutlined />, text: '处理中' },
          'failed': { color: 'error', icon: <ClockCircleOutlined />, text: '失败' }
        };
        const config = statusConfig[status as keyof typeof statusConfig] || 
                      { color: 'default', icon: <ClockCircleOutlined />, text: status };
        
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载Dashboard数据...</Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="数据加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <button onClick={fetchDashboardData}>
            重试
          </button>
        }
      />
    );
  }

  return (
    <div>
      <Title level={2}>控制台</Title>
      
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={stats?.total_users || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={stats?.active_users || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${stats?.total_users || 0}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日提交"
              value={stats?.commits_today || 0}
              prefix={<CodeOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均评分"
              value={stats?.avg_rating || 0}
              precision={1}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix="/ 5.0"
            />
          </Card>
        </Col>
      </Row>

      {/* 系统监控 */}
      {(stats?.cpu_usage !== undefined || stats?.memory_usage !== undefined || stats?.disk_usage !== undefined) && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={8}>
            <Card title="CPU使用率" size="small">
              <Progress
                type="circle"
                percent={Math.round(stats?.cpu_usage || 0)}
                strokeColor={stats?.cpu_usage && stats.cpu_usage > 80 ? '#ff4d4f' : '#52c41a'}
              />
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="内存使用率" size="small">
              <Progress
                type="circle"
                percent={Math.round(stats?.memory_usage || 0)}
                strokeColor={stats?.memory_usage && stats.memory_usage > 80 ? '#ff4d4f' : '#52c41a'}
              />
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="磁盘使用率" size="small">
              <Progress
                type="circle"
                percent={Math.round(stats?.disk_usage || 0)}
                strokeColor={stats?.disk_usage && stats.disk_usage > 80 ? '#ff4d4f' : '#52c41a'}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 图表区域 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="最近30天提交趋势">
            <ChartErrorBoundary>
              {commitAnalytics?.daily_trends && commitAnalytics.daily_trends.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={commitAnalytics.daily_trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(tick) => {
                        try {
                          return new Date(tick).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
                        } catch {
                          return tick;
                        }
                      }}
                    />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="commit_count" name="提交数" stroke="#8884d8" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: '50px' }}>
                  <Text type="secondary">暂无数据</Text>
                </div>
              )}
            </ChartErrorBoundary>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="提交风格分布">
            <ChartErrorBoundary>
              {commitAnalytics?.commit_style_distribution && commitAnalytics.commit_style_distribution.length > 0 ? (
                <div>
                  {commitAnalytics.commit_style_distribution.map((item, index) => (
                    <div key={item.style} style={{ marginBottom: '8px', display: 'flex', alignItems: 'center' }}>
                      <div 
                        style={{ 
                          width: '12px', 
                          height: '12px', 
                          backgroundColor: COLORS[index % COLORS.length],
                          marginRight: '8px',
                          borderRadius: '50%'
                        }}
                      />
                      <Text>{item.style}: {item.count}</Text>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '50px' }}>
                  <Text type="secondary">暂无数据</Text>
                </div>
              )}
            </ChartErrorBoundary>
          </Card>
        </Col>
      </Row>

      {/* 最近活动 */}
      <Card title="最近提交" style={{ marginBottom: 24 }}>
        <Table
          dataSource={recentCommits}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 5, showSizeChanger: false }}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard; 