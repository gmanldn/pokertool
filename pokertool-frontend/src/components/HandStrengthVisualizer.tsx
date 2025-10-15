/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/HandStrengthVisualizer.tsx
version: v79.0.0
last_commit: '2025-10-15T04:38:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Hand Strength Visualizer component with equity display and outs tracker
---
POKERTOOL-HEADER-END */

import React, { useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Grid,
  Chip,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
} from '@mui/icons-material';

// Hand category
export enum HandCategory {
  MONSTER = 'MONSTER',
  STRONG = 'STRONG',
  MEDIUM = 'MEDIUM',
  WEAK = 'WEAK',
  TRASH = 'TRASH',
}

// Out card
export interface OutCard {
  rank: string;
  suit: string;
  improvesTo: string; // Description of what it improves to
}

// Hand strength data
export interface HandStrengthData {
  equity: number; // 0-100
  percentile: number; // 0-100, percentile ranking vs opponent range
  category: HandCategory;
  outs: OutCard[];
  outsCount: number;
  outsPercentage: number; // % chance to hit an out
  improvingCards: string[]; // Cards that improve hand on next street
  averageEquity: number; // Average equity for all hands
  vsRange: string; // Description of opponent range
}

interface HandStrengthVisualizerProps {
  handStrength: HandStrengthData;
  compact?: boolean;
}

// Hand category configuration
const CATEGORY_CONFIG = {
  [HandCategory.MONSTER]: {
    label: 'Monster',
    color: '#4caf50',
    description: 'Premium hand, very strong equity',
    minEquity: 80,
  },
  [HandCategory.STRONG]: {
    label: 'Strong',
    color: '#8bc34a',
    description: 'Strong hand, good equity',
    minEquity: 60,
  },
  [HandCategory.MEDIUM]: {
    label: 'Medium',
    color: '#ffc107',
    description: 'Playable hand, decent equity',
    minEquity: 40,
  },
  [HandCategory.WEAK]: {
    label: 'Weak',
    color: '#ff9800',
    description: 'Marginal hand, low equity',
    minEquity: 20,
  },
  [HandCategory.TRASH]: {
    label: 'Trash',
    color: '#f44336',
    description: 'Very weak hand, poor equity',
    minEquity: 0,
  },
};

