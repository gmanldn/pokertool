import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export const TournamentView: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Tournament View
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>Tournament View component - Coming Soon</Typography>
      </Paper>
    </Box>
  );
};
