/**
 * Confidence Indicator Component
 *
 * Visual component for displaying confidence levels with color coding
 */
import React from 'react';
import { Box, Typography, LinearProgress, Tooltip } from '@mui/material';
import {
  getConfidenceColor,
  getConfidenceLabel,
  getConfidenceMuiColor
} from '../utils/confidenceColors';

interface ConfidenceIndicatorProps {
  confidence: number;  // 0-1
  label?: string;
  showPercentage?: boolean;
  showBar?: boolean;
  compact?: boolean;
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = React.memo(({
  confidence,
  label,
  showPercentage = true,
  showBar = false,
  compact = false
}) => {
  const percentage = Math.round(confidence * 100);
  const color = getConfidenceColor(confidence);
  const levelLabel = getConfidenceLabel(confidence);
  const muiColor = getConfidenceMuiColor(confidence);

  if (compact) {
    return (
      <Tooltip title={`${percentage}% confidence (${levelLabel})`}>
        <Box
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            backgroundColor: color,
            borderRadius: '4px',
            padding: '2px 6px',
            color: 'white',
            fontSize: '12px',
            fontWeight: 'bold'
          }}
        >
          {percentage}%
        </Box>
      </Tooltip>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: showBar ? 120 : 'auto' }}>
      {label && (
        <Typography variant="caption" color="textSecondary">
          {label}
        </Typography>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {showPercentage && (
          <Typography
            variant="body2"
            fontWeight="bold"
            sx={{ color, minWidth: '45px' }}
          >
            {percentage}%
          </Typography>
        )}

        {showBar && (
          <LinearProgress
            variant="determinate"
            value={percentage}
            color={muiColor}
            sx={{
              flexGrow: 1,
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }}
          />
        )}

        <Typography
          variant="caption"
          sx={{
            color,
            fontWeight: 'bold',
            textTransform: 'uppercase',
            fontSize: '10px'
          }}
        >
          {levelLabel}
        </Typography>
      </Box>
    </Box>
  );
});

ConfidenceIndicator.displayName = 'ConfidenceIndicator';


/**
 * Confidence Badge Component
 * Simpler badge-style indicator
 */
interface ConfidenceBadgeProps {
  confidence: number;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = React.memo(({ confidence }) => {
  const percentage = Math.round(confidence * 100);
  const color = getConfidenceColor(confidence);
  const label = getConfidenceLabel(confidence);

  return (
    <Tooltip title={`${percentage}% confidence`}>
      <Box
        sx={{
          display: 'inline-block',
          backgroundColor: color,
          color: 'white',
          padding: '2px 8px',
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: 'bold',
          textTransform: 'uppercase'
        }}
      >
        {label}
      </Box>
    </Tooltip>
  );
});

ConfidenceBadge.displayName = 'ConfidenceBadge';
