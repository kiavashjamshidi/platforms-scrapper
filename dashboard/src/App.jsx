import React, { useState } from 'react';
import { Layout, Menu, Typography, theme } from 'antd';
import { 
  VideoCameraOutlined, 
  TrophyOutlined, 
  SearchOutlined, 
  BarChartOutlined,
  HistoryOutlined,
  DownloadOutlined 
} from '@ant-design/icons';
import TopStreams from './components/TopStreams';
import MostActive from './components/MostActive';
import SearchStreams from './components/SearchStreams';
import CategoryStats from './components/CategoryStats';
import ChannelHistory from './components/ChannelHistory';
import ExportData from './components/ExportData';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const menuItems = [
  {
    key: 'top',
    icon: <VideoCameraOutlined />,
    label: 'Top Live Streams',
  },
  {
    key: 'active',
    icon: <TrophyOutlined />,
    label: 'Most Active',
  },
  {
    key: 'search',
    icon: <SearchOutlined />,
    label: 'Search Streams',
  },
  {
    key: 'categories',
    icon: <BarChartOutlined />,
    label: 'Category Stats',
  },
  {
    key: 'history',
    icon: <HistoryOutlined />,
    label: 'Channel History',
  },
  {
    key: 'export',
    icon: <DownloadOutlined />,
    label: 'Export Data',
  },
];

function App() {
  const [selectedMenu, setSelectedMenu] = useState('top');
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const renderContent = () => {
    switch (selectedMenu) {
      case 'top':
        return <TopStreams />;
      case 'active':
        return <MostActive />;
      case 'search':
        return <SearchStreams />;
      case 'categories':
        return <CategoryStats />;
      case 'history':
        return <ChannelHistory />;
      case 'export':
        return <ExportData />;
      default:
        return <TopStreams />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={250} style={{ background: colorBgContainer }}>
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Title level={4}>Streaming Dashboard</Title>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedMenu]}
          items={menuItems}
          onClick={({ key }) => setSelectedMenu(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }} />
        <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {renderContent()}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
