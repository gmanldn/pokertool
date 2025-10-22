/**
 * Pot Odds Display Component
 * Shows real-time pot odds for decision making
 */
import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

interface PotOddsDisplayProps {
  potSize: number;
  betToCall: number;
  impliedPot?: number;
}

export const PotOddsDisplay: React.FC<PotOddsDisplayProps> = React.memo(({ 
  potSize, 
  betToCall,
  impliedPot = 0 
}) => {
  const totalPot = potSize + betToCall;
  const potOddsPercentage = totalPot > 0 ? (betToCall / totalPot) * 100 : 0;
  const potOddsRatio = betToCall > 0 ? (potSize / betToCall).toFixed(1) : 'N/A';

  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        backgroundColor: 'rgba(33, 33, 33, 0.95)',
        border: '2px solid',
        borderColor: 'primary.main',
      }}
    >
      <Typography variant="h6" color="primary" gutterBottom>
        Pot Odds
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="textSecondary">
            Pot:
          </Typography>
          <Typography variant="body1" fontWeight="bold" color="white">
            ${potSize.toFixed(2)}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="textSecondary">
            To Call:
          </Typography>
          <Typography variant="body1" fontWeight="bold" color="warning.main">
            ${betToCall.toFixed(2)}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', pt: 1, borderTop: '1px solid rgba(255,255,255,0.2)' }}>
          <Typography variant="body2" color="textSecondary">
            Odds:
          </Typography>
          <Typography variant="h6" fontWeight="bold" color="success.main">
            {potOddsRatio}:1
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="textSecondary">
            Break-even:
          </Typography>
          <Typography variant="body1" fontWeight="bold" color="info.main">
            {potOddsPercentage.toFixed(1)}%
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
});

PotOddsDisplay.displayName = 'PotOddsDisplay';
