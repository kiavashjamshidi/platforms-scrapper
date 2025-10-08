import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Paper, Typography, Grid, CircularProgress } from '@mui/material';

function PlatformStats({ platform }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    axios.get(`/live/top?platform=${platform}&limit=100`)
      .then(res => {
        const streams = res.data;
        const totalViewers = streams.reduce((sum, s) => sum + s.viewer_count, 0);
        const totalFollowers = streams.reduce((sum, s) => sum + s.follower_count, 0);
        setStats({
          totalStreams: streams.length,
          totalViewers,
          totalFollowers,
        });
      })
      .finally(() => setLoading(false));
  }, [platform]);

  if (loading) return <CircularProgress sx={{ display: 'block', mx: 'auto', my: 2 }} />;
  if (!stats) return null;

  return (
    <Paper sx={{ mb: 2, p: 2 }}>
      <Grid container spacing={2} justifyContent="center">
        <Grid item>
          <Typography variant="h6">Total Streams: {stats.totalStreams}</Typography>
        </Grid>
        <Grid item>
          <Typography variant="h6">Total Viewers: {stats.totalViewers.toLocaleString()}</Typography>
        </Grid>
        <Grid item>
          <Typography variant="h6">Total Followers: {stats.totalFollowers.toLocaleString()}</Typography>
        </Grid>
      </Grid>
    </Paper>
  );
}

export default PlatformStats;
