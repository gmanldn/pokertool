/**
 * Pot Odds Visual Component
 *
 * Circular visual calculator showing pot odds, break-even equity, and required win percentage
 */
import React from 'react';
import { Box, Paper, Typography, Divider } from '@mui/material';

interface PotOddsVisualProps {
  potSize: number;
  betToCall: number;
  impliedOdds?: number;
}

export const PotOddsVisual: React.FC<PotOddsVisualProps> = React.memo(({
  potSize,
  betToCall,
  impliedOdds
}) => {
  const totalPot = potSize + betToCall;
  const oddsRatio = betToCall > 0 ? (potSize / betToCall) : 0;
  const breakEvenPercentage = totalPot > 0 ? (betToCall / totalPot) * 100 : 0;

  const getOddsColor = (): string => {
    if (oddsRatio >= 3) return '#4caf50';
    if (oddsRatio >= 2) return '#8bc34a';
    if (oddsRatio >= 1.5) return '#ff9800';
    return '#f44336';
  };

  const formatOdds = (): string => {
    if (betToCall === 0) return 'N/A';
    return `${oddsRatio.toFixed(1)}:1`;
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
      <Typography variant="subtitle1" fontWeight="bold" color="white" gutterBottom>
        💰 Pot Odds Calculator
      </Typography>

      {/* Circular Visualization */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          my: 2
        }}
      >
        <Box
          sx={{
            width: 150,
            height: 150,
            borderRadius: '50%',
            border: `8px solid ${getOddsColor()}`,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            position: 'relative',
            boxShadow: `0 0 20px ${getOddsColor()}66`
          }}
        >
          <Typography variant="h4" fontWeight="bold" sx={{ color: getOddsColor() }}>
            {formatOdds()}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Pot Odds
          </Typography>
        </Box>
      </Box>

      {/* Pot Information */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            Pot Size:
          </Typography>
          <Typography variant="body1" fontWeight="bold" color="white">
            ${potSize.toFixed(2)}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            To Call:
          </Typography>
          <Typography variant="body1" fontWeight="bold" color="warning.main">
            ${betToCall.toFixed(2)}
          </Typography>
        </Box>

        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            Total Pot:
          </Typography>
          <Typography variant="body1" fontWeight="bold" color="info.main">
            ${totalPot.toFixed(2)}
          </Typography>
        </Box>

        <Box
          sx={{
            p: 1.5,
            backgroundColor: `${getOddsColor()}22`,
            borderRadius: 1,
            border: `2px solid ${getOddsColor()}`,
            textAlign: 'center'
          }}
        >
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
            Break-Even Equity Required
          </Typography>
          <Typography
            variant="h5"
            fontWeight="bold"
            sx={{ color: getOddsColor() }}
          >
            {breakEvenPercentage.toFixed(1)}%
          </Typography>
        </Box>

        {impliedOdds !== undefined && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="textSecondary">
              Implied Odds:
            </Typography>
            <Typography variant="body2" fontWeight="medium" color="success.main">
              {impliedOdds.toFixed(1)}:1
            </Typography>
          </Box>
        )}
      </Box>

      {/* Interpretation */}
      <Box sx={{ mt: 2, p: 1, backgroundColor: 'rgba(255, 255, 255, 0.03)', borderRadius: 1 }}>
        <Typography variant="caption" color="rgba(255, 255, 255, 0.7)" sx={{ fontStyle: 'italic' }}>
          💡 {oddsRatio >= 2.5
            ? 'Excellent pot odds - favorable to call with drawing hands'
            : oddsRatio >= 1.5
            ? 'Decent pot odds - consider your equity and implied odds'
            : 'Marginal pot odds - need strong hand or good implied odds'}
        </Typography>
      </Box>
    </Paper>
  );
});

PotOddsVisual.displayName = 'PotOddsVisual';
