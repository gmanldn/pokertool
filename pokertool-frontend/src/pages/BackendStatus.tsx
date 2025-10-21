import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Paper, LinearProgress, Chip, Card, CardContent } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import { buildApiUrl } from '../config/api';

interface StartupStep {
  number: number;
  name: string;
  description: string;
  status: 'in_progress' | 'success' | 'failed';
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
  steps_remaining: number;
  is_complete: boolean;
  steps: StartupStep[];
}

const BackendStatus: React.FC = () => {
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
        return <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />;
      case 'failed':
        return <ErrorIcon sx={{ color: 'error.main', fontSize: 20 }} />;
      case 'in_progress':
        return <HourglassEmptyIcon sx={{ color: 'warning.main', fontSize: 20 }} />;
      default:
        return null;
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
      default:
        return 'default';
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
        Backend Status
      </Typography>

      {status && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Startup Progress
              </Typography>
              <Chip
                label={status.is_complete ? 'Complete' : 'Starting...'}
                color={status.is_complete ? 'success' : 'warning'}
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
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip label={`✓ ${status.steps_completed} Completed`} color="success" size="small" variant="outlined" />
              <Chip label={`⏳ ${status.steps_in_progress} In Progress`} color="warning" size="small" variant="outlined" />
              <Chip label={`✗ ${status.steps_failed} Failed`} color="error" size="small" variant="outlined" />
              <Chip label={`⋯ ${status.steps_remaining} Remaining`} color="default" size="small" variant="outlined" />
            </Box>
          </CardContent>
        </Card>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Startup Steps
          </Typography>
          <Box sx={{ maxHeight: '300px', overflow: 'auto' }}>
            {status?.steps.map((step, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 1,
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <Box sx={{ mr: 2 }}>{getStepIcon(step.status)}</Box>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body2" fontWeight="medium">
                    #{step.number} {step.name}
                  </Typography>
                  {step.description && (
                    <Typography variant="caption" color="text.secondary">
                      {step.description}
                    </Typography>
                  )}
                </Box>
                {step.duration !== undefined && (
                  <Chip
                    label={formatDuration(step.duration)}
                    size="small"
                    color={getStatusColor(step.status) as any}
                    variant="outlined"
                  />
                )}
              </Box>
            ))}
          </Box>
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
