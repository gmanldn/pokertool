/**
 * Animated Recommendation Component
 *
 * Smooth animations for SmartHelper recommendation changes with:
 * - Slide transitions between recommendations
 * - Confidence meter animation
 * - Action highlight effects
 * - Amount counter animation
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  LinearProgress,
  Fade,
  Slide,
  Grow,
  Zoom,
  Collapse
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  CheckCircle,
  Warning
} from '@mui/icons-material';

export interface Recommendation {
  id: string;
  action: string;
  amount?: number;
  confidence: number;
  reasoning: string[];
  timestamp: Date;
}

interface AnimatedRecommendationProps {
  recommendation: Recommendation | null;
  previousRecommendation?: Recommendation | null;
  animationDuration?: number; // milliseconds
  showChangeIndicator?: boolean;
  onAnimationComplete?: () => void;
}

export const AnimatedRecommendation: React.FC<AnimatedRecommendationProps> = ({
  recommendation,
  previousRecommendation,
  animationDuration = 500,
  showChangeIndicator = true,
  onAnimationComplete
}) => {
  const [displayRecommendation, setDisplayRecommendation] = useState(recommendation);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [changeDirection, setChangeDirection] = useState<'up' | 'down' | 'same'>('same');
  const [animatedConfidence, setAnimatedConfidence] = useState(0);
  const [animatedAmount, setAnimatedAmount] = useState(0);
  const animationRef = useRef<number | null>(null);

  // Determine change direction
  useEffect(() => {
    if (recommendation && previousRecommendation) {
      if (recommendation.confidence > previousRecommendation.confidence) {
        setChangeDirection('up');
      } else if (recommendation.confidence < previousRecommendation.confidence) {
        setChangeDirection('down');
      } else {
        setChangeDirection('same');
      }
    }
  }, [recommendation, previousRecommendation]);

  // Transition animation
  useEffect(() => {
    if (!recommendation) {
      setDisplayRecommendation(null);
      return;
    }

    if (recommendation.id !== displayRecommendation?.id) {
      setIsTransitioning(true);

      // Fade out old recommendation
      setTimeout(() => {
        setDisplayRecommendation(recommendation);
        setIsTransitioning(false);

        if (onAnimationComplete) {
          setTimeout(onAnimationComplete, animationDuration);
        }
      }, animationDuration / 2);
    } else {
      setDisplayRecommendation(recommendation);
    }
  }, [recommendation, displayRecommendation, animationDuration, onAnimationComplete]);

  // Animated confidence counter
  useEffect(() => {
    if (!displayRecommendation) return;

    const targetConfidence = displayRecommendation.confidence;
    const startConfidence = animatedConfidence;
    const duration = animationDuration;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-out cubic)
      const easeOut = 1 - Math.pow(1 - progress, 3);

      const current = startConfidence + (targetConfidence - startConfidence) * easeOut;
      setAnimatedConfidence(current);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [displayRecommendation?.confidence, animationDuration]);

  // Animated amount counter
  useEffect(() => {
    if (!displayRecommendation?.amount) return;

    const targetAmount = displayRecommendation.amount;
    const startAmount = animatedAmount;
    const duration = animationDuration;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-out cubic)
      const easeOut = 1 - Math.pow(1 - progress, 3);

      const current = startAmount + (targetAmount - startAmount) * easeOut;
      setAnimatedAmount(current);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [displayRecommendation?.amount, animationDuration]);

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return '#4caf50';
    if (confidence >= 60) return '#2196f3';
    if (confidence >= 40) return '#ff9800';
    return '#f44336';
  };

  const getChangeIcon = () => {
    switch (changeDirection) {
      case 'up':
        return <TrendingUp sx={{ fontSize: 16, color: '#4caf50' }} />;
      case 'down':
        return <TrendingDown sx={{ fontSize: 16, color: '#f44336' }} />;
      default:
        return <TrendingFlat sx={{ fontSize: 16, color: '#9e9e9e' }} />;
    }
  };

  if (!displayRecommendation) {
    return (
      <Fade in={!displayRecommendation} timeout={animationDuration}>
        <Paper
          elevation={2}
          sx={{
            p: 3,
            textAlign: 'center',
            backgroundColor: 'rgba(33, 33, 33, 0.9)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2
          }}
        >
          <Typography variant="body2" color="textSecondary">
            No active recommendation
          </Typography>
        </Paper>
      </Fade>
    );
  }

  const confidenceColor = getConfidenceColor(displayRecommendation.confidence);

  return (
    <Slide
      direction="up"
      in={!isTransitioning}
      timeout={animationDuration}
      mountOnEnter
      unmountOnExit
    >
      <Paper
        elevation={2}
        sx={{
          p: 2,
          backgroundColor: 'rgba(33, 33, 33, 0.9)',
          border: `2px solid ${confidenceColor}44`,
          borderRadius: 2,
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.3s ease'
        }}
      >
        {/* Confidence Glow Effect */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 4,
            backgroundColor: confidenceColor,
            boxShadow: `0 0 20px ${confidenceColor}`,
            animation: 'pulse-glow 2s ease-in-out infinite',
            '@keyframes pulse-glow': {
              '0%, 100%': { opacity: 0.6 },
              '50%': { opacity: 1 }
            }
          }}
        />

        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Zoom in={!isTransitioning} timeout={animationDuration} style={{ transitionDelay: '100ms' }}>
              <Typography
                variant="h5"
                fontWeight="bold"
                sx={{
                  color: confidenceColor,
                  textShadow: `0 0 10px ${confidenceColor}66`
                }}
              >
                {displayRecommendation.action}
              </Typography>
            </Zoom>

            {showChangeIndicator && changeDirection !== 'same' && (
              <Grow in timeout={animationDuration}>
                {getChangeIcon()}
              </Grow>
            )}
          </Box>

          <Zoom in={!isTransitioning} timeout={animationDuration} style={{ transitionDelay: '200ms' }}>
            <Chip
              label={`${Math.round(animatedConfidence)}%`}
              size="small"
              icon={
                displayRecommendation.confidence >= 70 ? (
                  <CheckCircle sx={{ fontSize: 14 }} />
                ) : (
                  <Warning sx={{ fontSize: 14 }} />
                )
              }
              sx={{
                height: 28,
                fontSize: '13px',
                fontWeight: 'bold',
                backgroundColor: confidenceColor,
                color: 'white',
                '& .MuiChip-icon': {
                  color: 'white'
                }
              }}
            />
          </Zoom>
        </Box>

        {/* Confidence Bar */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" color="textSecondary">
              Confidence
            </Typography>
            <Typography variant="caption" fontWeight="bold" sx={{ color: confidenceColor }}>
              {Math.round(animatedConfidence)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={animatedConfidence}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: `${confidenceColor}22`,
              '& .MuiLinearProgress-bar': {
                backgroundColor: confidenceColor,
                borderRadius: 4,
                transition: 'transform 0.3s ease'
              }
            }}
          />
        </Box>

        {/* Amount */}
        {displayRecommendation.amount !== undefined && (
          <Fade in={!isTransitioning} timeout={animationDuration} style={{ transitionDelay: '300ms' }}>
            <Box
              sx={{
                mb: 2,
                p: 1.5,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 1,
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
                Recommended Amount
              </Typography>
              <Typography
                variant="h6"
                fontWeight="bold"
                sx={{
                  color: confidenceColor,
                  fontFamily: 'monospace'
                }}
              >
                ${animatedAmount.toFixed(2)}
              </Typography>
            </Box>
          </Fade>
        )}

        {/* Reasoning */}
        <Collapse in={!isTransitioning} timeout={animationDuration}>
          <Box>
            <Typography variant="caption" fontWeight="bold" color="textSecondary" sx={{ display: 'block', mb: 1 }}>
              Reasoning
            </Typography>
            {displayRecommendation.reasoning.map((reason, index) => (
              <Fade
                key={index}
                in={!isTransitioning}
                timeout={animationDuration}
                style={{ transitionDelay: `${400 + index * 100}ms` }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 0.5 }}>
                  <Box
                    sx={{
                      width: 4,
                      height: 4,
                      borderRadius: '50%',
                      backgroundColor: confidenceColor,
                      mt: 0.75,
                      flexShrink: 0
                    }}
                  />
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.8)" sx={{ fontSize: '11px' }}>
                    {reason}
                  </Typography>
                </Box>
              </Fade>
            ))}
          </Box>
        </Collapse>

        {/* Timestamp */}
        <Fade in={!isTransitioning} timeout={animationDuration} style={{ transitionDelay: '500ms' }}>
          <Typography
            variant="caption"
            color="textSecondary"
            sx={{ display: 'block', mt: 1, fontSize: '9px', textAlign: 'right' }}
          >
            Updated {displayRecommendation.timestamp.toLocaleTimeString()}
          </Typography>
        </Fade>
      </Paper>
    </Slide>
  );
};

/**
 * Pulse animation for urgent recommendations
 */
interface PulseRecommendationProps {
  children: React.ReactNode;
  isUrgent?: boolean;
  pulseColor?: string;
}

export const PulseRecommendation: React.FC<PulseRecommendationProps> = ({
  children,
  isUrgent = false,
  pulseColor = '#f44336'
}) => (
  <Box
    sx={{
      position: 'relative',
      animation: isUrgent ? 'urgent-pulse 1.5s ease-in-out infinite' : 'none',
      '@keyframes urgent-pulse': {
        '0%, 100%': {
          boxShadow: `0 0 0 0 ${pulseColor}66`
        },
        '50%': {
          boxShadow: `0 0 20px 10px ${pulseColor}00`
        }
      }
    }}
  >
    {children}
  </Box>
);
