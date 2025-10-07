import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Select, Space, Typography, Statistic, Row, Col } from 'antd';
import { BarChartOutlined, EyeOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

const CategoryStats = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('kick');
  const [window, setWindow] = useState('7d');
  const [limit, setLimit] = useState(10);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/stats/categories?platform=${platform}&window=${window}&limit=${limit}`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching category stats:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [platform]);

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const columns = [
    {
      title: 'Rank',
      key: 'rank',
      render: (_, __, index) => (
        <span style={{ fontWeight: 'bold', fontSize: '16px' }}>#{index + 1}</span>
      ),
      width: 80,
    },
    {
      title: 'Game/Category',
      dataIndex: 'game_name',
      key: 'game',
      ellipsis: true,
      render: (text) => (
        <div style={{ fontWeight: 'bold', fontSize: '16px' }}>{text}</div>
      ),
    },
    {
      title: 'Total Streams',
      dataIndex: 'total_streams',
      key: 'streams',
      render: (text) => (
        <Statistic
          value={text}
          prefix={<PlayCircleOutlined />}
          valueStyle={{ fontSize: '16px' }}
        />
      ),
      sorter: (a, b) => a.total_streams - b.total_streams,
    },
    {
      title: 'Total Viewers',
      dataIndex: 'total_viewers',
      key: 'total_viewers',
      render: (text) => (
        <Statistic
          value={text}
          formatter={(value) => formatNumber(value)}
          prefix={<EyeOutlined />}
          valueStyle={{ fontSize: '16px', color: '#cf1322' }}
        />
      ),
      sorter: (a, b) => a.total_viewers - b.total_viewers,
    },
    {
      title: 'Avg Viewers',
      dataIndex: 'avg_viewers',
      key: 'avg_viewers',
      render: (text) => (
        <Statistic
          value={text}
          formatter={(value) => formatNumber(value)}
          valueStyle={{ fontSize: '16px' }}
        />
      ),
      sorter: (a, b) => a.avg_viewers - b.avg_viewers,
    },
    {
      title: 'Peak Viewers',
      dataIndex: 'peak_viewers',
      key: 'peak_viewers',
      render: (text) => (
        <Statistic
          value={text}
          formatter={(value) => formatNumber(value)}
          prefix={<EyeOutlined />}
          valueStyle={{ fontSize: '16px', color: '#1890ff' }}
        />
      ),
      sorter: (a, b) => a.peak_viewers - b.peak_viewers,
    },
  ];

  // Calculate totals
  const totalStreams = data.reduce((sum, item) => sum + (item.total_streams || 0), 0);
  const totalViewers = data.reduce((sum, item) => sum + (item.total_viewers || 0), 0);
  const avgViewers = data.length > 0 ? totalViewers / totalStreams : 0;

  return (
    <div>
      <Title level={2}>Category Statistics</Title>
      
      {/* Stats Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Categories"
              value={data.length}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Streams"
              value={totalStreams}
              formatter={(value) => formatNumber(value)}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Avg Viewers per Stream"
              value={avgViewers}
              formatter={(value) => formatNumber(value)}
              prefix={<EyeOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Space size="large">
          <div>
            <label style={{ marginRight: 8 }}>Platform:</label>
            <Select
              value={platform}
              onChange={setPlatform}
              style={{ width: 120 }}
            >
              <Option value="kick">Kick</Option>
              <Option value="twitch">Twitch</Option>
            </Select>
          </div>
          <div>
            <label style={{ marginRight: 8 }}>Time Window:</label>
            <Select
              value={window}
              onChange={setWindow}
              style={{ width: 120 }}
            >
              <Option value="24h">24 Hours</Option>
              <Option value="7d">7 Days</Option>
              <Option value="30d">30 Days</Option>
            </Select>
          </div>
          <div>
            <label style={{ marginRight: 8 }}>Limit:</label>
            <Select
              value={limit}
              onChange={setLimit}
              style={{ width: 100 }}
            >
              <Option value={10}>Top 10</Option>
              <Option value={20}>Top 20</Option>
              <Option value={50}>Top 50</Option>
            </Select>
          </div>
          <Button type="primary" onClick={fetchData} loading={loading}>
            Apply Filters
          </Button>
        </Space>
      </Card>

      {/* Chart */}
      <Card style={{ marginBottom: 24 }} title="Total Viewers by Category">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data.slice(0, 10)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="game_name" 
              angle={-45}
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis tickFormatter={formatNumber} />
            <Tooltip formatter={(value) => formatNumber(value)} />
            <Bar dataKey="total_viewers" fill="#1890ff" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="game_name"
          pagination={false}
          scroll={{ x: true }}
        />
      </Card>
    </div>
  );
};

export default CategoryStats;