import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Paper, LinearProgress, Chip, Card, CardContent, Alert, List, ListItem, ListItemIcon, ListItemText, useTheme } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import PlayCircleOutlineIcon from '@mui/icons-material/PlayCircleOutline';
import { buildApiUrl } from '../config/api';

interface StartupStep {
  number: number;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'success' | 'failed';
  start_time?: number;
  end_time?: number;
  duration?: number;
}

interface StartupStatus {
  elapsed_time: number;
  current_step: number;
  total_steps: number;
  steps_completed: number;
  steps_in_progress: number;
  steps_failed: number;
  steps_pending?: number;
  steps_remaining: number;
  is_complete: boolean;
  steps: StartupStep[];
}

const BackendStatus: React.FC = () => {
  const theme = useTheme();
  const [status, setStatus] = useState<StartupStatus | null>(null);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logLines]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(buildApiUrl('/api/backend/startup/status'));
        const data = await response.json();
        setStatus(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch backend status');
      }
    };

    const fetchLog = async () => {
      try {
        const response = await fetch(buildApiUrl('/api/backend/startup/log?lines=100'));
        const data = await response.json();
        setLogLines(data.log_lines || []);
      } catch (err) {
        // Silently fail for log fetch
      }
    };

    // Initial fetch
    fetchStatus();
    fetchLog();

    // Poll every 2 seconds
    const statusInterval = setInterval(fetchStatus, 2000);
    const logInterval = setInterval(fetchLog, 2000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(logInterval);
    };
  }, []);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(0);
    return `${mins}m ${secs}s`;
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon sx={{ color: 'success.main', fontSize: 24 }} />;
      case 'failed':
        return <ErrorIcon sx={{ color: 'error.main', fontSize: 24 }} />;
      case 'in_progress':
        return <PlayCircleOutlineIcon sx={{ color: 'warning.main', fontSize: 24 }} />;
      case 'pending':
        return <RadioButtonUncheckedIcon sx={{ color: '#8B4513', fontSize: 24 }} />; // Brown color
      default:
        return <RadioButtonUncheckedIcon sx={{ color: 'text.disabled', fontSize: 24 }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'warning';
      case 'pending':
        return 'default';
      default:
        return 'default';
    }
  };

  const getBackgroundColor = (status: string, theme: any) => {
    switch (status) {
      case 'success':
        return theme.palette.mode === 'dark' ? '#1B5E20' : '#E8F5E9'; // Dark/light green
      case 'failed':
        return theme.palette.mode === 'dark' ? '#B71C1C' : '#FFEBEE'; // Dark/light red
      case 'in_progress':
        return theme.palette.mode === 'dark' ? '#E65100' : '#FFF3E0'; // Dark/light orange
      case 'pending':
        return theme.palette.mode === 'dark' ? '#3E2723' : '#EFEBE9'; // Dark/light brown
      default:
        return 'transparent';
    }
  };

  if (error && !status) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Backend Status
        </Typography>
        <Paper sx={{ p: 3, backgroundColor: 'error.dark' }}>
          <Typography>{error}</Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Backend Status Monitor
      </Typography>

      {/* Status Alert */}
      {status && !status.is_complete && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Backend Offline - Starting Up
          </Typography>
          <Typography variant="body2">
            The backend is currently initializing. {status.steps_remaining} task{status.steps_remaining !== 1 ? 's' : ''} remaining before backend comes online.
            {status.steps_in_progress > 0 && ` Currently working on: ${status.steps.find(s => s.status === 'in_progress')?.name || 'unknown'}`}
          </Typography>
        </Alert>
      )}

      {status && status.is_complete && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Backend Online
          </Typography>
          <Typography variant="body2">
            All {status.total_steps} startup tasks completed successfully in {formatDuration(status.elapsed_time)}.
          </Typography>
        </Alert>
      )}

      {status && status.steps_failed > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Backend Startup Failed
          </Typography>
          <Typography variant="body2">
            {status.steps_failed} task{status.steps_failed !== 1 ? 's' : ''} failed during startup. Please check the logs below for details.
          </Typography>
        </Alert>
      )}

      {status && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Startup Progress
              </Typography>
              <Chip
                label={status.is_complete ? 'Online' : status.steps_failed > 0 ? 'Failed' : 'Starting...'}
                color={status.is_complete ? 'success' : status.steps_failed > 0 ? 'error' : 'warning'}
                size="small"
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Step {status.current_step} of {status.total_steps}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Elapsed: {formatDuration(status.elapsed_time)}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={status.total_steps > 0 ? (status.steps_completed / status.total_steps) * 100 : 0}
                sx={{ height: 8, borderRadius: 1 }}
                color={status.is_complete ? 'success' : status.steps_failed > 0 ? 'error' : 'primary'}
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip label={`✓ ${status.steps_completed} Completed`} color="success" size="small" variant="outlined" />
              <Chip label={`⏳ ${status.steps_in_progress} In Progress`} color="warning" size="small" variant="outlined" />
              <Chip label={`✗ ${status.steps_failed} Failed`} color="error" size="small" variant="outlined" />
              <Chip
                label={`⋯ ${status.steps_remaining} Pending`}
                size="small"
                variant="outlined"
                sx={{ borderColor: '#8B4513', color: '#8B4513' }}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Startup Tasks Timeline
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Watch tasks turn from brown (pending) → orange (in progress) → green (complete) as the backend initializes
          </Typography>
          <List sx={{ maxHeight: '400px', overflow: 'auto' }}>
            {status?.steps.map((step, index) => (
              <ListItem
                key={index}
                sx={{
                  mb: 1,
                  borderRadius: 2,
                  backgroundColor: getBackgroundColor(step.status, theme),
                  border: step.status === 'in_progress' ? `2px solid ${theme.palette.warning.main}` : '1px solid',
                  borderColor: step.status === 'in_progress' ? theme.palette.warning.main : 'divider',
                  transition: 'all 0.5s ease-in-out',
                  boxShadow: step.status === 'in_progress' ? 2 : 0,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {getStepIcon(step.status)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1" fontWeight="bold">
                        #{step.number} {step.name}
                      </Typography>
                      {step.status === 'success' && (
                        <Chip
                          label="Done"
                          color="success"
                          size="small"
                          variant="filled"
                        />
                      )}
                      {step.status === 'in_progress' && (
                        <Chip
                          label="Working..."
                          color="warning"
                          size="small"
                          variant="filled"
                        />
                      )}
                      {step.status === 'pending' && (
                        <Chip
                          label="Waiting"
                          size="small"
                          variant="outlined"
                          sx={{ borderColor: '#8B4513', color: '#8B4513' }}
                        />
                      )}
                      {step.status === 'failed' && (
                        <Chip
                          label="Failed"
                          color="error"
                          size="small"
                          variant="filled"
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {step.description}
                      </Typography>
                      {step.duration !== undefined && (
                        <Typography variant="caption" color="text.secondary">
                          Completed in {formatDuration(step.duration)}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Startup Log
          </Typography>
          <Paper
            sx={{
              p: 2,
              backgroundColor: '#1e1e1e',
              color: '#d4d4d4',
              fontFamily: 'monospace',
              fontSize: '12px',
              maxHeight: '400px',
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {logLines.map((line, index) => (
              <div key={index}>{line}</div>
            ))}
            <div ref={logEndRef} />
          </Paper>
        </CardContent>
      </Card>
    </Box>
  );
};

export default BackendStatus;
