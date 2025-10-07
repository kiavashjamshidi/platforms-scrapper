import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, CircularProgress, Chip, Avatar } from '@mui/material';

function StreamsTable({ streams, loading }) {
  if (loading) return <CircularProgress sx={{ display: 'block', mx: 'auto', my: 4 }} />;
  if (!streams.length) return <div>No live streams found.</div>;

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
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

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Channel</TableCell>
            <TableCell>Title</TableCell>
            <TableCell>Game</TableCell>
            <TableCell align="right">Viewers</TableCell>
            <TableCell align="right">Followers</TableCell>
            <TableCell>Started</TableCell>
            <TableCell>Link</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {streams.map((s) => (
            <TableRow key={s.channel_id} hover>
              <TableCell>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Avatar sx={{ width: 32, height: 32 }}>
                    {s.display_name.charAt(0).toUpperCase()}
                  </Avatar>
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{s.display_name}</div>
                    <div style={{ fontSize: '0.8em', color: 'gray' }}>{s.platform}</div>
                  </div>
                </div>
              </TableCell>
              <TableCell style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {s.title}
              </TableCell>
              <TableCell>
                {s.game_name && (
                  <Chip label={s.game_name} size="small" variant="outlined" />
                )}
              </TableCell>
              <TableCell align="right">
                <strong style={{ color: '#ff4444' }}>{formatNumber(s.viewer_count)}</strong>
              </TableCell>
              <TableCell align="right">
                <strong style={{ color: '#4444ff' }}>{formatNumber(s.follower_count)}</strong>
              </TableCell>
              <TableCell style={{ fontSize: '0.9em' }}>
                {getTimeAgo(s.started_at)}
              </TableCell>
              <TableCell>
                <a 
                  href={s.stream_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ 
                    textDecoration: 'none', 
                    background: '#1976d2', 
                    color: 'white', 
                    padding: '4px 8px', 
                    borderRadius: '4px',
                    fontSize: '0.8em'
                  }}
                >
                  Watch
                </a>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default StreamsTable;
