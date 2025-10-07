import React, { useState } from 'react';
import { Card, Table, Button, Select, Input, Space, Typography, Tag, Avatar, Statistic, Empty, Alert } from 'antd';
import { SearchOutlined, EyeOutlined, UserOutlined, PlayCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

const SearchStreams = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('kick');
  const [query, setQuery] = useState('');
  const [limit, setLimit] = useState(20);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  const fetchData = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const response = await axios.get(`/search?platform=${platform}&q=${encodeURIComponent(query)}&limit=${limit}`);
      console.log('Search response:', response.data); // Debug log
      setData(response.data || []);
    } catch (error) {
      console.error('Error searching:', error);
      setError(error.response?.data?.detail || 'Search failed');
      setData([]);
    }
    setLoading(false);
  };

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

  return (
    <div>
      <Title level={2}>Search Live Streams</Title>
      
      {/* Search Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Space size="large" style={{ width: '100%' }}>
          <div style={{ flex: 1 }}>
            <label style={{ marginRight: 8 }}>Search:</label>
            <Input
              placeholder="Search by title, game, or username..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onPressEnter={fetchData}
              style={{ width: 300 }}
              suffix={<SearchOutlined />}
            />
          </div>
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
            <Input
              type="number"
              min={1}
              max={100}
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 20)}
              style={{ width: 100 }}
            />
          </div>
          <Button 
            type="primary" 
            onClick={fetchData} 
            loading={loading}
            disabled={!query.trim()}
            icon={<SearchOutlined />}
          >
            Search
          </Button>
        </Space>
      </Card>

      {/* Results */}
      <Card>
        {error && (
          <Alert
            message="Search Error"
            description={error}
            type="error"
            style={{ marginBottom: 16 }}
          />
        )}
        
        {!hasSearched && !loading ? (
          <Empty description="Enter a search term and click Search to find streams" />
        ) : hasSearched && data.length === 0 && !loading ? (
          <Empty description={`No streams found for "${query}" on ${platform}`} />
        ) : (
          <Table
            columns={columns}
            dataSource={data}
            loading={loading}
            rowKey="channel_id"
            pagination={{ pageSize: 10, showSizeChanger: true }}
            scroll={{ x: true }}
          />
        )}
      </Card>
    </div>
  );
};

export default SearchStreams;