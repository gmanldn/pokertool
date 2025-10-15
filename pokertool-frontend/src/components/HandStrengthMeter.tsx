/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/HandStrengthMeter.tsx
version: v81.0.0
last_commit: '2025-10-15T16:09:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Hand Strength Meter for visual hand strength assessment
---
POKERTOOL-HEADER-END */

import React from 'react';
import { Box, Typography, LinearProgress, useTheme, Tooltip } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface HandStrengthMeterProps {
  strength: number; // 0-100
  label?: string;
  showPercentile?: boolean;
  compact?: boolean;
  animated?: boolean;
}

export const HandStrengthMeter: React.FC<HandStrengthMeterProps> = ({
  strength,
  label = 'Hand Strength',
  showPercentile = true,
  compact = false,
  animated = true,
}) => {
  const theme = useTheme();

  const getStrengthColor = (value: number): string => {
    if (value >= 80) return '#4caf50'; // Strong
    if (value >= 60) return '#8bc34a'; // Good
    if (value >= 40) return '#ffc107'; // Medium
    if (value >= 20) return '#ff9800'; // Weak
    return '#f44336'; // Very Weak
  };

  const getStrengthLabel = (value: number): string => {
    if (value >= 80) return 'Premium';
    if (value >= 60) return 'Strong';
    if (value >= 40) return 'Medium';
    if (value >= 20) return 'Weak';
    return 'Very Weak';
  };

  const getStrengthIcon = (value: number) => {
    if (value >= 50) {
      return <TrendingUp fontSize="small" sx={{ color: getStrengthColor(value) }} />;
    }
    return <TrendingDown fontSize="small" sx={{ color: getStrengthColor(value) }} />;
  };

  const color = getStrengthColor(strength);
  const strengthLabel = getStrengthLabel(strength);

  return (
    <Box
      sx={{
        p: compact ? 1 : 2,
        background: theme.palette.mode === 'dark' 
          ? 'rgba(255, 255, 255, 0.05)' 
          : 'rgba(0, 0, 0, 0.03)',
        borderRadius: 2,
        border: `1px solid ${color}40`,
        transition: 'all 0.3s ease',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography
          variant={compact ? 'caption' : 'subtitle2'}
          color="textSecondary"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          {getStrengthIcon(strength)}
          {label}
        </Typography>
        <Tooltip title={`${strengthLabel} - ${strength}th percentile`} arrow>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography
              variant={compact ? 'body2' : 'subtitle1'}
              sx={{
                fontWeight: 'bold',
                color: color,
              }}
            >
              {strengthLabel}
            </Typography>
            {showPercentile && (
              <Typography
                variant="caption"
                sx={{
                  color: 'textSecondary',
                  fontWeight: 'bold',
                }}
              >
                ({strength}%)
              </Typography>
            )}
          </Box>
        </Tooltip>
      </Box>

      <Box sx={{ position: 'relative' }}>
        <LinearProgress
          variant="determinate"
          value={strength}
          sx={{
            height: compact ? 8 : 12,
            borderRadius: 6,
            backgroundColor: theme.palette.mode === 'dark'
              ? 'rgba(255, 255, 255, 0.1)'
              : 'rgba(0, 0, 0, 0.1)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: color,
              borderRadius: 6,
              transition: animated ? 'transform 0.5s ease, background-color 0.3s ease' : 'none',
              backgroundImage: `linear-gradient(
                45deg,
                rgba(255, 255, 255, 0.15) 25%,
                transparent 25%,
                transparent 50%,
                rgba(255, 255, 255, 0.15) 50%,
                rgba(255, 255, 255, 0.15) 75%,
                transparent 75%,
                transparent
              )`,
              backgroundSize: '20px 20px',
              animation: animated ? 'moveStripes 1s linear infinite' : 'none',
            },
          }}
        />
        
        {/* Strength zones overlay */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            pointerEvents: 'none',
          }}
        >
          {[20, 40, 60, 80].map((threshold) => (
            <Box
              key={threshold}
              sx={{
                position: 'absolute',
                left: `${threshold}%`,
                top: 0,
                bottom: 0,
                width: '1px',
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
              }}
            />
          ))}
        </Box>
      </Box>

      {/* Strength description */}
      {!compact && (
        <Typography
          variant="caption"
          color="textSecondary"
          sx={{ mt: 1, display: 'block', fontSize: '0.7rem' }}
        >
          {strength >= 80 && 'Top tier hand - Strong value betting opportunity'}
          {strength >= 60 && strength < 80 && 'Above average - Good continuation potential'}
          {strength >= 40 && strength < 60 && 'Marginal hand - Play cautiously'}
          {strength >= 20 && strength < 40 && 'Below average - Consider folding to aggression'}
          {strength < 20 && 'Weak hand - Fold unless specific circumstances'}
        </Typography>
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
    </Box>
  );
};

export default HandStrengthMeter;