export const HandStrengthVisualizer: React.FC<HandStrengthVisualizerProps> = ({
  handStrength,
  compact = false,
}) => {
  // Get category configuration
  const categoryConfig = useMemo(() => {
    return CATEGORY_CONFIG[handStrength.category];
  }, [handStrength.category]);

  // Calculate equity difference from average
  const equityDifference = useMemo(() => {
    return handStrength.equity - handStrength.averageEquity;
  }, [handStrength.equity, handStrength.averageEquity]);

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  // Get percentile description
  const getPercentileDescription = (percentile: number): string => {
    if (percentile >= 90) return 'Top 10%';
    if (percentile >= 75) return 'Top 25%';
    if (percentile >= 50) return 'Top 50%';
    if (percentile >= 25) return 'Bottom 50%';
    return 'Bottom 25%';
  };

  // Get equity bar color
  const getEquityBarColor = (equity: number): string => {
    if (equity >= 80) return '#4caf50';
    if (equity >= 60) return '#8bc34a';
    if (equity >= 40) return '#ffc107';
    if (equity >= 20) return '#ff9800';
    return '#f44336';
  };

  // Get trend icon
  const getTrendIcon = () => {
    if (equityDifference > 10) return <TrendingUpIcon sx={{ color: '#4caf50' }} />;
    if (equityDifference < -10) return <TrendingDownIcon sx={{ color: '#f44336' }} />;
    return <RemoveIcon sx={{ color: '#9e9e9e' }} />;
  };

  // Group outs by suit
  const outsBySuit = useMemo(() => {
    const grouped: { [suit: string]: OutCard[] } = {};
    handStrength.outs.forEach((out) => {
      if (!grouped[out.suit]) {
        grouped[out.suit] = [];
      }
      grouped[out.suit].push(out);
    });
    return grouped;
  }, [handStrength.outs]);

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Hand Strength</Typography>
          <Chip
            label={categoryConfig.label}
            sx={{
              backgroundColor: categoryConfig.color,
              color: 'white',
              fontWeight: 'bold',
            }}
          />
        </Box>

        {/* Equity Bar */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Equity vs {handStrength.vsRange}
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: getEquityBarColor(handStrength.equity) }}>
              {formatPercentage(handStrength.equity)}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={handStrength.equity}
            sx={{
              height: 12,
              borderRadius: 6,
              backgroundColor: 'rgba(255,255,255,0.1)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getEquityBarColor(handStrength.equity),
                borderRadius: 6,
              },
            }}
          />
        </Box>

        {/* Stats Grid */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          {/* Percentile Ranking */}
          <Grid item xs={6}>
            <Box
              sx={{
                p: 1.5,
                backgroundColor: 'rgba(255,255,255,0.05)',
                borderRadius: 1,
                textAlign: 'center',
              }}
            >
              <Typography variant="caption" color="text.secondary" display="block">
                Percentile Ranking
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 'bold', my: 0.5 }}>
                {formatPercentage(handStrength.percentile)}
              </Typography>
              <Chip
                label={getPercentileDescription(handStrength.percentile)}
                size="small"
                sx={{ fontSize: '0.7rem' }}
              />
            </Box>
          </Grid>

          {/* Equity Comparison */}
          <Grid item xs={6}>
            <Box
              sx={{
                p: 1.5,
                backgroundColor: 'rgba(255,255,255,0.05)',
                borderRadius: 1,
                textAlign: 'center',
              }}
            >
              <Typography variant="caption" color="text.secondary" display="block">
                vs Average Hand
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', my: 0.5 }}>
                {getTrendIcon()}
                <Typography
                  variant="h5"
                  sx={{
                    fontWeight: 'bold',
                    ml: 0.5,
                    color: equityDifference > 0 ? '#4caf50' : equityDifference < 0 ? '#f44336' : '#9e9e9e',
                  }}
                >
                  {equityDifference > 0 ? '+' : ''}
                  {formatPercentage(Math.abs(equityDifference))}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Avg: {formatPercentage(handStrength.averageEquity)}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {!compact && (
          <>
            <Divider sx={{ my: 2 }} />

            {/* Outs Section */}
            {handStrength.outsCount > 0 && (
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Outs to Improve
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Chip
                      label={`${handStrength.outsCount} outs`}
                      size="small"
                      color="primary"
                      sx={{ fontWeight: 'bold' }}
                    />
                    <Chip
                      label={`${formatPercentage(handStrength.outsPercentage)} chance`}
                      size="small"
                      color="success"
                    />
                  </Box>
                </Box>

                {/* Outs by Suit */}
                <Box
                  sx={{
                    p: 1.5,
                    backgroundColor: 'rgba(255,255,255,0.05)',
                    borderRadius: 1,
                    maxHeight: 120,
                    overflowY: 'auto',
                  }}
                >
                  <Grid container spacing={1}>
                    {Object.entries(outsBySuit).map(([suit, cards]) => (
                      <Grid item xs={12} key={suit}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 'bold',
                              color:
                                suit === '♥' || suit === '♦'
                                  ? '#f44336'
                                  : suit === '♠' || suit === '♣'
                                  ? '#ffffff'
                                  : '#9e9e9e',
                            }}
                          >
                            {suit}
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {cards.map((card, idx) => (
                              <Tooltip key={idx} title={card.improvesTo} arrow>
                                <Chip
                                  label={card.rank}
                                  size="small"
                                  sx={{
                                    fontSize: '0.7rem',
                                    height: 20,
                                    backgroundColor: 'rgba(33, 150, 243, 0.2)',
                                    '&:hover': {
                                      backgroundColor: 'rgba(33, 150, 243, 0.3)',
                                    },
                                  }}
                                />
                              </Tooltip>
                            ))}
                          </Box>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              </Box>
            )}

            {/* Improving Cards on Next Street */}
            {handStrength.improvingCards.length > 0 && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  Cards That Improve Your Hand
                </Typography>
                <Box
                  sx={{
                    p: 1.5,
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    borderRadius: 1,
                    borderLeft: '4px solid #4caf50',
                  }}
                >
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {handStrength.improvingCards.map((card, idx) => (
                      <Chip
                        key={idx}
                        label={card}
                        size="small"
                        sx={{
                          backgroundColor: '#4caf50',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.75rem',
                        }}
                      />
                    ))}
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Any of these cards will improve your hand strength
                  </Typography>
                </Box>
              </Box>
            )}

            {/* No Outs Message */}
            {handStrength.outsCount === 0 && handStrength.equity < 80 && (
              <Box
                sx={{
                  p: 1.5,
                  backgroundColor: 'rgba(255, 152, 0, 0.1)',
                  borderRadius: 1,
                  borderLeft: '4px solid #ff9800',
                }}
              >
                <Typography variant="caption" color="warning.main">
                  ⚠️ No clear outs - hand is unlikely to improve significantly
                </Typography>
              </Box>
            )}

            {/* Monster Hand Message */}
            {handStrength.category === HandCategory.MONSTER && (
              <Box
                sx={{
                  p: 1.5,
                  backgroundColor: 'rgba(76, 175, 80, 0.1)',
                  borderRadius: 1,
                  borderLeft: '4px solid #4caf50',
                }}
              >
                <Typography variant="caption" sx={{ color: 'success.main' }}>
                  ✓ Excellent hand strength - you have a significant equity advantage
                </Typography>
              </Box>
            )}
          </>
        )}

        {/* Compact Mode Summary */}
        {compact && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              {getPercentileDescription(handStrength.percentile)} • {handStrength.outsCount} outs
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {formatPercentage(handStrength.outsPercentage)} to improve
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default HandStrengthVisualizer;
