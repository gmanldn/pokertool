/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/SessionClock.tsx
version: v86.1.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created real-time session clock with auto-pause detection
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Chip,
  Paper,
  Tooltip,
  IconButton,
  useTheme,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  AccessTime,
  Timer,
} from '@mui/icons-material';

interface SessionClockProps {
  /** Inactivity threshold in seconds before auto-pause (default: 300 = 5 minutes) */
  inactivityThreshold?: number;
  /** Callback when session clock updates */
  onTimeUpdate?: (totalSeconds: number, activeSeconds: number) => void;
  /** Compact mode for mobile displays */
  compact?: boolean;
}

interface SessionState {
  startTime: number | null;
  totalElapsed: number;
  activeElapsed: number;
  isPaused: boolean;
  lastActivity: number;
  breaks: Array<{ start: number; end?: number }>;
}

export const SessionClock: React.FC<SessionClockProps> = ({
  inactivityThreshold = 300,
  onTimeUpdate,
  compact = false,
}) => {
  const theme = useTheme();
  const [sessionState, setSessionState] = useState<SessionState>({
    startTime: null,
    totalElapsed: 0,
    activeElapsed: 0,
    isPaused: false,
    lastActivity: Date.now(),
    breaks: [],
  });

  const [currentTime, setCurrentTime] = useState(Date.now());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Format seconds to HH:MM:SS
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Start session
  const startSession = () => {
    const now = Date.now();
    setSessionState(prev => ({
      ...prev,
      startTime: prev.startTime || now,
      isPaused: false,
      lastActivity: now,
    }));
  };

  // Pause session
  const pauseSession = () => {
    const now = Date.now();
    setSessionState(prev => ({
      ...prev,
      isPaused: true,
      breaks: [...prev.breaks, { start: now }],
    }));
  };

  // Resume session
  const resumeSession = () => {
    const now = Date.now();
    setSessionState(prev => {
      const updatedBreaks = [...prev.breaks];
      if (updatedBreaks.length > 0 && !updatedBreaks[updatedBreaks.length - 1].end) {
        updatedBreaks[updatedBreaks.length - 1].end = now;
      }
      return {
        ...prev,
        isPaused: false,
        lastActivity: now,
        breaks: updatedBreaks,
      };
    });
  };

  // Stop session
  const stopSession = () => {
    setSessionState({
      startTime: null,
      totalElapsed: 0,
      activeElapsed: 0,
      isPaused: false,
      lastActivity: Date.now(),
      breaks: [],
    });
  };

  // Update clock every second
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Calculate elapsed time and check for inactivity
  useEffect(() => {
    if (!sessionState.startTime) return;

    const now = currentTime;
    const totalSeconds = Math.floor((now - sessionState.startTime) / 1000);

    // Calculate total break time
    let breakTime = 0;
    sessionState.breaks.forEach(brk => {
      const end = brk.end || now;
      breakTime += end - brk.start;
    });

    const activeSeconds = Math.floor((totalSeconds * 1000 - breakTime) / 1000);

    // Auto-pause detection
    const timeSinceActivity = (now - sessionState.lastActivity) / 1000;
    if (!sessionState.isPaused && timeSinceActivity > inactivityThreshold) {
      pauseSession();
    }

    setSessionState(prev => ({
      ...prev,
      totalElapsed: totalSeconds,
      activeElapsed: Math.max(0, activeSeconds),
    }));

    if (onTimeUpdate) {
      onTimeUpdate(totalSeconds, Math.max(0, activeSeconds));
    }
  }, [currentTime, sessionState.startTime, sessionState.lastActivity, sessionState.isPaused, inactivityThreshold, onTimeUpdate]);

  // Register activity to prevent auto-pause
  useEffect(() => {
    const handleActivity = () => {
      if (sessionState.startTime && !sessionState.isPaused) {
        setSessionState(prev => ({
          ...prev,
          lastActivity: Date.now(),
        }));
      }
    };

    // Listen for user activity events
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keypress', handleActivity);
    window.addEventListener('click', handleActivity);

    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keypress', handleActivity);
      window.removeEventListener('click', handleActivity);
    };
  }, [sessionState.startTime, sessionState.isPaused]);

  // Auto-start session on component mount
  useEffect(() => {
    if (!sessionState.startTime) {
      startSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isActive = sessionState.startTime && !sessionState.isPaused;
  const statusColor = isActive ? theme.palette.success.main : theme.palette.warning.main;
  const statusText = isActive ? 'Active' : 'Paused';

  const totalTimeFormatted = formatTime(sessionState.totalElapsed);
  const activeTimeFormatted = formatTime(sessionState.activeElapsed);

  if (compact) {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        <AccessTime sx={{ fontSize: 20, color: statusColor }} />
        <Typography variant="body1" fontWeight="bold">
          {activeTimeFormatted}
        </Typography>
        <Chip
          label={statusText}
          size="small"
          sx={{
            backgroundColor: `${statusColor}22`,
            color: statusColor,
            fontWeight: 'bold',
          }}
        />
      </Box>
    );
  }

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        background:
          theme.palette.mode === 'dark'
            ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
            : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
        borderLeft: `4px solid ${statusColor}`,
      }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            Session Time
          </Typography>

          {/* Active Time - Main Display */}
          <Box display="flex" alignItems="baseline" gap={1} mb={1}>
            <Typography
              variant="h3"
              fontWeight="bold"
              sx={{
                fontFamily: 'monospace',
                color: statusColor,
                animation: isActive ? 'pulse 2s ease-in-out infinite' : 'none',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.8 },
                },
              }}
            >
              {activeTimeFormatted}
            </Typography>
            <Chip
              icon={isActive ? <Timer /> : <Pause />}
              label={statusText}
              size="small"
              sx={{
                backgroundColor: `${statusColor}22`,
                color: statusColor,
                fontWeight: 'bold',
              }}
            />
          </Box>

          {/* Total Time vs Active Time */}
          <Box display="flex" gap={3} mt={2}>
            <Tooltip title="Total time including breaks">
              <Box>
                <Typography variant="caption" color="textSecondary" display="block">
                  Total Time
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {totalTimeFormatted}
                </Typography>
              </Box>
            </Tooltip>

            <Tooltip title="Active playing time (excludes breaks)">
              <Box>
                <Typography variant="caption" color="textSecondary" display="block">
                  Active Time
                </Typography>
                <Typography variant="body2" fontWeight="medium" color={statusColor}>
                  {activeTimeFormatted}
                </Typography>
              </Box>
            </Tooltip>

            {sessionState.breaks.length > 0 && (
              <Tooltip title="Number of breaks taken">
                <Box>
                  <Typography variant="caption" color="textSecondary" display="block">
                    Breaks
                  </Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {sessionState.breaks.length}
                  </Typography>
                </Box>
              </Tooltip>
            )}
          </Box>

          {/* Session Start Time */}
          {sessionState.startTime && (
            <Typography variant="caption" color="textSecondary" mt={2} display="block">
              Started: {new Date(sessionState.startTime).toLocaleTimeString()}
            </Typography>
          )}
        </Box>

        {/* Control Buttons */}
        <Box display="flex" gap={1}>
          {isActive ? (
            <Tooltip title="Pause session">
              <IconButton size="small" onClick={pauseSession} color="warning">
                <Pause />
              </IconButton>
            </Tooltip>
          ) : (
            <Tooltip title="Resume session">
              <IconButton size="small" onClick={resumeSession} color="success">
                <PlayArrow />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="End session">
            <IconButton size="small" onClick={stopSession} color="error">
              <Stop />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Auto-pause warning */}
      {!isActive && sessionState.startTime && (
        <Box
          mt={2}
          p={1}
          sx={{
            backgroundColor: `${theme.palette.warning.main}22`,
            borderRadius: 1,
          }}
        >
          <Typography variant="caption" color="warning.main">
            ⚠️ Session paused due to inactivity ({Math.floor(inactivityThreshold / 60)} minutes)
          </Typography>
        </Box>
      )}
    </Paper>
  );
};
