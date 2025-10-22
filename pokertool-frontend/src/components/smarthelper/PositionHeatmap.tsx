/**
 * Position Heatmap Component
 *
 * Visual grid showing stats by position (UTG, MP, CO, BTN, SB, BB)
 */
import React from 'react';
import { Box, Paper, Typography, Tooltip } from '@mui/material';
import { Place } from '@mui/icons-material';

interface PositionStats {
  position: string;
  vpip: number;
  pfr: number;
  aggression: number;
  winRate?: number;
  handsPlayed: number;
}

interface PositionHeatmapProps {
  stats: PositionStats[];
}

export const PositionHeatmap: React.FC<PositionHeatmapProps> = React.memo(({ stats }) => {
  const positions = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'];

  const getStatColor = (stat: number, type: 'vpip' | 'pfr' | 'aggression'): string => {
    if (type === 'vpip') {
      if (stat >= 30) return '#ff5722';
      if (stat >= 20) return '#ff9800';
      if (stat >= 15) return '#4caf50';
      return '#2196f3';
    }
    if (type === 'pfr') {
      if (stat >= 25) return '#ff5722';
      if (stat >= 15) return '#ff9800';
      if (stat >= 10) return '#4caf50';
      return '#2196f3';
    }
    // Aggression
    if (stat >= 3) return '#ff5722';
    if (stat >= 2) return '#ff9800';
    if (stat >= 1.5) return '#4caf50';
    return '#2196f3';
  };

  const getPositionStats = (position: string): PositionStats | null => {
    return stats.find(s => s.position === position) || null;
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
        <Typography variant="subtitle1" fontWeight="bold" color="white">
          Positional Heatmap
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1 }}>
        {positions.map((position) => {
          const posStats = getPositionStats(position);

          if (!posStats) {
            return (
              <Box
                key={position}
                sx={{
                  p: 1.5,
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: 1,
                  border: '1px dashed rgba(255, 255, 255, 0.1)',
                  textAlign: 'center'
                }}
              >
                <Typography variant="caption" color="textSecondary">
                  {position}
                </Typography>
                <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                  No data
                </Typography>
              </Box>
            );
          }

          return (
            <Tooltip
              key={position}
              title={`${position}: VPIP ${posStats.vpip.toFixed(0)}%, PFR ${posStats.pfr.toFixed(0)}%, Agg ${posStats.aggression.toFixed(1)} (${posStats.handsPlayed} hands)`}
              arrow
            >
              <Box
                sx={{
                  p: 1.5,
                  backgroundColor: getStatColor(posStats.vpip, 'vpip') + '22',
                  borderRadius: 1,
                  border: `2px solid ${getStatColor(posStats.vpip, 'vpip')}`,
                  cursor: 'help',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'scale(1.05)',
                    boxShadow: `0 4px 12px ${getStatColor(posStats.vpip, 'vpip')}66`
                  }
                }}
              >
                <Typography variant="caption" fontWeight="bold" color="white" sx={{ display: 'block' }}>
                  {position}
                </Typography>
                <Typography variant="caption" sx={{ color: getStatColor(posStats.vpip, 'vpip'), display: 'block' }}>
                  V: {posStats.vpip.toFixed(0)}%
                </Typography>
                <Typography variant="caption" sx={{ color: getStatColor(posStats.pfr, 'pfr'), display: 'block' }}>
                  R: {posStats.pfr.toFixed(0)}%
                </Typography>
                <Typography variant="caption" sx={{ color: getStatColor(posStats.aggression, 'aggression'), display: 'block', fontSize: '9px' }}>
                  {posStats.handsPlayed} hands
                </Typography>
              </Box>
            </Tooltip>
          );
        })}
      </Box>
    </Paper>
  );
});

PositionHeatmap.displayName = 'PositionHeatmap';
