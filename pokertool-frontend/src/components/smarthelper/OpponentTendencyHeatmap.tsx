/**
 * Opponent Tendency Heatmap Component
 *
 * Visual grid showing opponent's tendencies and exploitable patterns
 */
import React from 'react';
import { Box, Paper, Typography, Tooltip, Chip } from '@mui/material';
import { Person, TrendingUp, TrendingDown } from '@mui/icons-material';

interface OpponentStats {
  name: string;
  vpip: number;
  pfr: number;
  threebet: number;
  foldToCbet: number;
  foldToThreebet: number;
  aggression: number;
  handsPlayed: number;
}

interface OpponentTendencyHeatmapProps {
  opponent: OpponentStats;
}

export const OpponentTendencyHeatmap: React.FC<OpponentTendencyHeatmapProps> = React.memo(({
  opponent
}) => {
  const getTendencyColor = (stat: number, thresholds: { exploitable: number; standard: number }): string => {
    if (stat < thresholds.exploitable || stat > (100 - thresholds.exploitable)) {
      return '#4caf50'; // Exploitable (green)
    }
    if (stat >= thresholds.standard && stat <= (100 - thresholds.standard)) {
      return '#ffc107'; // Standard (yellow)
    }
    return '#ff5722'; // Dangerous (orange-red)
  };

  const getTendencyLabel = (stat: number, thresholds: { exploitable: number; standard: number }): string => {
    if (stat < thresholds.exploitable) return 'Too Low';
    if (stat > (100 - thresholds.exploitable)) return 'Too High';
    if (stat >= thresholds.standard && stat <= (100 - thresholds.standard)) return 'Standard';
    return 'Aggressive';
  };

  const getPlayerTypeIcon = () => {
    if (opponent.vpip >= 35 && opponent.pfr >= 25) {
      return { icon: <TrendingUp />, label: 'LAG (Loose-Aggressive)', color: '#ff5722' };
    }
    if (opponent.vpip <= 20 && opponent.pfr <= 15) {
      return { icon: <TrendingDown />, label: 'TAG (Tight-Aggressive)', color: '#2196f3' };
    }
    if (opponent.vpip >= 35 && opponent.pfr <= 15) {
      return { icon: <Person />, label: 'LP (Loose-Passive)', color: '#4caf50' };
    }
    if (opponent.vpip <= 20 && opponent.pfr >= 15) {
      return { icon: <Person />, label: 'TP (Tight-Passive)', color: '#ff9800' };
    }
    return { icon: <Person />, label: 'Balanced', color: '#9c27b0' };
  };

  const playerType = getPlayerTypeIcon();

  const tendencies = [
    {
      name: 'VPIP',
      value: opponent.vpip,
      thresholds: { exploitable: 20, standard: 25 },
      description: 'Voluntarily Put $ In Pot - How often they play hands'
    },
    {
      name: 'PFR',
      value: opponent.pfr,
      thresholds: { exploitable: 15, standard: 20 },
      description: 'Preflop Raise - How often they raise preflop'
    },
    {
      name: '3-Bet',
      value: opponent.threebet,
      thresholds: { exploitable: 5, standard: 8 },
      description: '3-Bet Frequency - How often they re-raise'
    },
    {
      name: 'Fold to C-Bet',
      value: opponent.foldToCbet,
      thresholds: { exploitable: 60, standard: 50 },
      description: 'Fold to Continuation Bet - Exploitable if >60%'
    },
    {
      name: 'Fold to 3-Bet',
      value: opponent.foldToThreebet,
      thresholds: { exploitable: 70, standard: 60 },
      description: 'Fold to 3-Bet - Exploitable if >70%'
    },
    {
      name: 'Aggression',
      value: opponent.aggression * 20,
      thresholds: { exploitable: 40, standard: 60 },
      description: 'Aggression Factor - Bet/Raise vs Call ratio'
    }
  ];

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
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box>
          <Typography variant="subtitle1" fontWeight="bold" color="white">
            🎯 {opponent.name}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {opponent.handsPlayed} hands observed
          </Typography>
        </Box>
        <Chip
          icon={playerType.icon}
          label={playerType.label}
          sx={{
            backgroundColor: playerType.color,
            color: 'white',
            fontWeight: 'bold'
          }}
        />
      </Box>

      {/* Tendency Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.5 }}>
        {tendencies.map((tendency) => {
          const color = getTendencyColor(tendency.value, tendency.thresholds);
          const label = getTendencyLabel(tendency.value, tendency.thresholds);
          const isExploitable = color === '#4caf50';

          return (
            <Tooltip key={tendency.name} title={tendency.description} arrow>
              <Box
                sx={{
                  p: 1.5,
                  backgroundColor: `${color}22`,
                  borderRadius: 1,
                  border: `2px solid ${color}`,
                  cursor: 'help',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'scale(1.05)',
                    boxShadow: `0 4px 12px ${color}66`
                  }
                }}
              >
                <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
                  {tendency.name}
                </Typography>
                <Typography variant="h6" fontWeight="bold" sx={{ color }}>
                  {tendency.value.toFixed(0)}%
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color,
                    fontSize: '10px',
                    fontWeight: isExploitable ? 'bold' : 'normal'
                  }}
                >
                  {label} {isExploitable && '⚡'}
                </Typography>
              </Box>
            </Tooltip>
          );
        })}
      </Box>

      {/* Exploitation Suggestions */}
      <Box sx={{ mt: 2, p: 1.5, backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1, border: '1px solid #4caf50' }}>
        <Typography variant="caption" fontWeight="bold" color="#4caf50" sx={{ display: 'block', mb: 0.5 }}>
          💡 Exploitation Strategy:
        </Typography>
        <Typography variant="caption" color="rgba(255, 255, 255, 0.8)">
          {opponent.foldToCbet > 60 && 'C-bet frequently - they fold too often. '}
          {opponent.foldToThreebet > 70 && '3-bet light - they fold to 3-bets. '}
          {opponent.vpip > 40 && 'Tighten value range - they play too many hands. '}
          {opponent.threebet < 5 && 'Widen stealing range - they rarely 3-bet. '}
          {!((opponent.foldToCbet > 60) || (opponent.foldToThreebet > 70) || (opponent.vpip > 40) || (opponent.threebet < 5)) &&
            'Solid player - stick to GTO strategy.'}
        </Typography>
      </Box>
    </Paper>
  );
});

OpponentTendencyHeatmap.displayName = 'OpponentTendencyHeatmap';
