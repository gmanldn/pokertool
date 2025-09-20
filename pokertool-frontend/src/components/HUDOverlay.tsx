import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export const HUDOverlay: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        HUD Overlay
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>HUD Overlay component - Coming Soon</Typography>
      </Paper>
    </Box>
  );
};
