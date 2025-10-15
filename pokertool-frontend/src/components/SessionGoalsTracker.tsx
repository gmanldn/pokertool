/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/SessionGoalsTracker.tsx
version: v81.0.0
last_commit: '2025-10-15T16:11:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Session Goals Tracker for session management
---
POKERTOOL-HEADER-END */

import React from 'react';
import { Box, Typography, LinearProgress, Paper, Grid, useTheme, Chip } from '@mui/material';
import { EmojiEvents, Timer, Casino, TrendingUp } from '@mui/icons-material';

interface SessionGoal {
  label: string;
  current: number;
  target: number;
  unit: string;
  icon: React.ReactNode;
  color: string;
}

interface SessionGoalsTrackerProps {
  goals?: SessionGoal[];
  compact?: boolean;
}

const DEFAULT_GOALS: SessionGoal[] = [
  {
    label: 'Hands Played',
    current: 125,
    target: 200,
    unit: 'hands',
    icon: <Casino />,
    color: '#2196f3',
  },
  {
    label: 'Profit Target',
    current: 180,
    target: 250,
    unit: '$',
    icon: <TrendingUp />,
    color: '#4caf50',
  },
  {
    label: 'Session Time',
    current: 75,
    target: 120,
    unit: 'min',
    icon: <Timer />,
    color: '#ff9800',
  },
];

export const SessionGoalsTracker: React.FC<SessionGoalsTrackerProps> = ({
  goals = DEFAULT_GOALS,
  compact = false,
}) => {
  const theme = useTheme();

  const getProgressPercentage = (current: number, target: number): number => {
    return Math.min((current / target) * 100, 100);
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 100) return theme.palette.success.main;
    if (percentage >= 75) return theme.palette.info.main;
    if (percentage >= 50) return theme.palette.warning.main;
    return theme.palette.error.light;
  };

  const formatValue = (value: number, unit: string): string => {
    if (unit === '$') return `$${value.toFixed(0)}`;
    if (unit === 'min') {
      const hours = Math.floor(value / 60);
      const mins = value % 60;
      return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    }
    return `${value}`;
  };

  const overallProgress =
    goals.reduce((acc, goal) => acc + getProgressPercentage(goal.current, goal.target), 0) / goals.length;

  return (
    <Paper
      sx={{
        p: compact ? 2 : 3,
        background: theme.palette.mode === 'dark'
          ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
          : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
        border: `1px solid ${getProgressColor(overallProgress)}40`,
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant={compact ? 'h6' : 'h5'} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmojiEvents sx={{ color: getProgressColor(overallProgress) }} />
          Session Goals
        </Typography>
        <Chip
          label={`${overallProgress.toFixed(0)}%`}
          sx={{
            background: `${getProgressColor(overallProgress)}20`,
            color: getProgressColor(overallProgress),
            fontWeight: 'bold',
            fontSize: compact ? '0.8rem' : '0.9rem',
          }}
        />
      </Box>

      {/* Overall Progress Bar */}
      {!compact && (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2" color="textSecondary">
              Overall Progress
            </Typography>
            <Typography variant="subtitle2" fontWeight="bold" sx={{ color: getProgressColor(overallProgress) }}>
              {overallProgress.toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={overallProgress}
            sx={{
              height: 10,
              borderRadius: 5,
              backgroundColor: theme.palette.mode === 'dark'
                ? 'rgba(255, 255, 255, 0.1)'
                : 'rgba(0, 0, 0, 0.1)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 5,
                backgroundColor: getProgressColor(overallProgress),
                backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.15) 75%, transparent 75%, transparent)',
                backgroundSize: '20px 20px',
                animation: 'moveStripes 1s linear infinite',
              },
            }}
          />
        </Box>
      )}

      {/* Individual Goals */}
      <Grid container spacing={compact ? 2 : 3}>
        {goals.map((goal, index) => {
          const progress = getProgressPercentage(goal.current, goal.target);
          const progressColor = getProgressColor(progress);
          const isComplete = progress >= 100;

          return (
            <Grid item xs={12} sm={compact ? 12 : 6} md={compact ? 6 : 4} key={index}>
              <Box
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: theme.palette.mode === 'dark'
                    ? 'rgba(255, 255, 255, 0.05)'
                    : 'rgba(0, 0, 0, 0.03)',
                  border: `1px solid ${isComplete ? theme.palette.success.main : 'transparent'}`,
                  transition: 'all 0.3s ease',
                  position: 'relative',
                  overflow: 'hidden',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 4px 12px ${goal.color}30`,
                  },
                }}
              >
                {/* Background Icon */}
                <Box
                  sx={{
                    position: 'absolute',
                    top: -10,
                    right: -10,
                    opacity: 0.1,
                    fontSize: 80,
                    color: goal.color,
                  }}
                >
                  {goal.icon}
                </Box>

                {/* Content */}
                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                    <Box
                      sx={{
                        p: 0.8,
                        borderRadius: 1.5,
                        background: `${goal.color}20`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {React.cloneElement(goal.icon as React.ReactElement, {
                        sx: { fontSize: 20, color: goal.color },
                      })}
                    </Box>
                    <Typography variant="subtitle2" fontWeight="bold">
                      {goal.label}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', mb: 0.5 }}>
                      <Typography variant="h5" fontWeight="bold" sx={{ color: goal.color }}>
                        {formatValue(goal.current, goal.unit)}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        / {formatValue(goal.target, goal.unit)}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={progress}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: theme.palette.mode === 'dark'
                          ? 'rgba(255, 255, 255, 0.1)'
                          : 'rgba(0, 0, 0, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          backgroundColor: progressColor,
                          transition: 'transform 0.5s ease',
                        },
                      }}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" color="textSecondary">
                      {progress.toFixed(0)}% Complete
                    </Typography>
                    {isComplete && (
                      <Chip
                        label="✓ Done"
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.7rem',
                          background: theme.palette.success.main,
                          color: 'white',
                          fontWeight: 'bold',
                        }}
                      />
                    )}
                  </Box>
                </Box>
              </Box>
            </Grid>
          );
        })}
      </Grid>

      {/* Motivational Message */}
      {!compact && overallProgress < 100 && (
        <Box
          sx={{
            mt: 3,
            p: 2,
            borderRadius: 2,
            background: `${theme.palette.primary.main}10`,
            border: `1px solid ${theme.palette.primary.main}30`,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" color="textSecondary">
            {overallProgress >= 75 && "You're almost there! Keep pushing! 💪"}
            {overallProgress >= 50 && overallProgress < 75 && "Great progress! Stay focused! 🎯"}
            {overallProgress >= 25 && overallProgress < 50 && "Keep grinding! You're doing well! 🔥"}
            {overallProgress < 25 && "Just getting started! Let's do this! 🚀"}
          </Typography>
        </Box>
      )}

      <style>
        {`
          @keyframes moveStripes {
            0% {
              background-position: 0 0;
            }
            100% {
              background-position: 20px 0;
            }
          }
        `}
      </style>
    </Paper>
  );
};

export default SessionGoalsTracker;
