import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export const HandHistory: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Hand History
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>Hand History component - Coming Soon</Typography>
      </Paper>
    </Box>
  );
};
