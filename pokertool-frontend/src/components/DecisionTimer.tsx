/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/DecisionTimer.tsx
version: v81.0.0
last_commit: '2025-10-15T16:08:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Quick Decision Timer component for time management
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Typography, useTheme } from '@mui/material';
import { AccessTime } from '@mui/icons-material';

interface DecisionTimerProps {
  timeLimit?: number; // in seconds
  onTimeExpired?: () => void;
  showWarning?: boolean;
  compact?: boolean;
}

export const DecisionTimer: React.FC<DecisionTimerProps> = ({
  timeLimit = 30,
  onTimeExpired,
  showWarning = true,
  compact = false,
}) => {
  const theme = useTheme();
  const [timeLeft, setTimeLeft] = useState(timeLimit);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setIsActive(false);
          onTimeExpired?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, onTimeExpired]);

  const getTimerColor = () => {
    const percentage = (timeLeft / timeLimit) * 100;
    if (percentage > 50) return theme.palette.success.main;
    if (percentage > 25) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getUrgencyLevel = () => {
    const percentage = (timeLeft / timeLimit) * 100;
    if (percentage > 50) return 'normal';
    if (percentage > 25) return 'warning';
    return 'critical';
  };

  const urgency = getUrgencyLevel();
  const color = getTimerColor();
  const progress = (timeLeft / timeLimit) * 100;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: compact ? 1 : 2,
        p: compact ? 1 : 2,
        background:
          urgency === 'critical'
            ? 'rgba(244, 67, 54, 0.1)'
            : urgency === 'warning'
            ? 'rgba(255, 152, 0, 0.1)'
            : 'transparent',
        borderRadius: 2,
        border: urgency === 'critical' ? `2px solid ${theme.palette.error.main}` : 'none',
        transition: 'all 0.3s ease',
        animation: urgency === 'critical' ? 'pulse 1s infinite' : 'none',
        '@keyframes pulse': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.7 },
        },
      }}
    >
      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress
          variant="determinate"
          value={progress}
          size={compact ? 40 : 60}
          thickness={compact ? 4 : 5}
          sx={{
            color: color,
            transition: 'color 0.3s ease',
          }}
        />
        <Box
          sx={{
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            position: 'absolute',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography
            variant={compact ? 'body2' : 'h6'}
            component="div"
            sx={{
              fontWeight: 'bold',
              color: color,
            }}
          >
            {timeLeft}
          </Typography>
        </Box>
      </Box>

      {!compact && (
        <Box>
          <Typography variant="subtitle2" color="textSecondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <AccessTime fontSize="small" />
            Time to Act
          </Typography>
          {showWarning && urgency !== 'normal' && (
            <Typography
              variant="caption"
              sx={{
                color: urgency === 'critical' ? theme.palette.error.main : theme.palette.warning.main,
                fontWeight: 'bold',
              }}
            >
              {urgency === 'critical' ? '⚠️ Act now!' : '⏰ Hurry up!'}
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default DecisionTimer;
