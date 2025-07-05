import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Space,
  Typography,
  Progress,
  Alert,
  Button,
} from 'antd';
import {
  ApiOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const { Title } = Typography;

interface APIEndpoint {
  endpoint: string;
  method: string;
  status: 'healthy' | 'warning' | 'error';
  response_time: number;
  success_rate: number;
  requests_24h: number;
}

interface APIMetrics {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_response_time: number;
  peak_rps: number;
  active_users: number;
}

const APIMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<APIMetrics>({
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    avg_response_time: 0,
    peak_rps: 0,
    active_users: 0,
  });

  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
    // 设置定时刷新
    const interval = setInterval(loadData, 30000); // 30秒刷新一次
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setLoading(true);
    
    // 模拟API数据
    setTimeout(() => {
      const mockMetrics: APIMetrics = {
        total_requests: 15847,
        successful_requests: 15203,
        failed_requests: 644,
        avg_response_time: 245,
        peak_rps: 89,
        active_users: 23,
      };

      const mockEndpoints: APIEndpoint[] = [
        {
          endpoint: '/v1/commit-message',
          method: 'POST',
          status: 'healthy',
          response_time: 180,
          success_rate: 98.5,
          requests_24h: 4567,
        },
        {
          endpoint: '/v1/code-review',
          method: 'POST',
          status: 'healthy',
          response_time: 234,
          success_rate: 97.2,
          requests_24h: 3421,
        },
        {
          endpoint: '/v1/git-error',
          method: 'POST',
          status: 'warning',
          response_time: 456,
          success_rate: 94.8,
          requests_24h: 2134,
        },
        {
          endpoint: '/v1/code-quality-check',
          method: 'POST',
          status: 'healthy',
          response_time: 312,
          success_rate: 96.7,
          requests_24h: 1876,
        },
        {
          endpoint: '/v1/chat/completions',
          method: 'POST',
          status: 'error',
          response_time: 892,
          success_rate: 89.3,
          requests_24h: 987,
        },
      ];

      setMetrics(mockMetrics);
      setEndpoints(mockEndpoints);
      setLoading(false);
    }, 1000);
  };

  // 模拟时间序列数据
  const chartData = [
    { time: '00:00', requests: 45, errors: 2, response_time: 180 },
    { time: '04:00', requests: 23, errors: 1, response_time: 165 },
    { time: '08:00', requests: 178, errors: 8, response_time: 245 },
    { time: '12:00', requests: 287, errors: 12, response_time: 298 },
    { time: '16:00', requests: 234, errors: 9, response_time: 267 },
    { time: '20:00', requests: 156, errors: 5, response_time: 198 },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <CheckCircleOutlined />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'green';
      case 'warning':
        return 'orange';
      case 'error':
        return 'red';
      default:
        return 'default';
    }
  };

  const columns = [
    {
      title: '接口',
      dataIndex: 'endpoint',
      key: 'endpoint',
      render: (text: string, record: APIEndpoint) => (
        <Space>
          <Tag color="blue">{record.method}</Tag>
          <code>{text}</code>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Space>
          {getStatusIcon(status)}
          <Tag color={getStatusColor(status)}>
            {status === 'healthy' ? '健康' : status === 'warning' ? '警告' : '错误'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '响应时间',
      dataIndex: 'response_time',
      key: 'response_time',
      render: (time: number) => `${time}ms`,
      sorter: (a: APIEndpoint, b: APIEndpoint) => a.response_time - b.response_time,
    },
    {
      title: '成功率',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (rate: number) => (
        <Progress
          percent={rate}
          size="small"
          strokeColor={rate >= 95 ? '#52c41a' : rate >= 90 ? '#faad14' : '#ff4d4f'}
        />
      ),
      sorter: (a: APIEndpoint, b: APIEndpoint) => a.success_rate - b.success_rate,
    },
    {
      title: '24小时请求数',
      dataIndex: 'requests_24h',
      key: 'requests_24h',
      render: (count: number) => count.toLocaleString(),
      sorter: (a: APIEndpoint, b: APIEndpoint) => a.requests_24h - b.requests_24h,
    },
  ];

  const successRate = (metrics.successful_requests / metrics.total_requests) * 100;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2}>API监控</Title>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={loadData}
          loading={loading}
        >
          刷新数据
        </Button>
      </div>

      {/* 系统状态警告 */}
      {metrics.failed_requests > 100 && (
        <Alert
          message="系统状态警告"
          description={`检测到较高的错误率，最近24小时内共有 ${metrics.failed_requests} 个失败请求`}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 关键指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={4}>
          <Card>
            <Statistic
              title="总请求数"
              value={metrics.total_requests}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card>
            <Statistic
              title="成功率"
              value={successRate}
              precision={1}
              suffix="%"
              valueStyle={{ color: successRate >= 95 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={metrics.avg_response_time}
              suffix="ms"
              valueStyle={{ color: metrics.avg_response_time <= 300 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card>
            <Statistic
              title="峰值RPS"
              value={metrics.peak_rps}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card>
            <Statistic
              title="活跃用户"
              value={metrics.active_users}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card>
            <Statistic
              title="失败请求"
              value={metrics.failed_requests}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* 请求趋势图 */}
        <Col xs={24} lg={12}>
          <Card title="请求趋势（24小时）">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="requests" 
                  stroke="#1890ff" 
                  name="请求数"
                />
                <Line 
                  type="monotone" 
                  dataKey="errors" 
                  stroke="#ff4d4f" 
                  name="错误数"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* 响应时间图 */}
        <Col xs={24} lg={12}>
          <Card title="响应时间趋势">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="response_time" fill="#52c41a" name="响应时间(ms)" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* API接口状态表格 */}
      <Card title="API接口状态">
        <Table
          columns={columns}
          dataSource={endpoints}
          rowKey="endpoint"
          loading={loading}
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default APIMonitor; 