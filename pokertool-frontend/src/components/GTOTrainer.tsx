/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/GTOTrainer.tsx
version: v28.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
---
POKERTOOL-HEADER-END */

import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export const GTOTrainer: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        GTO Trainer
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Typography>GTO Trainer component - Coming Soon</Typography>
      </Paper>
    </Box>
  );
};