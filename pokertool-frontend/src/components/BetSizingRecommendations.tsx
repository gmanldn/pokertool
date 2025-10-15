/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/BetSizingRecommendations.tsx
version: v81.0.0
last_commit: '2025-10-15T16:10:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Bet Sizing Recommendations component for optimal bet guidance
---
POKERTOOL-HEADER-END */

import React, { useState } from 'react';
import { Box, Typography, Slider, Paper, Chip, useTheme, Tooltip } from '@mui/material';
import { ShowChart, Info } from '@mui/icons-material';

interface BetSizeOption {
  label: string;
  value: number; // Percentage of pot
  ev: number; // Expected value
  recommended: boolean;
  reasoning: string;
}

interface BetSizingRecommendationsProps {
  potSize: number;
  currentBet?: number;
  recommendedSizes?: BetSizeOption[];
  compact?: boolean;
}

const DEFAULT_SIZES: BetSizeOption[] = [
  { label: '1/3 Pot', value: 33, ev: 5.2, recommended: false, reasoning: 'Small sizing for value/protection' },
  { label: '1/2 Pot', value: 50, ev: 8.5, recommended: false, reasoning: 'Standard continuation bet' },
  { label: '2/3 Pot', value: 67, ev: 12.3, recommended: true, reasoning: 'Optimal value sizing' },
  { label: 'Pot', value: 100, ev: 10.1, recommended: false, reasoning: 'Maximum value extraction' },
  { label: 'Overbet', value: 150, ev: 7.8, recommended: false, reasoning: 'Polarized range strategy' },
];

export const BetSizingRecommendations: React.FC<BetSizingRecommendationsProps> = ({
  potSize,
  currentBet = 0,
  recommendedSizes = DEFAULT_SIZES,
  compact = false,
}) => {
  const theme = useTheme();
  const [selectedSize, setSelectedSize] = useState<number>(
    recommendedSizes.find((s) => s.recommended)?.value || 67
  );

  const calculateBetAmount = (percentage: number): number => {
    return (potSize * percentage) / 100;
  };

  const formatCurrency = (value: number): string => `$${value.toFixed(2)}`;

  const getEVColor = (ev: number): string => {
    if (ev > 10) return theme.palette.success.main;
    if (ev > 5) return theme.palette.success.light;
    if (ev > 0) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    setSelectedSize(newValue as number);
  };

  const selectedOption = recommendedSizes.find((s) => Math.abs(s.value - selectedSize) < 5) || {
    label: 'Custom',
    value: selectedSize,
    ev: 0,
    recommended: false,
    reasoning: 'Custom bet size',
  };

  return (
    <Paper
      sx={{
        p: compact ? 1.5 : 2.5,
        background: theme.palette.mode === 'dark'
          ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
          : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant={compact ? 'subtitle1' : 'h6'} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ShowChart />
          Bet Sizing
        </Typography>
        <Chip
          label={formatCurrency(potSize)}
          size="small"
          sx={{
            background: `${theme.palette.primary.main}20`,
            color: theme.palette.primary.main,
            fontWeight: 'bold',
          }}
        />
      </Box>

      {/* Quick Size Buttons */}
      <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
        {recommendedSizes.map((size) => (
          <Tooltip key={size.label} title={size.reasoning} arrow>
            <Chip
              label={size.label}
              onClick={() => setSelectedSize(size.value)}
              color={size.recommended ? 'success' : 'default'}
              variant={Math.abs(selectedSize - size.value) < 5 ? 'filled' : 'outlined'}
              icon={size.recommended ? <Info /> : undefined}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': {
                  transform: 'scale(1.05)',
                },
              }}
            />
          </Tooltip>
        ))}
      </Box>

      {/* Slider */}
      <Box sx={{ px: 1, mb: 3 }}>
        <Slider
          value={selectedSize}
          onChange={handleSliderChange}
          min={10}
          max={200}
          step={5}
          marks={recommendedSizes.map((s) => ({ value: s.value, label: '' }))}
          sx={{
            color: selectedOption.recommended ? theme.palette.success.main : theme.palette.primary.main,
            '& .MuiSlider-thumb': {
              width: 20,
              height: 20,
              '&:hover': {
                boxShadow: `0 0 0 8px ${
                  selectedOption.recommended
                    ? `${theme.palette.success.main}20`
                    : `${theme.palette.primary.main}20`
                }`,
              },
            },
            '& .MuiSlider-mark': {
              backgroundColor: 'rgba(255, 255, 255, 0.3)',
              height: 8,
              width: 2,
            },
            '& .MuiSlider-markActive': {
              backgroundColor: 'currentColor',
            },
          }}
        />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
          <Typography variant="caption" color="textSecondary">
            10%
          </Typography>
          <Typography variant="caption" color="textSecondary">
            200%
          </Typography>
        </Box>
      </Box>

      {/* Selected Bet Display */}
      <Box
        sx={{
          p: 2,
          borderRadius: 2,
          background: selectedOption.recommended
            ? `${theme.palette.success.main}15`
            : `${theme.palette.primary.main}15`,
          border: `2px solid ${
            selectedOption.recommended ? theme.palette.success.main : theme.palette.primary.main
          }`,
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Recommended Bet
            </Typography>
            <Typography variant={compact ? 'h5' : 'h4'} fontWeight="bold">
              {formatCurrency(calculateBetAmount(selectedSize))}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="caption" color="textSecondary">
              % of Pot
            </Typography>
            <Typography variant={compact ? 'h5' : 'h4'} fontWeight="bold" color="primary">
              {selectedSize}%
            </Typography>
          </Box>
        </Box>

        {/* EV Display */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mt: 1.5,
            pt: 1.5,
            borderTop: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography variant="body2" color="textSecondary">
            Expected Value:
          </Typography>
          <Typography
            variant="body2"
            fontWeight="bold"
            sx={{ color: getEVColor(selectedOption.ev) }}
          >
            +{formatCurrency(selectedOption.ev)}
          </Typography>
          <Box
            sx={{
              ml: 'auto',
              px: 1,
              py: 0.5,
              borderRadius: 1,
              background: selectedOption.recommended ? `${theme.palette.success.main}30` : 'transparent',
            }}
          >
            {selectedOption.recommended && (
              <Typography variant="caption" sx={{ color: theme.palette.success.main, fontWeight: 'bold' }}>
                ✓ Optimal
              </Typography>
            )}
          </Box>
        </Box>
      </Box>

      {/* Reasoning */}
      {!compact && (
        <Box
          sx={{
            p: 1.5,
            borderRadius: 1,
            background: 'rgba(255, 255, 255, 0.05)',
          }}
        >
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
            Reasoning:
          </Typography>
          <Typography variant="body2">{selectedOption.reasoning}</Typography>
        </Box>
      )}

      {/* Size Comparison */}
      {!compact && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="textSecondary" gutterBottom>
            EV by Size:
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
            {recommendedSizes.map((size) => (
              <Tooltip key={size.label} title={`${size.label}: ${formatCurrency(size.ev)} EV`} arrow>
                <Box
                  sx={{
                    flex: 1,
                    height: 4,
                    borderRadius: 2,
                    background: getEVColor(size.ev),
                    opacity: Math.abs(selectedSize - size.value) < 5 ? 1 : 0.3,
                    transition: 'opacity 0.3s ease',
                  }}
                />
              </Tooltip>
            ))}
          </Box>
        </Box>
      )}
    </Paper>
  );
};

export default BetSizingRecommendations;
