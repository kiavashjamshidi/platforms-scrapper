import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Select, InputNumber, Space, Typography, Tag, Avatar, Statistic } from 'antd';
import { TrophyOutlined, EyeOutlined, UserOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

const MostActive = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('kick');
  const [window, setWindow] = useState('7d');
  const [limit, setLimit] = useState(10);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/live/most-active?platform=${platform}&window=${window}&limit=${limit}`);
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

  const columns = [
    {
      title: 'Rank',
      key: 'rank',
      render: (_, __, index) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {index < 3 && <TrophyOutlined style={{ color: ['#ffd700', '#c0c0c0', '#cd7f32'][index], marginRight: 8 }} />}
          <span style={{ fontWeight: 'bold', fontSize: '16px' }}>#{index + 1}</span>
        </div>
      ),
      width: 80,
    },
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
      title: 'Stream Sessions',
      dataIndex: 'stream_count',
      key: 'sessions',
      render: (text) => (
        <Statistic
          value={text}
          valueStyle={{ fontSize: '16px', color: '#1890ff' }}
        />
      ),
      sorter: (a, b) => a.stream_count - b.stream_count,
    },
    {
      title: 'Avg Viewers',
      dataIndex: 'avg_viewers',
      key: 'avg_viewers',
      render: (text) => (
        <Statistic
          value={text}
          formatter={(value) => formatNumber(value)}
          prefix={<EyeOutlined />}
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
          valueStyle={{ fontSize: '16px', color: '#cf1322' }}
        />
      ),
      sorter: (a, b) => a.peak_viewers - b.peak_viewers,
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
          valueStyle={{ fontSize: '16px', color: '#1890ff' }}
        />
      ),
      sorter: (a, b) => a.follower_count - b.follower_count,
    },
    {
      title: 'Last Seen',
      dataIndex: 'last_seen',
      key: 'last_seen',
      render: (text) => new Date(text).toLocaleDateString(),
    },
  ];

  return (
    <div>
      <Title level={2}>Most Active Streamers</Title>
      
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
            <InputNumber
              min={1}
              max={100}
              value={limit}
              onChange={setLimit}
              style={{ width: 100 }}
            />
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
          pagination={false}
          scroll={{ x: true }}
        />
      </Card>
    </div>
  );
};

export default MostActive;