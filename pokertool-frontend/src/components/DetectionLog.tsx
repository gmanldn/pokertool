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
} from '@mui/material';
import { Clear, GetApp, FilterList } from '@mui/icons-material';
import { DetectionMessage, DetectionLogData } from '../types/common';
import { buildApiUrl, httpToWs } from '../config/api';

interface DetectionLogProps {
  messages?: DetectionMessage[];
}

interface LogEntry {
  timestamp: string;
  type: 'player' | 'card' | 'pot' | 'action' | 'system' | 'error';
  severity: 'info' | 'success' | 'warning' | 'error';
  message: string;
  data?: DetectionLogData;
}

export const DetectionLog: React.FC<DetectionLogProps> = ({ messages = [] }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const logContainerRef = useRef<HTMLDivElement>(null);

  const detectionEndpoint = React.useMemo(() => httpToWs(buildApiUrl('/ws/detections')), []);
  const fallbackEndpoint = React.useMemo(() => {
    if (detectionEndpoint.includes('localhost')) {
      return detectionEndpoint.replace('localhost', '127.0.0.1');
    }
    return null;
  }, [detectionEndpoint]);

  const [logs, setLogs] = useState<LogEntry[]>([
    {
      timestamp: new Date().toISOString(),
      type: 'system',
      severity: 'info',
      message: 'Detection system initializing - connecting to backend...',
      data: {
        version: '84.0.0',
        endpoint: detectionEndpoint,
        status: 'Attempting to connect...'
      },
    },
  ]);

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

  // Connect to WebSocket for real detection events with retry logic
  useEffect(() => {

    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;
    let hasShownError = false;
    let isCleaningUp = false;
    let attemptedFallback = false;

    const connect = (endpoint: string) => {
      if (isCleaningUp) return;

      try {
        ws = new WebSocket(endpoint);

        ws.onopen = () => {
          console.log('Detection WebSocket connected');
          hasShownError = false;
          setLogs((prev) => [
            ...prev,
            {
              timestamp: new Date().toISOString(),
              type: 'system' as const,
              severity: 'success' as const,
              message: 'Connected to detection backend',
              data: { endpoint },
            },
          ].slice(-100));
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
          if (!attemptedFallback && fallbackEndpoint && endpoint !== fallbackEndpoint) {
            attemptedFallback = true;
            setLogs((prev) => [
              ...prev,
              {
                timestamp: new Date().toISOString(),
                type: 'system' as const,
                severity: 'warning' as const,
                message: `Primary endpoint unavailable, retrying via ${fallbackEndpoint}`,
              },
            ].slice(-100));
            if (ws) {
              try {
                ws.close();
              } catch (closeErr) {
                console.debug('Error closing failed WebSocket:', closeErr);
              }
            }
            reconnectTimeout = setTimeout(() => connect(fallbackEndpoint), 500);
            return;
          }

          if (!hasShownError) {
            hasShownError = true;
            setLogs((prev) => [
              ...prev,
              {
                timestamp: new Date().toISOString(),
                type: 'system' as const,
                severity: 'warning' as const,
                message: `Waiting for backend API at ${endpoint}`,
                data: {
                  status: 'Retrying in 10 seconds...',
                  possibleCauses: [
                    'Backend is still starting up',
                    'Check that start.py is running',
                    'Port 5001 may be in use by another process'
                  ]
                },
              },
            ].slice(-100));
          }
        };

        ws.onclose = () => {
          console.log('Detection WebSocket closed');
          if (!isCleaningUp) {
            // Reconnect after 10 seconds
            reconnectTimeout = setTimeout(() => connect(endpoint), 10000);
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        if (!hasShownError && !isCleaningUp) {
          hasShownError = true;
          setLogs((prev) => [
            ...prev,
            {
              timestamp: new Date().toISOString(),
              type: 'system' as const,
              severity: 'warning' as const,
              message: `Waiting for backend API at ${endpoint}`,
              data: {
                status: 'Retrying in 10 seconds...',
                error: String(error),
                possibleCauses: [
                  'Backend is still starting up',
                  'Check that start.py is running',
                  'Port 5001 may be in use by another process'
                ]
              },
            },
          ].slice(-100));
          reconnectTimeout = setTimeout(() => connect(endpoint), 10000);
        }
      }
    };

    connect(detectionEndpoint);

    return () => {
      isCleaningUp = true;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [detectionEndpoint, fallbackEndpoint]);

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
