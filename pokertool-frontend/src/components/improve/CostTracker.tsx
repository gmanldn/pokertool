/**Cost Tracking Component*/
import React, { useState, useEffect } from 'react';
import { Paper, Typography, LinearProgress } from '@mui/material';

export const CostTracker: React.FC = () => {
  const [cost, setCost] = useState(0);
  const [budget] = useState(100);
  
  return (
    <Paper sx={{p: 2}}>
      <Typography variant="h6">API Cost: ${cost.toFixed(2)} / ${budget}</Typography>
      <LinearProgress variant="determinate" value={(cost / budget) * 100} />
    </Paper>
  );
};
