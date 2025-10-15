/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/AlternativeActions.tsx
version: v76.0.0
last_commit: '2025-10-15T03:47:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Alternative Actions Suggester component
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Collapse,
  IconButton,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { ActionType, ConfidenceLevel } from './AdvicePanel';
import { useWebSocketSubscription, WebSocketMessage } from '../hooks/useWebSocket';

// Alternative action data structure
export interface AlternativeAction {
  action: ActionType;
  amount?: number;
  ev: number;
  evDifference: number; // Difference from primary action EV
  winProbability: number; // 0-100
  reasoning: string;
  viability: 'close' | 'suboptimal' | 'bad';
}

interface AlternativeActionsData {
  primaryEV: number;
  alternatives: AlternativeAction[];
  timestamp: number;
}

interface AlternativeActionsProps {
  messages: WebSocketMessage[];
  maxAlternatives?: number;
}

// Viability configuration
const VIABILITY_CONFIG = {
  close: {
    label: 'Close Alternative',
    color: '#4caf50',
    maxEVDiff: 5,
  },
  suboptimal: {
    label: 'Suboptimal',
    color: '#ffc107',
    maxEVDiff: 15,
  },
  bad: {
    label: 'Not Recommended',
    color: '#f44336',
    maxEVDiff: Infinity,
  },
};

// Determine viability based on EV difference
const getViability = (evDiff: number): 'close' | 'suboptimal' | 'bad' => {
  const absEvDiff = Math.abs(evDiff);
  if (absEvDiff <= VIABILITY_CONFIG.close.maxEVDiff) return 'close';
  if (absEvDiff <= VIABILITY_CONFIG.suboptimal.maxEVDiff) return 'suboptimal';
  return 'bad';
};

export const AlternativeActions: React.FC<AlternativeActionsProps> = ({
  messages,
  maxAlternatives = 3,
}) => {
  const [alternativesData, setAlternativesData] = useState<AlternativeActionsData | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [expandedAlternative, setExpandedAlternative] = useState<number | null>(null);

  // Subscribe to alternative actions messages
  const alternativeMessages = useWebSocketSubscription(messages, 'alternative_actions');

  // Process alternative actions updates
  useEffect(() => {
    if (alternativeMessages.length === 0) return;

    const latestMessage = alternativeMessages[alternativeMessages.length - 1];

    try {
      const data: AlternativeActionsData = latestMessage.data;
      
      // Sort alternatives by EV (highest first)
      const sortedAlternatives = [...data.alternatives].sort((a, b) => b.ev - a.ev);
      
      // Limit to maxAlternatives
      const limitedAlternatives = sortedAlternatives.slice(0, maxAlternatives);
      
      // Calculate viability for each alternative
      const alternativesWithViability = limitedAlternatives.map(alt => ({
        ...alt,
        viability: getViability(alt.evDifference),
      }));

      setAlternativesData({
        ...data,
        alternatives: alternativesWithViability,
      });
    } catch (error) {
      console.error('Failed to parse alternative actions data:', error);
    }
  }, [alternativeMessages, maxAlternatives]);

  // Format currency
  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(2)}`;
  };

  // Format EV difference
  const formatEVDifference = (evDiff: number): string => {
    const sign = evDiff >= 0 ? '+' : '';
    return `${sign}${formatCurrency(evDiff)}`;
  };

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  // Toggle alternative detail expansion
  const toggleAlternative = (index: number) => {
    setExpandedAlternative(expandedAlternative === index ? null : index);
  };

  if (!alternativesData || alternativesData.alternatives.length === 0) {
    return null;
  }

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
          }}
          onClick={() => setExpanded(!expanded)}
        >
          <Typography variant="h6">
            Alternative Actions ({alternativesData.alternatives.length})
          </Typography>
          <IconButton size="small">
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={expanded}>
          <Divider sx={{ my: 2 }} />
          
          <List sx={{ p: 0 }}>
            {alternativesData.alternatives.map((alternative, index) => {
              const viabilityConfig = VIABILITY_CONFIG[alternative.viability];
              const isExpanded = expandedAlternative === index;

              return (
                <React.Fragment key={index}>
                  <ListItem
                    sx={{
                      flexDirection: 'column',
                      alignItems: 'stretch',
                      p: 2,
                      borderRadius: 1,
                      backgroundColor: 'rgba(255,255,255,0.03)',
                      mb: 1,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        backgroundColor: 'rgba(255,255,255,0.05)',
                      },
                    }}
                    onClick={() => toggleAlternative(index)}
                  >
                    {/* Action Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                          {alternative.action}
                          {alternative.amount && (
                            <Typography
                              component="span"
                              variant="body1"
                              sx={{ ml: 1, fontWeight: 'normal' }}
                            >
                              {formatCurrency(alternative.amount)}
                            </Typography>
                          )}
                        </Typography>
                        <Chip
                          label={viabilityConfig.label}
                          size="small"
                          sx={{
                            backgroundColor: viabilityConfig.color,
                            color: 'white',
                            fontWeight: 'bold',
                          }}
                        />
                      </Box>
                      <IconButton size="small">
                        {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Box>

                    {/* Metrics Row */}
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-around',
                        gap: 2,
                        mb: isExpanded ? 1 : 0,
                      }}
                    >
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          EV Difference
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {alternative.evDifference > 0 ? (
                            <TrendingUpIcon fontSize="small" sx={{ color: '#4caf50', mr: 0.5 }} />
                          ) : (
                            <TrendingDownIcon fontSize="small" sx={{ color: '#f44336', mr: 0.5 }} />
                          )}
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 'bold',
                              color: alternative.evDifference >= 0 ? '#4caf50' : '#f44336',
                            }}
                          >
                            {formatEVDifference(alternative.evDifference)}
                          </Typography>
                        </Box>
                      </Box>

                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          Expected Value
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {formatCurrency(alternative.ev)}
                        </Typography>
                      </Box>

                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          Win Probability
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {formatPercentage(alternative.winProbability)}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Reasoning (Expanded) */}
                    <Collapse in={isExpanded}>
                      <Divider sx={{ my: 1.5 }} />
                      <Box
                        sx={{
                          p: 1.5,
                          backgroundColor: 'rgba(255,255,255,0.05)',
                          borderRadius: 1,
                        }}
                      >
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                          Reasoning:
                        </Typography>
                        <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                          {alternative.reasoning}
                        </Typography>
                      </Box>
                    </Collapse>
                  </ListItem>
                </React.Fragment>
              );
            })}
          </List>

          {/* Summary Note */}
          <Box
            sx={{
              mt: 2,
              p: 1.5,
              backgroundColor: 'rgba(33, 150, 243, 0.1)',
              borderLeft: '4px solid #2196f3',
              borderRadius: 1,
            }}
          >
            <Typography variant="caption" color="primary.main">
              💡 Click on an alternative to see detailed reasoning. EV differences show how much
              better (+) or worse (-) each option is compared to the primary recommendation.
            </Typography>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default AlternativeActions;
