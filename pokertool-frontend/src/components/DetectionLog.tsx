/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/DetectionLog.tsx
version: v28.0.0
last_commit: '2025-10-15T00:00:00+01:00'
fixes:
- date: '2025-10-15'
  summary: Created DetectionLog component for real-time detection data stream
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
  useTheme,
  useMediaQuery,
  Divider,
} from '@mui/material';
import {
  Clear,
  PauseCircle,
  PlayCircle,
  GetApp,
  FilterList,
} from '@mui/icons-material';

interface DetectionLogProps {
  messages?: any[];
}

interface LogEntry {
  timestamp: string;
  type: 'player' | 'card' | 'pot' | 'action' | 'system' | 'error';
  severity: 'info' | 'success' | 'warning' | 'error';
  message: string;
  data?: any;
}

export const DetectionLog: React.FC<DetectionLogProps> = ({ messages = [] }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const logContainerRef = useRef<HTMLDivElement>(null);

  const [logs, setLogs] = useState<LogEntry[]>([
    {
      timestamp: new Date().toISOString(),
      type: 'system',
      severity: 'info',
      message: 'Detection system ready - waiting for poker table...',
      data: { version: '84.0.0' },
    },
  ]);

  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filters, setFilters] = useState({
    player: true,
    card: true,
    pot: true,
    action: true,
    system: true,
    error: true,
  });

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Connect to WebSocket for real detection events
  useEffect(() => {
    if (isPaused) return;

    const ws = new WebSocket('ws://localhost:5001/ws/detections');

    ws.onopen = () => {
      console.log('Detection WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const newLog: LogEntry = {
        timestamp: data.timestamp || new Date().toISOString(),
        type: data.type || 'system',
        severity: data.severity || 'info',
        message: data.message,
        data: data.data || {},
      };
      setLogs((prev) => [...prev, newLog].slice(-100)); // Keep last 100 entries
    };

    ws.onerror = (error) => {
      console.error('Detection WebSocket error:', error);
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          type: 'error' as const,
          severity: 'error' as const,
          message: 'Failed to connect to detection stream - is the backend running?',
          data: {},
        },
      ].slice(-100));
    };

    ws.onclose = () => {
      console.log('Detection WebSocket closed');
    };

    return () => ws.close();
  }, [isPaused]);

  const handleClearLogs = () => {
    setLogs([
      {
        timestamp: new Date().toISOString(),
        type: 'system',
        severity: 'info',
        message: 'Logs cleared',
      },
    ]);
  };

  const handleExportLogs = () => {
    const logData = logs.map((log) => ({
      timestamp: log.timestamp,
      type: log.type,
      severity: log.severity,
      message: log.message,
      data: log.data,
    }));

    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `detection-log-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLogColor = (entry: LogEntry) => {
    const typeColors: Record<string, string> = {
      player: '#2196f3',
      card: '#9c27b0',
      pot: '#ff9800',
      action: '#4caf50',
      system: '#607d8b',
      error: '#f44336',
    };
    return typeColors[entry.type] || '#999';
  };

  const getSeverityColor = (severity: LogEntry['severity']) => {
    const severityColors: Record<string, string> = {
      info: '#2196f3',
      success: '#4caf50',
      warning: '#ff9800',
      error: '#f44336',
    };
    return severityColors[severity];
  };

  const filteredLogs = logs.filter((log) => filters[log.type]);

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight="bold">
          Detection Log
        </Typography>
        <Box display="flex" gap={1} alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                size="small"
              />
            }
            label={<Typography variant="caption">Auto-scroll</Typography>}
          />
          <IconButton
            onClick={() => setIsPaused(!isPaused)}
            color={isPaused ? 'warning' : 'success'}
            size="small"
          >
            {isPaused ? <PlayCircle /> : <PauseCircle />}
          </IconButton>
          <IconButton onClick={handleExportLogs} size="small">
            <GetApp />
          </IconButton>
          <IconButton onClick={handleClearLogs} size="small">
            <Clear />
          </IconButton>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <FilterList fontSize="small" />
          <Typography variant="subtitle2">Filters</Typography>
        </Box>
        <Box display="flex" gap={1} flexWrap="wrap">
          {Object.entries(filters).map(([key, value]) => (
            <Chip
              key={key}
              label={key.toUpperCase()}
              onClick={() => setFilters({ ...filters, [key]: !value })}
              color={value ? 'primary' : 'default'}
              variant={value ? 'filled' : 'outlined'}
              size="small"
              sx={{
                borderColor: getLogColor({ type: key } as LogEntry),
                color: value ? '#fff' : getLogColor({ type: key } as LogEntry),
                backgroundColor: value ? getLogColor({ type: key } as LogEntry) : 'transparent',
              }}
            />
          ))}
        </Box>
      </Paper>

      {/* Log Stream */}
      <Paper
        sx={{
          height: 'calc(100vh - 300px)',
          overflow: 'auto',
          backgroundColor: '#1a1a1a',
          fontFamily: 'monospace',
        }}
        ref={logContainerRef}
      >
        {filteredLogs.map((entry, index) => (
          <Box
            key={index}
            sx={{
              p: 1.5,
              borderBottom: '1px solid rgba(255,255,255,0.05)',
              '&:hover': {
                backgroundColor: 'rgba(255,255,255,0.03)',
              },
            }}
          >
            <Box display="flex" alignItems="flex-start" gap={1}>
              <Typography
                variant="caption"
                sx={{
                  color: '#666',
                  minWidth: 180,
                  fontFamily: 'monospace',
                  fontSize: '0.7rem',
                }}
              >
                {new Date(entry.timestamp).toLocaleTimeString('en-US', {
                  hour12: false,
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                  fractionalSecondDigits: 3,
                })}
              </Typography>
              <Chip
                label={entry.type.toUpperCase()}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  backgroundColor: getLogColor(entry),
                  color: '#fff',
                  minWidth: 60,
                }}
              />
              <Chip
                label={entry.severity.toUpperCase()}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  backgroundColor: getSeverityColor(entry.severity),
                  color: '#fff',
                  minWidth: 60,
                }}
              />
              <Typography
                variant="body2"
                sx={{
                  color: '#fff',
                  fontFamily: 'monospace',
                  fontSize: '0.85rem',
                  flex: 1,
                }}
              >
                {entry.message}
              </Typography>
            </Box>
            {entry.data && Object.keys(entry.data).length > 0 && (
              <Box
                sx={{
                  ml: 28,
                  mt: 0.5,
                  p: 1,
                  backgroundColor: 'rgba(255,255,255,0.03)',
                  borderRadius: 1,
                  fontSize: '0.75rem',
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: '#888',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {JSON.stringify(entry.data, null, 2)}
                </Typography>
              </Box>
            )}
          </Box>
        ))}
      </Paper>

      {/* Stats Footer */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Box display="flex" justifyContent="space-between" flexWrap="wrap" gap={2}>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Total Events
            </Typography>
            <Typography variant="h6">{logs.length}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Status
            </Typography>
            <Typography variant="h6" color={isPaused ? 'warning.main' : 'success.main'}>
              {isPaused ? 'PAUSED' : 'ACTIVE'}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Player Events
            </Typography>
            <Typography variant="h6" sx={{ color: getLogColor({ type: 'player' } as LogEntry) }}>
              {logs.filter((l) => l.type === 'player').length}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Card Events
            </Typography>
            <Typography variant="h6" sx={{ color: getLogColor({ type: 'card' } as LogEntry) }}>
              {logs.filter((l) => l.type === 'card').length}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Pot Events
            </Typography>
            <Typography variant="h6" sx={{ color: getLogColor({ type: 'pot' } as LogEntry) }}>
              {logs.filter((l) => l.type === 'pot').length}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Action Events
            </Typography>
            <Typography variant="h6" sx={{ color: getLogColor({ type: 'action' } as LogEntry) }}>
              {logs.filter((l) => l.type === 'action').length}
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};
