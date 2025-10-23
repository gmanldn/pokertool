/**
 * Animated Decision Factors Component
 *
 * Visual representation of decision factors with pulse animations for:
 * - Factor importance changes
 * - New factor detection
 * - Critical factor highlights
 * - Strength meter animations
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Chip,
  Tooltip,
  Fade,
  Zoom
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Error,
  CheckCircle,
  Warning,
  Info,
  AutoAwesome
} from '@mui/icons-material';

export type FactorImpact = 'critical' | 'high' | 'medium' | 'low';
export type FactorSentiment = 'positive' | 'negative' | 'neutral';

export interface DecisionFactor {
  id: string;
  name: string;
  description: string;
  value: number; // 0-100 scale
  impact: FactorImpact;
  sentiment: FactorSentiment;
  isNew?: boolean;
  hasChanged?: boolean;
  previousValue?: number;
}

interface AnimatedDecisionFactorsProps {
  factors: DecisionFactor[];
  title?: string;
  showImpactBadges?: boolean;
  enablePulseAnimation?: boolean;
  animationDuration?: number;
}

export const AnimatedDecisionFactors: React.FC<AnimatedDecisionFactorsProps> = ({
  factors,
  title = 'Decision Factors',
  showImpactBadges = true,
  enablePulseAnimation = true,
  animationDuration = 300
}) => {
  const [animatedFactors, setAnimatedFactors] = useState<Map<string, number>>(new Map());

  // Animate factor value changes
  useEffect(() => {
    factors.forEach((factor) => {
      const currentValue = animatedFactors.get(factor.id) || 0;
      const targetValue = factor.value;

      if (currentValue !== targetValue) {
        const startValue = currentValue;
        const startTime = Date.now();
        const duration = animationDuration;

        const animate = () => {
          const elapsed = Date.now() - startTime;
          const progress = Math.min(elapsed / duration, 1);

          // Ease-out cubic
          const easeOut = 1 - Math.pow(1 - progress, 3);

          const current = startValue + (targetValue - startValue) * easeOut;

          setAnimatedFactors((prev) => new Map(prev).set(factor.id, current));

          if (progress < 1) {
            requestAnimationFrame(animate);
          }
        };

        requestAnimationFrame(animate);
      }
    });
  }, [factors, animationDuration]);

  const getImpactConfig = (impact: FactorImpact) => {
    switch (impact) {
      case 'critical':
        return { color: '#f44336', label: 'Critical', icon: <Error sx={{ fontSize: 14 }} /> };
      case 'high':
        return { color: '#ff9800', label: 'High', icon: <Warning sx={{ fontSize: 14 }} /> };
      case 'medium':
        return { color: '#2196f3', label: 'Medium', icon: <Info sx={{ fontSize: 14 }} /> };
      case 'low':
        return { color: '#9e9e9e', label: 'Low', icon: <CheckCircle sx={{ fontSize: 14 }} /> };
      default:
        return { color: '#9e9e9e', label: 'Unknown', icon: <Info sx={{ fontSize: 14 }} /> };
    }
  };

  const getSentimentConfig = (sentiment: FactorSentiment) => {
    switch (sentiment) {
      case 'positive':
        return { color: '#4caf50', icon: <TrendingUp sx={{ fontSize: 16 }} /> };
      case 'negative':
        return { color: '#f44336', icon: <TrendingDown sx={{ fontSize: 16 }} /> };
      case 'neutral':
        return { color: '#9e9e9e', icon: null };
      default:
        return { color: '#9e9e9e', icon: null };
    }
  };

  const getChangePercentage = (factor: DecisionFactor): number | null => {
    if (!factor.hasChanged || factor.previousValue === undefined) return null;
    return factor.value - factor.previousValue;
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
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <AutoAwesome sx={{ color: 'primary.main', fontSize: 20 }} />
        <Typography variant="subtitle1" fontWeight="bold" color="white">
          {title}
        </Typography>
        <Chip
          label={`${factors.length} factors`}
          size="small"
          sx={{ height: 18, fontSize: '10px', ml: 'auto' }}
        />
      </Box>

      {/* Factors List */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {factors.map((factor, index) => {
          const impactConfig = getImpactConfig(factor.impact);
          const sentimentConfig = getSentimentConfig(factor.sentiment);
          const animatedValue = animatedFactors.get(factor.id) || factor.value;
          const changePercent = getChangePercentage(factor);

          return (
            <Zoom
              key={factor.id}
              in
              timeout={animationDuration}
              style={{ transitionDelay: `${index * 50}ms` }}
            >
              <Box
                sx={{
                  position: 'relative',
                  p: 1.5,
                  backgroundColor: factor.isNew ? 'rgba(33, 150, 243, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                  borderRadius: 1,
                  border: factor.isNew
                    ? '1px solid rgba(33, 150, 243, 0.5)'
                    : `1px solid ${impactConfig.color}44`,
                  animation: enablePulseAnimation && (factor.isNew || factor.impact === 'critical')
                    ? 'factor-pulse 2s ease-in-out infinite'
                    : 'none',
                  '@keyframes factor-pulse': {
                    '0%, 100%': {
                      boxShadow: `0 0 0 0 ${impactConfig.color}66`
                    },
                    '50%': {
                      boxShadow: `0 0 15px 5px ${impactConfig.color}00`
                    }
                  }
                }}
              >
                {/* New Badge */}
                {factor.isNew && (
                  <Fade in timeout={animationDuration}>
                    <Chip
                      label="NEW"
                      size="small"
                      sx={{
                        position: 'absolute',
                        top: -8,
                        right: 8,
                        height: 16,
                        fontSize: '9px',
                        fontWeight: 'bold',
                        backgroundColor: 'primary.main',
                        color: 'white'
                      }}
                    />
                  </Fade>
                )}

                {/* Factor Header */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {sentimentConfig.icon}
                    <Tooltip title={factor.description} arrow>
                      <Typography variant="body2" fontWeight="bold" color="white" sx={{ cursor: 'help' }}>
                        {factor.name}
                      </Typography>
                    </Tooltip>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {/* Change Indicator */}
                    {changePercent !== null && (
                      <Fade in timeout={animationDuration}>
                        <Chip
                          label={`${changePercent > 0 ? '+' : ''}${changePercent.toFixed(0)}%`}
                          size="small"
                          sx={{
                            height: 18,
                            fontSize: '9px',
                            fontWeight: 'bold',
                            backgroundColor: changePercent > 0 ? '#4caf5033' : '#f4433633',
                            color: changePercent > 0 ? '#4caf50' : '#f44336',
                            border: `1px solid ${changePercent > 0 ? '#4caf50' : '#f44336'}44`
                          }}
                        />
                      </Fade>
                    )}

                    {/* Impact Badge */}
                    {showImpactBadges && (
                      <Chip
                        icon={impactConfig.icon}
                        label={impactConfig.label}
                        size="small"
                        sx={{
                          height: 18,
                          fontSize: '9px',
                          fontWeight: 'bold',
                          backgroundColor: `${impactConfig.color}22`,
                          color: impactConfig.color,
                          border: `1px solid ${impactConfig.color}44`,
                          '& .MuiChip-icon': {
                            color: impactConfig.color
                          }
                        }}
                      />
                    )}
                  </Box>
                </Box>

                {/* Progress Bar */}
                <Box sx={{ mb: 0.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
                      Strength
                    </Typography>
                    <Typography
                      variant="caption"
                      fontWeight="bold"
                      sx={{ fontSize: '10px', color: sentimentConfig.color }}
                    >
                      {Math.round(animatedValue)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={animatedValue}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: `${sentimentConfig.color}22`,
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: sentimentConfig.color,
                        borderRadius: 3,
                        transition: 'transform 0.3s ease',
                        boxShadow: factor.impact === 'critical'
                          ? `0 0 8px ${sentimentConfig.color}`
                          : 'none'
                      }
                    }}
                  />
                </Box>

                {/* Description */}
                <Typography
                  variant="caption"
                  color="rgba(255, 255, 255, 0.6)"
                  sx={{ fontSize: '10px', display: 'block' }}
                >
                  {factor.description}
                </Typography>

                {/* Critical Indicator */}
                {factor.impact === 'critical' && (
                  <Box
                    sx={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      bottom: 0,
                      width: 3,
                      backgroundColor: impactConfig.color,
                      borderTopLeftRadius: 4,
                      borderBottomLeftRadius: 4,
                      boxShadow: `0 0 10px ${impactConfig.color}`,
                      animation: 'critical-pulse 1s ease-in-out infinite',
                      '@keyframes critical-pulse': {
                        '0%, 100%': { opacity: 1 },
                        '50%': { opacity: 0.5 }
                      }
                    }}
                  />
                )}
              </Box>
            </Zoom>
          );
        })}
      </Box>

      {/* Empty State */}
      {factors.length === 0 && (
        <Box
          sx={{
            p: 3,
            textAlign: 'center',
            color: 'rgba(255, 255, 255, 0.5)'
          }}
        >
          <Typography variant="body2">
            No decision factors available
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

/**
 * Single Pulsing Factor Badge
 */
interface PulsingFactorBadgeProps {
  factor: DecisionFactor;
  size?: 'small' | 'medium' | 'large';
}

export const PulsingFactorBadge: React.FC<PulsingFactorBadgeProps> = ({
  factor,
  size = 'medium'
}) => {
  const impactConfig = (() => {
    switch (factor.impact) {
      case 'critical':
        return { color: '#f44336' };
      case 'high':
        return { color: '#ff9800' };
      case 'medium':
        return { color: '#2196f3' };
      case 'low':
        return { color: '#9e9e9e' };
      default:
        return { color: '#9e9e9e' };
    }
  })();

  const sizeMap = {
    small: 8,
    medium: 12,
    large: 16
  };

  return (
    <Tooltip title={`${factor.name}: ${factor.value}%`} arrow>
      <Box
        sx={{
          width: sizeMap[size],
          height: sizeMap[size],
          borderRadius: '50%',
          backgroundColor: impactConfig.color,
          boxShadow: `0 0 8px ${impactConfig.color}`,
          animation: factor.impact === 'critical' || factor.isNew
            ? 'badge-pulse 1.5s ease-in-out infinite'
            : 'none',
          '@keyframes badge-pulse': {
            '0%, 100%': {
              transform: 'scale(1)',
              opacity: 1
            },
            '50%': {
              transform: 'scale(1.2)',
              opacity: 0.7
            }
          }
        }}
      />
    </Tooltip>
  );
};
