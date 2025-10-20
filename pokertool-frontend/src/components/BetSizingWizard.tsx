/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/BetSizingWizard.tsx
version: v79.0.0
last_commit: '2025-10-15T04:37:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Bet Sizing Wizard component with interactive slider and presets
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Slider,
  Grid,
  Chip,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

// Bet size preset
export interface BetSizePreset {
  label: string;
  percentage: number; // Percentage of pot
  description: string;
}

// Bet size recommendation
export interface BetSizeRecommendation {
  amount: number;
  percentage: number;
  ev: number;
  foldEquity: number;
  isPotCommitted: boolean;
  isOptimal: boolean;
}

interface BetSizingWizardProps {
  potSize: number;
  stackSize: number;
  onBetSizeSelect?: (amount: number, percentage: number) => void;
  calculateEV?: (amount: number) => number;
  calculateFoldEquity?: (amount: number) => number;
}

// Standard bet size presets
const BET_PRESETS: BetSizePreset[] = [
  {
    label: '33% Pot',
    percentage: 33,
    description: 'Small probe bet',
  },
  {
    label: '50% Pot',
    percentage: 50,
    description: 'Standard bet',
  },
  {
    label: '75% Pot',
    percentage: 75,
    description: 'Strong bet',
  },
  {
    label: '100% Pot',
    percentage: 100,
    description: 'Pot-sized bet',
  },
  {
    label: '200% Pot',
    percentage: 200,
    description: 'Overbet',
  },
];

