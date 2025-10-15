/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/AdvicePanel.tsx
version: v76.0.0
last_commit: '2025-10-15T03:47:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Real-Time Advice Panel Component with WebSocket integration
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Collapse,
  IconButton,
  Fade,
  Grid,
  Chip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useWebSocketSubscription, WebSocketMessage } from '../hooks/useWebSocket';

// Action types
export enum ActionType {
  FOLD = 'FOLD',
  CALL = 'CALL',
  RAISE = 'RAISE',
  CHECK = 'CHECK',
  ALL_IN = 'ALL-IN',
}

// Confidence levels
export enum ConfidenceLevel {
  VERY_HIGH = 'VERY_HIGH',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW',
  VERY_LOW = 'VERY_LOW',
}

// Advice data structure
export interface Advice {
  action: ActionType;
  confidence: ConfidenceLevel;
  confidenceScore: number; // 0-100
  amount?: number;
  ev: number;
  potOdds: number;
  handStrength: number; // 0-100
  reasoning: string;
  timestamp: number;
}

interface AdvicePanelProps {
  messages: WebSocketMessage[];
  compact?: boolean;
}

// Confidence level configuration
const CONFIDENCE_CONFIG = {
  [ConfidenceLevel.VERY_HIGH]: {
    label: 'Very High',
    color: '#4caf50',
    minScore: 90,
  },
  [ConfidenceLevel.HIGH]: {
    label: 'High',
    color: '#8bc34a',
    minScore: 75,
  },
  [ConfidenceLevel.MEDIUM]: {
    label: 'Medium',
    color: '#ffc107',
    minScore: 60,
  },
  [ConfidenceLevel.LOW]: {
    label: 'Low',
    color: '#ff9800',
    minScore: 40,
  },
  [ConfidenceLevel.VERY_LOW]: {
    label: 'Very Low',
    color: '#f44336',
    minScore: 0,
  },
};

// Action colors
const ACTION_COLORS = {
  [ActionType.FOLD]: '#f44336',
  [ActionType.CALL]: '#2196f3',
  [ActionType.RAISE]: '#4caf50',
  [ActionType.CHECK]: '#9e9e9e',
  [ActionType.ALL_IN]: '#ff5722',
};

export const AdvicePanel: React.FC<AdvicePanelProps> = ({ messages, compact = false }) => {
  const [advice, setAdvice] = useState<Advice | null>(null);
  const [expanded, setExpanded] = useState(!compact);
  const [isUpdating, setIsUpdating] = useState(false);
  const lastUpdateRef = useRef<number>(0);
  const updateThrottleMs = 500; // Max 2 updates per second

  // Subscribe to advice messages
  const adviceMessages = useWebSocketSubscription(messages, 'advice');

  // Process advice updates with throttling
  useEffect(() => {
    if (adviceMessages.length === 0) return;

    const latestMessage = adviceMessages[adviceMessages.length - 1];
    const now = Date.now();

    // Throttle updates
    if (now - lastUpdateRef.current < updateThrottleMs) {
      return;
    }

    lastUpdateRef.current = now;

    // Show update animation
    setIsUpdating(true);
    setTimeout(() => setIsUpdating(false), 300);

    // Parse advice data
    try {
      const adviceData: Advice = latestMessage.data;
      setAdvice(adviceData);
    } catch (error) {
      console.error('Failed to parse advice data:', error);
    }
  }, [adviceMessages]);

  // Get confidence configuration
  const getConfidenceConfig = (level: ConfidenceLevel) => {
    return CONFIDENCE_CONFIG[level];
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
    if (ev > 10) return '#4caf50';
    if (ev > 0) return '#8bc34a';
    if (ev > -10) return '#ff9800';
    return '#f44336';
  };

  if (!advice) {
    return (
      <Card sx={{ minHeight: compact ? 120 : 200 }}>
        <CardContent>
          <Typography variant="h6" color="text.secondary" align="center">
            Waiting for advice...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const confidenceConfig = getConfidenceConfig(advice.confidence);
  const actionColor = ACTION_COLORS[advice.action];

  return (
    <Fade in={true} timeout={300}>
      <Card
        sx={{
          position: 'relative',
          overflow: 'visible',
          transition: 'all 0.3s ease',
          opacity: isUpdating ? 0.7 : 1,
        }}
      >
        <CardContent>
          {/* Primary Action */}
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Typography
              variant={compact ? 'h4' : 'h3'}
              sx={{
                fontWeight: 'bold',
                color: actionColor,
                textShadow: `0 0 10px ${actionColor}40`,
                transition: 'all 0.3s ease',
              }}
            >
              {advice.action}
              {advice.amount && advice.action === ActionType.RAISE && (
                <Typography
                  component="span"
                  variant={compact ? 'h5' : 'h4'}
                  sx={{ ml: 1, color: actionColor }}
                >
                  {formatCurrency(advice.amount)}
                </Typography>
              )}
            </Typography>
          </Box>

          {/* Confidence Bar */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Confidence
              </Typography>
              <Chip
                label={confidenceConfig.label}
                size="small"
                sx={{
                  backgroundColor: confidenceConfig.color,
                  color: 'white',
                  fontWeight: 'bold',
                }}
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={advice.confidenceScore}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(255,255,255,0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: confidenceConfig.color,
                  borderRadius: 4,
                },
              }}
            />
          </Box>

          {/* Supporting Metrics */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  EV
                </Typography>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 'bold',
                    color: getEVColor(advice.ev),
                  }}
                >
                  {advice.ev >= 0 ? '+' : ''}
                  {formatCurrency(advice.ev)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  Pot Odds
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {formatPercentage(advice.potOdds)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  Hand Strength
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {formatPercentage(advice.handStrength)}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Reasoning Section */}
          <Box>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                cursor: 'pointer',
              }}
              onClick={() => setExpanded(!expanded)}
            >
              <Typography variant="subtitle2" color="text.secondary">
                Reasoning
              </Typography>
              <IconButton size="small">
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expanded}>
              <Box
                sx={{
                  mt: 1,
                  p: 1.5,
                  backgroundColor: 'rgba(255,255,255,0.05)',
                  borderRadius: 1,
                  maxHeight: 100,
                  overflowY: 'auto',
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    lineHeight: 1.6,
                    wordWrap: 'break-word',
                  }}
                >
                  {advice.reasoning}
                </Typography>
              </Box>
            </Collapse>
          </Box>

          {/* Low Confidence Warning */}
          {advice.confidence === ConfidenceLevel.LOW ||
            advice.confidence === ConfidenceLevel.VERY_LOW ? (
            <Box
              sx={{
                mt: 2,
                p: 1,
                backgroundColor: 'rgba(255, 152, 0, 0.1)',
                borderLeft: '4px solid #ff9800',
                borderRadius: 1,
              }}
            >
              <Typography variant="caption" color="warning.main">
                ⚠️ Low confidence - consider the situation carefully
              </Typography>
            </Box>
          ) : null}
        </CardContent>
      </Card>
    </Fade>
  );
};

export default AdvicePanel;
