/**
 * Reasoning Panel Component
 *
 * Displays factor-weight scoring system showing why a specific action was recommended.
 * Shows weighted factors with color-coding and expandable details.
 */
import React, { useState } from 'react';
import { Box, Paper, Typography, Chip, Collapse, IconButton, Tooltip } from '@mui/material';
import { ExpandMore, TrendingUp, TrendingDown } from '@mui/icons-material';

export interface DecisionFactor {
  name: string;
  score: number;
  weight: number;
  description: string;
  details?: string;
}

interface ReasoningPanelProps {
  factors: DecisionFactor[];
  netConfidence: number;
}

export const ReasoningPanel: React.FC<ReasoningPanelProps> = React.memo(({
  factors,
  netConfidence
}) => {
  const [expandedFactor, setExpandedFactor] = useState<string | null>(null);

  const getFactorColor = (score: number): string => {
    if (score >= 5) return '#4caf50';
    if (score >= 0) return '#8bc34a';
    if (score >= -5) return '#ff9800';
    return '#f44336';
  };

  const getConfidenceLevel = (confidence: number): string => {
    if (confidence >= 15) return 'STRONG';
    if (confidence >= 5) return 'MODERATE';
    if (confidence >= -5) return 'WEAK';
    return 'VERY WEAK';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 15) return '#4caf50';
    if (confidence >= 5) return '#8bc34a';
    if (confidence >= -5) return '#ff9800';
    return '#f44336';
  };

  const handleFactorClick = (factorName: string) => {
    setExpandedFactor(expandedFactor === factorName ? null : factorName);
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
      <Typography variant="h6" fontWeight="bold" color="white" gutterBottom>
        📊 Why This Action?
      </Typography>

      {/* Factors List */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
        {factors.map((factor) => (
          <Box key={factor.name}>
            <Box
              onClick={() => handleFactorClick(factor.name)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                p: 1.5,
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 1,
                cursor: factor.details ? 'pointer' : 'default',
                transition: 'all 0.2s',
                '&:hover': {
                  backgroundColor: factor.details ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.05)'
                }
              }}
            >
              {/* Factor Name and Icon */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                {factor.score >= 0 ? (
                  <TrendingUp sx={{ color: getFactorColor(factor.score), fontSize: 20 }} />
                ) : (
                  <TrendingDown sx={{ color: getFactorColor(factor.score), fontSize: 20 }} />
                )}
                <Typography variant="body2" color="white" fontWeight="medium">
                  {factor.name}
                </Typography>
              </Box>

              {/* Score Display */}
              <Tooltip title={factor.description}>
                <Chip
                  label={`${factor.score > 0 ? '+' : ''}${factor.score}`}
                  size="small"
                  sx={{
                    backgroundColor: getFactorColor(factor.score),
                    color: 'white',
                    fontWeight: 'bold',
                    minWidth: '60px'
                  }}
                />
              </Tooltip>

              {/* Expand Icon */}
              {factor.details && (
                <IconButton
                  size="small"
                  sx={{
                    ml: 1,
                    transform: expandedFactor === factor.name ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s'
                  }}
                >
                  <ExpandMore sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: 20 }} />
                </IconButton>
              )}
            </Box>

            {/* Expanded Details */}
            {factor.details && (
              <Collapse in={expandedFactor === factor.name}>
                <Box
                  sx={{
                    p: 1.5,
                    mt: 0.5,
                    backgroundColor: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: 1,
                    borderLeft: `3px solid ${getFactorColor(factor.score)}`
                  }}
                >
                  <Typography variant="caption" color="rgba(255, 255, 255, 0.8)">
                    {factor.details}
                  </Typography>
                </Box>
              </Collapse>
            )}
          </Box>
        ))}
      </Box>

      {/* Net Confidence Summary */}
      <Box
        sx={{
          p: 2,
          backgroundColor: `${getConfidenceColor(netConfidence)}22`,
          borderRadius: 1,
          border: `2px solid ${getConfidenceColor(netConfidence)}`,
          textAlign: 'center'
        }}
      >
        <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
          Net Decision Confidence
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <Typography
            variant="h5"
            fontWeight="bold"
            sx={{ color: getConfidenceColor(netConfidence) }}
          >
            {netConfidence > 0 ? '+' : ''}{netConfidence}
          </Typography>
          <Chip
            label={getConfidenceLevel(netConfidence)}
            size="small"
            sx={{
              backgroundColor: getConfidenceColor(netConfidence),
              color: 'white',
              fontWeight: 'bold'
            }}
          />
        </Box>
      </Box>
    </Paper>
  );
});

ReasoningPanel.displayName = 'ReasoningPanel';


/**
 * Helper function to create decision factors
 */
export function createDecisionFactor(
  name: string,
  score: number,
  description: string,
  details?: string
): DecisionFactor {
  return {
    name,
    score,
    weight: 1.0,
    description,
    details
  };
}
