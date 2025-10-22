/**
 * Action Recommendation Card
 *
 * Primary card displaying the recommended poker action with GTO frequencies,
 * strategic reasoning, and confidence metrics.
 */
import React, { useState } from 'react';
import { Box, Paper, Typography, Chip, LinearProgress, Tooltip, IconButton, Snackbar } from '@mui/material';
import { TrendingUp, TrendingDown, Remove, ContentCopy, Check } from '@mui/icons-material';

export type PokerAction = 'FOLD' | 'CHECK' | 'CALL' | 'BET' | 'RAISE' | 'ALL_IN';

interface GTOFrequencies {
  fold?: number;
  check?: number;
  call?: number;
  bet?: number;
  raise?: number;
  all_in?: number;
}

interface ActionRecommendationCardProps {
  action: PokerAction;
  amount?: number;
  gtoFrequencies?: GTOFrequencies;
  strategicReasoning?: string;
  confidence: number;
  isUpdating?: boolean;
}

export const ActionRecommendationCard: React.FC<ActionRecommendationCardProps> = React.memo(({
  action,
  amount,
  gtoFrequencies,
  strategicReasoning = 'Optimal play based on current situation',
  confidence,
  isUpdating = false
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyToClipboard = async () => {
    const copyText = `Action: ${action}${amount ? ` ${formatAmount(amount)}` : ''}\nConfidence: ${(confidence * 100).toFixed(0)}%\nReasoning: ${strategicReasoning}`;

    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getActionColor = (action: PokerAction): string => {
    switch (action) {
      case 'FOLD': return '#f44336';
      case 'CHECK': return '#4caf50';
      case 'CALL': return '#2196f3';
      case 'BET': return '#ff9800';
      case 'RAISE': return '#ff5722';
      case 'ALL_IN': return '#e91e63';
      default: return '#9e9e9e';
    }
  };

  const getActionIcon = (action: PokerAction) => {
    switch (action) {
      case 'FOLD': return <TrendingDown />;
      case 'RAISE': case 'BET': case 'ALL_IN': return <TrendingUp />;
      default: return <Remove />;
    }
  };

  const formatAmount = (amount?: number): string => {
    if (!amount) return '';
    return `$${amount.toFixed(2)}`;
  };

  const getConfidenceColor = (): string => {
    if (confidence >= 0.8) return '#4caf50';
    if (confidence >= 0.6) return '#ff9800';
    return '#f44336';
  };

  return (
    <Paper
      elevation={4}
      sx={{
        p: 3,
        backgroundColor: 'rgba(33, 33, 33, 0.95)',
        border: `3px solid ${getActionColor(action)}`,
        borderRadius: 2,
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: `0 8px 24px ${getActionColor(action)}66`
        }
      }}
    >
      {/* Loading Indicator */}
      {isUpdating && (
        <LinearProgress
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 2
          }}
        />
      )}

      {/* Copy Button */}
      <Tooltip title={copied ? 'Copied!' : 'Copy recommendation'}>
        <IconButton
          onClick={handleCopyToClipboard}
          size="small"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            color: copied ? '#4caf50' : 'rgba(255, 255, 255, 0.7)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }
          }}
        >
          {copied ? <Check fontSize="small" /> : <ContentCopy fontSize="small" />}
        </IconButton>
      </Tooltip>

      {/* Main Action Display */}
      <Box sx={{
        textAlign: 'center',
        mb: 2,
        animation: 'fadeInScale 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
        '@keyframes fadeInScale': {
          '0%': { opacity: 0, transform: 'scale(0.9)' },
          '100%': { opacity: 1, transform: 'scale(1)' }
        }
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, mb: 1 }}>
          <Box sx={{
            color: getActionColor(action),
            fontSize: 40,
            transition: 'all 0.3s ease',
            animation: 'iconPulse 0.6s ease-in-out',
            '@keyframes iconPulse': {
              '0%, 100%': { transform: 'scale(1)' },
              '50%': { transform: 'scale(1.1)' }
            }
          }}>
            {getActionIcon(action)}
          </Box>
          <Typography
            variant="h3"
            fontWeight="bold"
            sx={{
              color: getActionColor(action),
              transition: 'color 0.4s ease'
            }}
          >
            {action}
          </Typography>
        </Box>

        {amount && (
          <Typography
            variant="h5"
            color="white"
            fontWeight="medium"
            sx={{
              transition: 'all 0.3s ease',
              animation: 'slideUp 0.5s ease-out',
              '@keyframes slideUp': {
                '0%': { opacity: 0, transform: 'translateY(10px)' },
                '100%': { opacity: 1, transform: 'translateY(0)' }
              }
            }}>
            {formatAmount(amount)}
          </Typography>
        )}
      </Box>

      {/* GTO Frequencies */}
      {gtoFrequencies && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 1 }}>
            GTO Frequency Mix:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
            {Object.entries(gtoFrequencies)
              .filter(([_, freq]) => freq && freq > 0)
              .sort(([_, a], [__, b]) => (b || 0) - (a || 0))
              .map(([actionType, frequency]) => (
                <Chip
                  key={actionType}
                  label={`${actionType.toUpperCase()}: ${((frequency || 0) * 100).toFixed(0)}%`}
                  size="small"
                  sx={{
                    backgroundColor: actionType === action.toLowerCase()
                      ? getActionColor(action)
                      : 'rgba(255, 255, 255, 0.1)',
                    color: 'white',
                    fontWeight: actionType === action.toLowerCase() ? 'bold' : 'normal'
                  }}
                />
              ))}
          </Box>
        </Box>
      )}

      {/* Strategic Reasoning */}
      <Box sx={{ mb: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="rgba(255, 255, 255, 0.9)" fontStyle="italic">
          💡 {strategicReasoning}
        </Typography>
      </Box>

      {/* Alternative Actions */}
      {gtoFrequencies && (
        <Box sx={{ mb: 2, p: 1.5, backgroundColor: 'rgba(255, 255, 255, 0.03)', borderRadius: 1 }}>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 1, fontWeight: 'bold' }}>
            Alternative Actions
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {Object.entries(gtoFrequencies)
              .filter(([actionType, freq]) => actionType !== action.toLowerCase() && freq && freq > 5)
              .sort(([, freqA], [, freqB]) => (freqB || 0) - (freqA || 0))
              .slice(0, 2)
              .map(([actionType, freq]) => (
                <Box
                  key={actionType}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 0.5
                  }}
                >
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.7)">
                    {actionType.toUpperCase().replace('_', ' ')}
                  </Typography>
                  <Chip
                    label={`${freq?.toFixed(0)}%`}
                    size="small"
                    sx={{
                      height: 18,
                      fontSize: '10px',
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      color: 'rgba(255, 255, 255, 0.7)'
                    }}
                  />
                </Box>
              ))}
          </Box>
        </Box>
      )}

      {/* Confidence Meter */}
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
          <Typography variant="caption" color="textSecondary">
            Confidence
          </Typography>
          <Typography variant="caption" fontWeight="bold" sx={{ color: getConfidenceColor() }}>
            {(confidence * 100).toFixed(0)}%
          </Typography>
        </Box>
        <Tooltip title={`Recommendation confidence: ${(confidence * 100).toFixed(1)}%`}>
          <LinearProgress
            variant="determinate"
            value={confidence * 100}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getConfidenceColor(),
                borderRadius: 4
              }
            }}
          />
        </Tooltip>
      </Box>

      {/* Strength Border Animation */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          border: `2px solid ${getConfidenceColor()}`,
          borderRadius: 2,
          opacity: 0.3,
          pointerEvents: 'none',
          animation: confidence >= 0.8 ? 'pulse 2s infinite' : 'none',
          '@keyframes pulse': {
            '0%, 100%': { opacity: 0.3 },
            '50%': { opacity: 0.6 }
          }
        }}
      />
    </Paper>
  );
});

ActionRecommendationCard.displayName = 'ActionRecommendationCard';
