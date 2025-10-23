/**
 * Position Stats Card Component
 *
 * Shows player's statistics from current position
 */
import React from 'react';
import { Box, Paper, Typography, LinearProgress, Chip } from '@mui/material';
import { Place, TrendingUp, LocalFireDepartment } from '@mui/icons-material';

interface PositionStats {
  position: string;
  vpip: number;
  pfr: number;
  aggression: number;
  winRate?: number;
  handsPlayed: number;
}

interface PositionStatsCardProps {
  stats: PositionStats;
  gtoComparison?: {
    vpip: number;
    pfr: number;
    aggression: number;
  };
}

export const PositionStatsCard: React.FC<PositionStatsCardProps> = React.memo(({
  stats,
  gtoComparison
}) => {
  const getStatColor = (stat: number, optimal?: number): string => {
    if (!optimal) {
      if (stat >= 70) return '#4caf50';
      if (stat >= 50) return '#8bc34a';
      if (stat >= 30) return '#ff9800';
      return '#f44336';
    }

    const diff = Math.abs(stat - optimal);
    if (diff <= 5) return '#4caf50';
    if (diff <= 10) return '#ff9800';
    return '#f44336';
  };

  const getVariance = (stat: number, optimal?: number): string => {
    if (!optimal) return '';
    const diff = stat - optimal;
    if (Math.abs(diff) <= 2) return '✓';
    return diff > 0 ? `+${diff.toFixed(0)}` : diff.toFixed(0);
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        backgroundColor: 'rgba(33, 33, 33, 0.9)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 2
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Place sx={{ color: 'primary.main', fontSize: 24 }} />
        <Box>
          <Typography variant="subtitle1" fontWeight="bold" color="white">
            {stats.position} Statistics
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {stats.handsPlayed} hands played
          </Typography>
        </Box>
      </Box>

      {/* VPIP */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
          <Typography variant="body2" color="textSecondary">
            VPIP (Voluntarily Put $ In Pot)
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography
              variant="body1"
              fontWeight="bold"
              sx={{ color: getStatColor(stats.vpip, gtoComparison?.vpip) }}
            >
              {stats.vpip.toFixed(0)}%
            </Typography>
            {gtoComparison && (
              <Chip
                label={getVariance(stats.vpip, gtoComparison.vpip)}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '10px',
                  backgroundColor: getStatColor(stats.vpip, gtoComparison.vpip),
                  color: 'white'
                }}
              />
            )}
          </Box>
        </Box>
        <LinearProgress
          variant="determinate"
          value={Math.min(stats.vpip, 100)}
          sx={{
            height: 6,
            borderRadius: 3,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getStatColor(stats.vpip, gtoComparison?.vpip),
              borderRadius: 3
            }
          }}
        />
      </Box>

      {/* PFR */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrendingUp sx={{ fontSize: 16, color: 'textSecondary' }} />
            <Typography variant="body2" color="textSecondary">
              PFR (Preflop Raise)
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography
              variant="body1"
              fontWeight="bold"
              sx={{ color: getStatColor(stats.pfr, gtoComparison?.pfr) }}
            >
              {stats.pfr.toFixed(0)}%
            </Typography>
            {gtoComparison && (
              <Chip
                label={getVariance(stats.pfr, gtoComparison.pfr)}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '10px',
                  backgroundColor: getStatColor(stats.pfr, gtoComparison.pfr),
                  color: 'white'
                }}
              />
            )}
          </Box>
        </Box>
        <LinearProgress
          variant="determinate"
          value={Math.min(stats.pfr, 100)}
          sx={{
            height: 6,
            borderRadius: 3,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getStatColor(stats.pfr, gtoComparison?.pfr),
              borderRadius: 3
            }
          }}
        />
      </Box>

      {/* Aggression */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <LocalFireDepartment sx={{ fontSize: 16, color: 'textSecondary' }} />
            <Typography variant="body2" color="textSecondary">
              Aggression Factor
            </Typography>
          </Box>
          <Typography
            variant="body1"
            fontWeight="bold"
            sx={{ color: getStatColor(stats.aggression * 20, gtoComparison?.aggression ? gtoComparison.aggression * 20 : undefined) }}
          >
            {stats.aggression.toFixed(1)}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={Math.min(stats.aggression * 20, 100)}
          sx={{
            height: 6,
            borderRadius: 3,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getStatColor(stats.aggression * 20),
              borderRadius: 3
            }
          }}
        />
      </Box>

      {/* Win Rate */}
      {stats.winRate !== undefined && (
        <Box
          sx={{
            p: 1,
            backgroundColor: stats.winRate >= 0 ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
            borderRadius: 1,
            border: `1px solid ${stats.winRate >= 0 ? '#4caf50' : '#f44336'}`,
            textAlign: 'center'
          }}
        >
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
            Win Rate from {stats.position}
          </Typography>
          <Typography
            variant="h6"
            fontWeight="bold"
            sx={{ color: stats.winRate >= 0 ? '#4caf50' : '#f44336' }}
          >
            {stats.winRate > 0 ? '+' : ''}{stats.winRate.toFixed(1)} bb/100
          </Typography>
        </Box>
      )}

      {/* GTO Comparison Note */}
      {gtoComparison && (
        <Box sx={{ mt: 2, p: 1, backgroundColor: 'rgba(255, 255, 255, 0.03)', borderRadius: 1 }}>
          <Typography variant="caption" color="rgba(255, 255, 255, 0.7)" sx={{ fontStyle: 'italic' }}>
            💡 Compared to GTO optimal ranges for {stats.position}
          </Typography>
        </Box>
      )}
    </Paper>
  );
});

PositionStatsCard.displayName = 'PositionStatsCard';
