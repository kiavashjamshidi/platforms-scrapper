import React, { useState } from 'react';
import { Card, Button, Select, Space, Typography, Alert, message } from 'antd';
import { DownloadOutlined, FileExcelOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

const ExportData = () => {
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('kick');
  const [window, setWindow] = useState('24h');

  const handleExport = async () => {
    setLoading(true);
    try {
      console.log('Starting export request...', { platform, window });
      
      const response = await axios.get(`/export/csv?platform=${platform}&window=${window}`, {
        responseType: 'blob',
        headers: {
          'Accept': 'text/csv',
        },
      });
      
      console.log('Export response received:', response);
      
      // Create download link using globalThis.window to avoid variable conflict
      const url = globalThis.window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${platform}_streams_${window}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      globalThis.window.URL.revokeObjectURL(url);
      
      message.success('Data exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      message.error('Error exporting data: ' + errorMessage);
    }
    setLoading(false);
  };

  return (
    <div>
      <Title level={2}>Export Data</Title>
      
      <Card style={{ maxWidth: 600 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            message="Export Stream Data"
            description="Download streaming data as a CSV file for analysis in Excel, Google Sheets, or other tools."
            type="info"
            showIcon
          />
          
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
          </Space>

          <Button
            type="primary"
            size="large"
            icon={<DownloadOutlined />}
            onClick={handleExport}
            loading={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'Exporting...' : 'Export to CSV'}
          </Button>

          <div style={{ marginTop: 24 }}>
            <Title level={4}>
              <FileExcelOutlined /> What's included in the export:
            </Title>
            <ul>
              <li>Channel information (username, display name, followers)</li>
              <li>Stream details (title, game, viewer count)</li>
              <li>Timestamps (when stream started, when data was collected)</li>
              <li>Stream URLs for easy access</li>
            </ul>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default ExportData;