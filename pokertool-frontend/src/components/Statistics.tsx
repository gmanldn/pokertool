import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export const Statistics: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Statistics
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>Statistics component - Coming Soon</Typography>
      </Paper>
    </Box>
  );
};
