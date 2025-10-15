/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/EquityCalculator.tsx
version: v81.0.0
last_commit: '2025-10-15T16:09:30Z'
fixes:
- date: '2025-10-15'
  summary: Created Equity Calculator for real-time equity display
---
POKERTOOL-HEADER-END */

import React from 'react';
import { Box, Typography, LinearProgress, useTheme, Paper, Divider } from '@mui/material';
import { TrendingUp, EmojiEvents } from '@mui/icons-material';

interface EquityCalculatorProps {
  winEquity: number; // 0-100
  tieEquity: number; // 0-100
  ev: number; // Expected value in dollars
  potOdds: number; // 0-100
  requiredEquity?: number; // 0-100
  compact?: boolean;
}

export const EquityCalculator: React.FC<EquityCalculatorProps> = ({
  winEquity,
  tieEquity,
  ev,
  potOdds,
  requiredEquity,
  compact = false,
}) => {
  const theme = useTheme();
  const loseEquity = 100 - winEquity - tieEquity;

  const formatPercentage = (value: number): string => `${value.toFixed(1)}%`;
  const formatCurrency = (value: number): string => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}$${Math.abs(value).toFixed(2)}`;
  };

  const getEVColor = (value: number): string => {
    if (value > 10) return theme.palette.success.main;
    if (value > 0) return theme.palette.success.light;
    if (value > -10) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const isPositiveEV = ev > 0;
  const meetsRequiredEquity = requiredEquity ? winEquity >= requiredEquity : true;

  return (
    <Paper
      sx={{
        p: compact ? 1.5 : 2,
        background: theme.palette.mode === 'dark'
          ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
          : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
        border: `1px solid ${isPositiveEV ? theme.palette.success.main : theme.palette.error.main}40`,
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant={compact ? 'subtitle2' : 'h6'} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TrendingUp />
          Equity Analysis
        </Typography>
        <Box
          sx={{
            px: 1.5,
            py: 0.5,
            borderRadius: 1,
            background: `${getEVColor(ev)}20`,
            border: `1px solid ${getEVColor(ev)}`,
          }}
        >
          <Typography
            variant={compact ? 'caption' : 'body2'}
            sx={{
              fontWeight: 'bold',
              color: getEVColor(ev),
            }}
          >
            EV: {formatCurrency(ev)}
          </Typography>
        </Box>
      </Box>

      {/* Equity Breakdown Bar */}
      <Box sx={{ mb: 2 }}>
        <Box
          sx={{
            display: 'flex',
            height: compact ? 32 : 40,
            borderRadius: 2,
            overflow: 'hidden',
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          }}
        >
          {/* Win */}
          <Box
            sx={{
              width: `${winEquity}%`,
              background: 'linear-gradient(180deg, #4caf50 0%, #2e7d32 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'width 0.5s ease',
              position: 'relative',
              '&:hover': {
                filter: 'brightness(1.1)',
              },
            }}
          >
            {winEquity > 15 && (
              <Typography
                variant="caption"
                sx={{ color: 'white', fontWeight: 'bold', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
              >
                {formatPercentage(winEquity)}
              </Typography>
            )}
          </Box>

          {/* Tie */}
          {tieEquity > 0 && (
            <Box
              sx={{
                width: `${tieEquity}%`,
                background: 'linear-gradient(180deg, #ffc107 0%, #f57c00 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'width 0.5s ease',
                '&:hover': {
                  filter: 'brightness(1.1)',
                },
              }}
            >
              {tieEquity > 5 && (
                <Typography
                  variant="caption"
                  sx={{ color: 'white', fontWeight: 'bold', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
                >
                  {formatPercentage(tieEquity)}
                </Typography>
              )}
            </Box>
          )}

          {/* Lose */}
          <Box
            sx={{
              width: `${loseEquity}%`,
              background: 'linear-gradient(180deg, #f44336 0%, #c62828 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'width 0.5s ease',
              '&:hover': {
                filter: 'brightness(1.1)',
              },
            }}
          >
            {loseEquity > 15 && (
              <Typography
                variant="caption"
                sx={{ color: 'white', fontWeight: 'bold', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
              >
                {formatPercentage(loseEquity)}
              </Typography>
            )}
          </Box>
        </Box>

        {/* Labels */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
          <Typography variant="caption" sx={{ color: theme.palette.success.main, fontWeight: 'bold' }}>
            Win
          </Typography>
          {tieEquity > 0 && (
            <Typography variant="caption" sx={{ color: theme.palette.warning.main, fontWeight: 'bold' }}>
              Tie
            </Typography>
          )}
          <Typography variant="caption" sx={{ color: theme.palette.error.main, fontWeight: 'bold' }}>
            Lose
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ my: 1.5 }} />

      {/* Metrics Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: compact ? '1fr 1fr' : 'repeat(2, 1fr)',
          gap: 1.5,
        }}
      >
        {/* Pot Odds */}
        <Box>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
            Pot Odds
          </Typography>
          <Typography variant={compact ? 'body2' : 'h6'} fontWeight="bold" color="primary">
            {formatPercentage(potOdds)}
          </Typography>
        </Box>

        {/* Win Probability */}
        <Box>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
            Win Probability
          </Typography>
          <Typography variant={compact ? 'body2' : 'h6'} fontWeight="bold" color="success.main">
            {formatPercentage(winEquity)}
          </Typography>
        </Box>

        {/* Required Equity (if provided) */}
        {requiredEquity !== undefined && (
          <>
            <Box>
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
                Required Equity
              </Typography>
              <Typography variant={compact ? 'body2' : 'h6'} fontWeight="bold">
                {formatPercentage(requiredEquity)}
              </Typography>
            </Box>

            <Box>
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
                Status
              </Typography>
              <Typography
                variant={compact ? 'body2' : 'h6'}
                fontWeight="bold"
                color={meetsRequiredEquity ? 'success.main' : 'error.main'}
              >
                {meetsRequiredEquity ? '✓ Profitable' : '✗ Unprofitable'}
              </Typography>
            </Box>
          </>
        )}
      </Box>

      {/* Decision Recommendation */}
      {!compact && (
        <Box
          sx={{
            mt: 2,
            p: 1.5,
            borderRadius: 1,
            background: isPositiveEV
              ? `${theme.palette.success.main}20`
              : `${theme.palette.error.main}20`,
            border: `1px solid ${isPositiveEV ? theme.palette.success.main : theme.palette.error.main}`,
          }}
        >
          <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {isPositiveEV ? <EmojiEvents fontSize="small" /> : '⚠️'}
            {isPositiveEV
              ? 'Positive EV situation - Recommended to continue'
              : 'Negative EV situation - Consider folding'}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default EquityCalculator;