export const BetSizingWizard: React.FC<BetSizingWizardProps> = ({
  potSize,
  stackSize,
  onBetSizeSelect,
  calculateEV,
  calculateFoldEquity,
}) => {
  const [selectedPercentage, setSelectedPercentage] = useState<number>(100);
  const [customPercentage, setCustomPercentage] = useState<number>(100);
  const [useCustom, setUseCustom] = useState<boolean>(false);

  // Calculate current bet amount
  const currentBetAmount = useMemo(() => {
    const percentage = useCustom ? customPercentage : selectedPercentage;
    const amount = (potSize * percentage) / 100;
    return Math.min(amount, stackSize); // Can't bet more than stack
  }, [potSize, stackSize, selectedPercentage, customPercentage, useCustom]);

  // Calculate Stack-to-Pot Ratio (SPR)
  const spr = useMemo(() => {
    if (potSize === 0) return 0;
    return stackSize / potSize;
  }, [stackSize, potSize]);

  // Default EV calculator (can be overridden)
  const defaultCalculateEV = (amount: number): number => {
    // Simple heuristic: EV increases with fold equity, decreases with pot commitment
    const betPercentage = (amount / potSize) * 100;
    const baseFoldEquity = Math.min(betPercentage / 2, 60); // Max 60% fold equity
    const potCommitmentPenalty = amount > stackSize * 0.5 ? -5 : 0;
    return baseFoldEquity / 10 + potCommitmentPenalty;
  };

  // Default fold equity calculator (can be overridden)
  const defaultCalculateFoldEquity = (amount: number): number => {
    const betPercentage = (amount / potSize) * 100;
    return Math.min(betPercentage / 2, 60); // Simple linear relationship, max 60%
  };

  // Get recommendations for each preset
  const getRecommendations = (): BetSizeRecommendation[] => {
    const allPercentages = [
      ...BET_PRESETS.map((p) => p.percentage),
      customPercentage,
    ];

    return allPercentages.map((percentage) => {
      const amount = Math.min((potSize * percentage) / 100, stackSize);
      const ev = calculateEV ? calculateEV(amount) : defaultCalculateEV(amount);
      const foldEquity = calculateFoldEquity
        ? calculateFoldEquity(amount)
        : defaultCalculateFoldEquity(amount);
      const isPotCommitted = amount > stackSize * 0.5;

      return {
        amount,
        percentage,
        ev,
        foldEquity,
        isPotCommitted,
        isOptimal: false, // Will be set below
      };
    });
  };

  const recommendations = useMemo(() => {
    const recs = getRecommendations();
    // Mark optimal bet (highest EV)
    const maxEV = Math.max(...recs.map((r) => r.ev));
    return recs.map((r) => ({
      ...r,
      isOptimal: Math.abs(r.ev - maxEV) < 0.01,
    }));
  }, [potSize, stackSize, customPercentage, calculateEV, calculateFoldEquity]);

  // Get current recommendation
  const currentRecommendation = useMemo(() => {
    const percentage = useCustom ? customPercentage : selectedPercentage;
    return recommendations.find((r) => r.percentage === percentage);
  }, [recommendations, selectedPercentage, customPercentage, useCustom]);

  // Handle preset selection
  const handlePresetSelect = (percentage: number) => {
    setSelectedPercentage(percentage);
    setUseCustom(false);
    if (onBetSizeSelect) {
      const amount = Math.min((potSize * percentage) / 100, stackSize);
      onBetSizeSelect(amount, percentage);
    }
  };

  // Handle custom slider change
  const handleCustomChange = (event: Event, value: number | number[]) => {
    const percentage = value as number;
    setCustomPercentage(percentage);
    setUseCustom(true);
    if (onBetSizeSelect) {
      const amount = Math.min((potSize * percentage) / 100, stackSize);
      onBetSizeSelect(amount, percentage);
    }
  };

  // Format currency
  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(2)}`;
  };

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  // Get EV color
  const getEVColor = (ev: number): string => {
    if (ev > 5) return '#4caf50';
    if (ev > 0) return '#8bc34a';
    if (ev > -5) return '#ff9800';
    return '#f44336';
  };

  // Get optimal zone for slider
  const getOptimalZone = (): [number, number] => {
    const optimalRecs = recommendations.filter((r) => r.isOptimal);
    if (optimalRecs.length === 0) return [75, 125];

    const percentages = optimalRecs.map((r) => r.percentage);
    const min = Math.min(...percentages);
    const max = Math.max(...percentages);
    return [Math.max(min - 10, 10), Math.min(max + 10, 500)];
  };

  const [optimalMin, optimalMax] = getOptimalZone();

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrendingUpIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">Bet Sizing Wizard</Typography>
        </Box>

        {/* Pot & Stack Info */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={4}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Pot Size
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(potSize)}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Your Stack
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(stackSize)}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                SPR
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                {spr.toFixed(1)}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Preset Buttons */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            Quick Presets
          </Typography>
          <Grid container spacing={1}>
            {BET_PRESETS.map((preset) => {
              const rec = recommendations.find((r) => r.percentage === preset.percentage);
              const isSelected = !useCustom && selectedPercentage === preset.percentage;
              const amount = Math.min((potSize * preset.percentage) / 100, stackSize);
              const isAllIn = amount >= stackSize;

              return (
                <Grid item xs={6} sm={4} key={preset.label}>
                  <Tooltip title={preset.description} arrow>
                    <Button
                      variant={isSelected ? 'contained' : 'outlined'}
                      fullWidth
                      size="small"
                      onClick={() => handlePresetSelect(preset.percentage)}
                      sx={{
                        position: 'relative',
                        borderWidth: rec?.isOptimal ? 2 : 1,
                        borderColor: rec?.isOptimal ? 'success.main' : undefined,
                      }}
                    >
                      <Box sx={{ width: '100%' }}>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {preset.label}
                        </Typography>
                        <Typography variant="caption" display="block">
                          {formatCurrency(amount)}
                        </Typography>
                        {rec && (
                          <Typography
                            variant="caption"
                            display="block"
                            sx={{ color: getEVColor(rec.ev) }}
                          >
                            EV: {rec.ev >= 0 ? '+' : ''}
                            {rec.ev.toFixed(1)}
                          </Typography>
                        )}
                        {isAllIn && (
                          <Chip
                            label="ALL-IN"
                            size="small"
                            color="error"
                            sx={{ mt: 0.5, fontSize: '0.65rem', height: 16 }}
                          />
                        )}
                      </Box>
                    </Button>
                  </Tooltip>
                </Grid>
              );
            })}
          </Grid>
        </Box>

        {/* Custom Slider */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            Custom Bet Size
          </Typography>
          <Box sx={{ px: 2 }}>
            <Slider
              value={customPercentage}
              onChange={handleCustomChange}
              min={10}
              max={500}
              step={5}
              marks={[
                { value: 50, label: '50%' },
                { value: 100, label: '100%' },
                { value: 200, label: '200%' },
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
              sx={{
                '& .MuiSlider-track': {
                  background: `linear-gradient(to right, 
                    #ff9800 0%, 
                    #4caf50 ${optimalMin}%, 
                    #4caf50 ${optimalMax}%, 
                    #ff9800 100%)`,
                },
                '& .MuiSlider-rail': {
                  opacity: 0.3,
                },
              }}
            />
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {formatPercentage(customPercentage)} of pot
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
              {formatCurrency(currentBetAmount)}
            </Typography>
          </Box>
        </Box>

        {/* Current Recommendation */}
        {currentRecommendation && (
          <Box
            sx={{
              p: 2,
              backgroundColor: currentRecommendation.isOptimal
                ? 'rgba(76, 175, 80, 0.1)'
                : 'rgba(255, 255, 255, 0.05)',
              borderRadius: 1,
              borderLeft: `4px solid ${
                currentRecommendation.isOptimal ? '#4caf50' : '#2196f3'
              }`,
            }}
          >
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Expected Value
                  </Typography>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 'bold',
                      color: getEVColor(currentRecommendation.ev),
                    }}
                  >
                    {currentRecommendation.ev >= 0 ? '+' : ''}$
                    {currentRecommendation.ev.toFixed(2)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Fold Equity
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {formatPercentage(currentRecommendation.foldEquity)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Status
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {currentRecommendation.isOptimal ? (
                      <Chip
                        label="Optimal"
                        size="small"
                        color="success"
                        sx={{ fontWeight: 'bold' }}
                      />
                    ) : (
                      <Chip
                        label="Suboptimal"
                        size="small"
                        color="default"
                      />
                    )}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Pot Commitment Warning */}
        {currentRecommendation?.isPotCommitted && (
          <Alert severity="warning" sx={{ mt: 2 }} icon={<WarningIcon />}>
            <Typography variant="caption">
              <strong>Pot Committed:</strong> This bet commits over 50% of your stack.
              Consider going all-in or betting less.
            </Typography>
          </Alert>
        )}

        {/* Optimal Zone Indicator */}
        {currentRecommendation?.isOptimal && (
          <Box
            sx={{
              mt: 2,
              p: 1,
              backgroundColor: 'rgba(76, 175, 80, 0.1)',
              borderRadius: 1,
              textAlign: 'center',
            }}
          >
            <Typography variant="caption" sx={{ color: 'success.main' }}>
              ✓ This bet size is in the optimal EV range ({optimalMin}%-{optimalMax}% of pot)
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default BetSizingWizard;
