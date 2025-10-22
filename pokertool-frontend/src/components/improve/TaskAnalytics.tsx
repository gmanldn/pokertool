/**Task Analytics Dashboard*/
import React from 'react';
import { Paper, Typography, Grid } from '@mui/material';

export const TaskAnalytics: React.FC = () => {
  const stats = { total: 100, completed: 25, avgTime: '2.5h', p0Count: 20 };
  
  return (
    <Paper sx={{p: 2}}>
      <Typography variant="h6">Task Analytics</Typography>
      <Grid container spacing={2}>
        {Object.entries(stats).map(([k, v]) => (
          <Grid item xs={3} key={k}><Typography>{k}: {v}</Typography></Grid>
        ))}
      </Grid>
    </Paper>
  );
};
