/**
 * Action History Timeline Component
 *
 * Shows the last 5 action recommendations with timestamps
 */
import React from 'react';
import { Box, Paper, Typography, Chip, Tooltip } from '@mui/material';
import { Timeline, TimelineItem, TimelineSeparator, TimelineConnector, TimelineContent, TimelineDot } from '@mui/lab';
import { History, TrendingUp, TrendingDown, Remove } from '@mui/icons-material';
import { PokerAction } from './ActionRecommendationCard';

export interface ActionHistoryItem {
  id: string;
  action: PokerAction;
  amount?: number;
  confidence: number;
  timestamp: number;
  street: string;
}

interface ActionHistoryProps {
  history: ActionHistoryItem[];
}

export const ActionHistory: React.FC<ActionHistoryProps> = React.memo(({ history }) => {
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
      case 'FOLD': return <TrendingDown fontSize="small" />;
      case 'RAISE': case 'BET': case 'ALL_IN': return <TrendingUp fontSize="small" />;
      default: return <Remove fontSize="small" />;
    }
  };

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatAmount = (amount?: number): string => {
    if (!amount) return '';
    return `$${amount.toFixed(2)}`;
  };

  // Show last 5 items, most recent first
  const recentHistory = history.slice(-5).reverse();

  if (recentHistory.length === 0) {
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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <History sx={{ color: 'primary.main', fontSize: 24 }} />
          <Typography variant="subtitle1" fontWeight="bold" color="white">
            Recommendation History
          </Typography>
        </Box>
        <Typography variant="body2" color="textSecondary" textAlign="center" sx={{ py: 2 }}>
          No recommendation history yet. Recommendations will appear here as they are generated.
        </Typography>
      </Paper>
    );
  }

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
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <History sx={{ color: 'primary.main', fontSize: 24 }} />
        <Typography variant="subtitle1" fontWeight="bold" color="white">
          Recommendation History
        </Typography>
        <Chip
          label={`${history.length} total`}
          size="small"
          sx={{
            height: 20,
            fontSize: '10px',
            ml: 'auto'
          }}
        />
      </Box>

      <Timeline
        sx={{
          p: 0,
          m: 0,
          '& .MuiTimelineItem-root:before': {
            flex: 0,
            padding: 0
          }
        }}
      >
        {recentHistory.map((item, index) => (
          <TimelineItem key={item.id}>
            <TimelineSeparator>
              <Tooltip title={item.action}>
                <TimelineDot
                  sx={{
                    bgcolor: getActionColor(item.action),
                    boxShadow: `0 0 8px ${getActionColor(item.action)}66`
                  }}
                >
                  {getActionIcon(item.action)}
                </TimelineDot>
              </Tooltip>
              {index < recentHistory.length - 1 && (
                <TimelineConnector sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)' }} />
              )}
            </TimelineSeparator>
            <TimelineContent sx={{ py: 1, px: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography
                  variant="body2"
                  fontWeight="bold"
                  sx={{ color: getActionColor(item.action) }}
                >
                  {item.action}
                </Typography>
                {item.amount && (
                  <Typography variant="body2" color="rgba(255, 255, 255, 0.7)">
                    {formatAmount(item.amount)}
                  </Typography>
                )}
                <Chip
                  label={`${(item.confidence * 100).toFixed(0)}%`}
                  size="small"
                  sx={{
                    height: 18,
                    fontSize: '10px',
                    backgroundColor: item.confidence >= 0.8 ? '#4caf50' : item.confidence >= 0.6 ? '#ff9800' : '#f44336',
                    color: 'white'
                  }}
                />
              </Box>
              <Typography variant="caption" color="textSecondary">
                {item.street} • {formatTimestamp(item.timestamp)}
              </Typography>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>

      {history.length > 5 && (
        <Typography variant="caption" color="textSecondary" textAlign="center" sx={{ display: 'block', mt: 1 }}>
          Showing last 5 of {history.length} recommendations
        </Typography>
      )}
    </Paper>
  );
});

ActionHistory.displayName = 'ActionHistory';
