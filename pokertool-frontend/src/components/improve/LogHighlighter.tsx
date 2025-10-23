import React from 'react';
import { Box, Typography } from '@mui/material';

interface LogEntry {
  level: 'error' | 'warning' | 'info' | 'debug';
  message: string;
}

/**
 * Highlights errors in log display
 */
export const LogHighlighter: React.FC<{ logs: LogEntry[] }> = ({ logs }) => {
  const getColor = (level: string) => {
    switch (level) {
      case 'error': return '#f44336';
      case 'warning': return '#ff9800';
      default: return '#fff';
    }
  };

  return (
    <Box>
      {logs.map((log, i) => (
        <Typography key={i} style={{ color: getColor(log.level), fontFamily: 'monospace' }}>
          [{log.level.toUpperCase()}] {log.message}
        </Typography>
      ))}
    </Box>
  );
};
