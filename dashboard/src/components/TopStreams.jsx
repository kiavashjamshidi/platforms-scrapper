import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Select, InputNumber, Space, Typography, Tag, Avatar, Statistic, Row, Col } from 'antd';
import { EyeOutlined, UserOutlined, PlayCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

const TopStreams = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('kick');
  const [limit, setLimit] = useState(20);
  const [sortBy, setSortBy] = useState('viewers');

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/live/top?platform=${platform}&limit=${limit}&sort_by=${sortBy}`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching data:', error);
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

  const getTimeAgo = (dateString) => {
    const now = new Date();
    const startTime = new Date(dateString);
    const diffMs = now - startTime;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 0) return `${diffHours}h ${diffMins}m ago`;
    return `${diffMins}m ago`;
  };

  const columns = [
    {
      title: 'Channel',
      dataIndex: 'display_name',
      key: 'channel',
      render: (text, record) => (
        <Space>
          <Avatar size="large" icon={<UserOutlined />}>
            {text?.charAt(0)?.toUpperCase()}
          </Avatar>
          <div>
            <div style={{ fontWeight: 'bold' }}>{text}</div>
            <Tag color={record.platform === 'kick' ? 'green' : 'purple'}>
              {record.platform}
            </Tag>
          </div>
        </Space>
      ),
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      width: '30%',
    },
    {
      title: 'Game',
      dataIndex: 'game_name',
      key: 'game',
      render: (text) => text ? <Tag color="blue">{text}</Tag> : '-',
    },
    {
      title: 'Viewers',
      dataIndex: 'viewer_count',
      key: 'viewers',
      render: (text) => (
        <Statistic
          value={text}
          formatter={(value) => formatNumber(value)}
          prefix={<EyeOutlined />}
          valueStyle={{ color: '#cf1322', fontSize: '16px' }}
        />
      ),
      sorter: (a, b) => a.viewer_count - b.viewer_count,
    },
    {
      title: 'Followers',
      dataIndex: 'follower_count',
      key: 'followers',
      render: (text) => (
        <Statistic
          value={text}
          formatter={(value) => formatNumber(value)}
          prefix={<UserOutlined />}
          valueStyle={{ color: '#1890ff', fontSize: '16px' }}
        />
      ),
      sorter: (a, b) => a.follower_count - b.follower_count,
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started',
      render: (text) => getTimeAgo(text),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          href={record.stream_url}
          target="_blank"
          size="small"
        >
          Watch
        </Button>
      ),
    },
  ];

  // Calculate stats
  const totalViewers = data.reduce((sum, item) => sum + (item.viewer_count || 0), 0);
  const totalFollowers = data.reduce((sum, item) => sum + (item.follower_count || 0), 0);

  return (
    <div>
      <Title level={2}>Top Live Streams</Title>
      
      {/* Stats Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Streams"
              value={data.length}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Viewers"
              value={totalViewers}
              formatter={(value) => formatNumber(value)}
              prefix={<EyeOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Followers"
              value={totalFollowers}
              formatter={(value) => formatNumber(value)}
              prefix={<UserOutlined />}
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
            <label style={{ marginRight: 8 }}>Limit:</label>
            <InputNumber
              min={1}
              max={500}
              value={limit}
              onChange={setLimit}
              style={{ width: 100 }}
            />
          </div>
          <div>
            <label style={{ marginRight: 8 }}>Sort by:</label>
            <Select
              value={sortBy}
              onChange={setSortBy}
              style={{ width: 150 }}
            >
              <Option value="viewers">Current Viewers</Option>
              <Option value="followers">Follower Count</Option>
            </Select>
          </div>
          <Button type="primary" onClick={fetchData} loading={loading}>
            Apply Filters
          </Button>
        </Space>
      </Card>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="channel_id"
          pagination={{ pageSize: 10, showSizeChanger: true }}
          scroll={{ x: true }}
        />
      </Card>
    </div>
  );
};

export default TopStreams;