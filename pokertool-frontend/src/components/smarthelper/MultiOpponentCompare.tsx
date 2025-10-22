/**
 * Multi-Opponent Comparison Component
 *
 * Compare all active opponents side-by-side with color-coded stats
 */
import React from 'react';
import { Box, Paper, Typography, Chip } from '@mui/material';
import { People, Person } from '@mui/icons-material';

interface OpponentStats {
  name: string;
  vpip: number;
  pfr: number;
  threebet: number;
  foldToCbet: number;
  foldToThreebet: number;
  aggression: number;
  handsPlayed: number;
  position: string;
}

interface MultiOpponentCompareProps {
  opponents: OpponentStats[];
}

export const MultiOpponentCompare: React.FC<MultiOpponentCompareProps> = React.memo(({ opponents }) => {
  const getStatColor = (stat: number, thresholds: { low: number; high: number }): string => {
    if (stat < thresholds.low) return '#2196f3';  // Blue - tight/passive
    if (stat > thresholds.high) return '#ff5722';  // Red - loose/aggressive
    return '#4caf50';  // Green - standard
  };

  const getPlayerTypeLabel = (opp: OpponentStats): string => {
    if (opp.vpip >= 35 && opp.pfr >= 25) return 'LAG';
    if (opp.vpip <= 20 && opp.pfr <= 15) return 'TAG';
    if (opp.vpip >= 35 && opp.pfr <= 15) return 'LP';
    if (opp.vpip <= 20 && opp.pfr >= 15) return 'TP';
    return 'BAL';
  };

  const getPlayerTypeColor = (label: string): string => {
    switch (label) {
      case 'LAG': return '#ff5722';  // Loose-Aggressive
      case 'TAG': return '#2196f3';  // Tight-Aggressive
      case 'LP': return '#4caf50';   // Loose-Passive
      case 'TP': return '#ff9800';   // Tight-Passive
      default: return '#9c27b0';     // Balanced
    }
  };

  if (opponents.length === 0) {
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
        <Typography variant="body2" color="textSecondary" textAlign="center">
          No opponent data available
        </Typography>
      </Paper>
    );
  }

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
        <People sx={{ color: 'primary.main', fontSize: 24 }} />
        <Typography variant="subtitle1" fontWeight="bold" color="white">
          Opponent Comparison
        </Typography>
        <Chip
          label={`${opponents.length} player${opponents.length > 1 ? 's' : ''}`}
          size="small"
          sx={{ height: 20, fontSize: '10px', ml: 'auto' }}
        />
      </Box>

      <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', pb: 1 }}>
        {opponents.map((opp) => {
          const playerType = getPlayerTypeLabel(opp);
          const playerColor = getPlayerTypeColor(playerType);

          return (
            <Box
              key={opp.name}
              sx={{
                minWidth: 160,
                p: 1.5,
                backgroundColor: 'rgba(255, 255, 255, 0.03)',
                borderRadius: 1,
                border: `2px solid ${playerColor}44`
              }}
            >
              {/* Header */}
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Person sx={{ fontSize: 16, color: playerColor }} />
                  <Typography variant="caption" fontWeight="bold" color="white">
                    {opp.name}
                  </Typography>
                </Box>
                <Chip
                  label={playerType}
                  size="small"
                  sx={{
                    height: 16,
                    fontSize: '9px',
                    backgroundColor: playerColor,
                    color: 'white'
                  }}
                />
              </Box>

              {/* Position */}
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 1 }}>
                {opp.position}
              </Typography>

              {/* Stats */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.6)">
                    VPIP:
                  </Typography>
                  <Typography
                    variant="caption"
                    fontWeight="bold"
                    sx={{ color: getStatColor(opp.vpip, { low: 20, high: 35 }) }}
                  >
                    {opp.vpip.toFixed(0)}%
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.6)">
                    PFR:
                  </Typography>
                  <Typography
                    variant="caption"
                    fontWeight="bold"
                    sx={{ color: getStatColor(opp.pfr, { low: 15, high: 25 }) }}
                  >
                    {opp.pfr.toFixed(0)}%
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.6)">
                    3-Bet:
                  </Typography>
                  <Typography
                    variant="caption"
                    fontWeight="bold"
                    sx={{ color: getStatColor(opp.threebet, { low: 5, high: 12 }) }}
                  >
                    {opp.threebet.toFixed(0)}%
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.6)">
                    Fold C-Bet:
                  </Typography>
                  <Typography
                    variant="caption"
                    fontWeight="bold"
                    sx={{ color: opp.foldToCbet > 60 ? '#4caf50' : '#ff9800' }}
                  >
                    {opp.foldToCbet.toFixed(0)}%
                  </Typography>
                </Box>
              </Box>

              {/* Hands */}
              <Typography
                variant="caption"
                color="textSecondary"
                sx={{ display: 'block', mt: 1, fontSize: '9px', textAlign: 'center' }}
              >
                {opp.handsPlayed} hands
              </Typography>
            </Box>
          );
        })}
      </Box>
    </Paper>
  );
});

MultiOpponentCompare.displayName = 'MultiOpponentCompare';
