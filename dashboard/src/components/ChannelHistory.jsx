import React, { useState } from 'react';
import { Card, Input, Button, Select, Space, Typography, Empty, Spin, Alert } from 'antd';
import { SearchOutlined, HistoryOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

const ChannelHistory = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [platform, setPlatform] = useState('kick');
  const [channelId, setChannelId] = useState('');
  const [window, setWindow] = useState('24h');

  const fetchData = async () => {
    if (!channelId.trim()) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/channel/${platform}/${encodeURIComponent(channelId)}/history?window=${window}`);
      setData(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Error fetching channel history');
      setData(null);
    }
    setLoading(false);
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const chartData = data?.snapshots?.map(snapshot => ({
    time: new Date(snapshot.collected_at).toLocaleTimeString(),
    viewers: snapshot.viewer_count,
    date: new Date(snapshot.collected_at)
  })) || [];

  return (
    <div>
      <Title level={2}>Channel History</Title>
      
      {/* Search Form */}
      <Card style={{ marginBottom: 24 }}>
        <Space size="large" style={{ width: '100%' }}>
          <div style={{ flex: 1 }}>
            <label style={{ marginRight: 8 }}>Channel ID/Username:</label>
            <Input
              placeholder="Enter channel ID or username..."
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
              onPressEnter={fetchData}
              style={{ width: 300 }}
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
          <Button 
            type="primary" 
            onClick={fetchData} 
            loading={loading}
            disabled={!channelId.trim()}
            icon={<SearchOutlined />}
          >
            Get History
          </Button>
        </Space>
      </Card>

      {/* Loading */}
      {loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>Loading channel history...</div>
          </div>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Results */}
      {data && !loading && (
        <>
          {/* Channel Info */}
          <Card title="Channel Information" style={{ marginBottom: 24 }}>
            <Space size="large">
              <div>
                <strong>Display Name:</strong> {data.channel.display_name}
              </div>
              <div>
                <strong>Username:</strong> {data.channel.username}
              </div>
              <div>
                <strong>Platform:</strong> {data.channel.platform}
              </div>
              <div>
                <strong>Followers:</strong> {formatNumber(data.channel.follower_count)}
              </div>
            </Space>
          </Card>

          {/* Statistics */}
          <Card title="Statistics" style={{ marginBottom: 24 }}>
            <Space size="large">
              <div>
                <strong>Total Snapshots:</strong> {data.total_snapshots}
              </div>
              <div>
                <strong>Average Viewers:</strong> {formatNumber(Math.round(data.avg_viewer_count))}
              </div>
              <div>
                <strong>Peak Viewers:</strong> {formatNumber(data.peak_viewer_count)}
              </div>
            </Space>
          </Card>

          {/* Chart */}
          {chartData.length > 0 ? (
            <Card title="Viewer Count Over Time">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="time"
                    interval="preserveStartEnd"
                  />
                  <YAxis tickFormatter={formatNumber} />
                  <Tooltip 
                    formatter={(value) => [formatNumber(value), 'Viewers']}
                    labelFormatter={(label, payload) => {
                      if (payload && payload[0]) {
                        return payload[0].payload.date.toLocaleString();
                      }
                      return label;
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="viewers" 
                    stroke="#1890ff" 
                    strokeWidth={2}
                    dot={{ fill: '#1890ff', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          ) : (
            <Card>
              <Empty description="No data available for the selected time period" />
            </Card>
          )}
        </>
      )}

      {/* Empty State */}
      {!data && !loading && !error && (
        <Card>
          <Empty 
            icon={<HistoryOutlined style={{ fontSize: 64 }} />}
            description="Enter a channel ID/username and click 'Get History' to view channel analytics"
          />
        </Card>
      )}
    </div>
  );
};

export default ChannelHistory;