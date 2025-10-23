/**
 * Detection State Indicator Component
 *
 * Shows visual indicators for detection states (detecting, detected, failed, etc.)
 */
import React from 'react';
import { Box, Chip, CircularProgress, Tooltip } from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  HourglassEmpty,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';

export type DetectionState = 'idle' | 'detecting' | 'detected' | 'failed' | 'low_confidence' | 'no_detection';

interface DetectionStateIndicatorProps {
  state: DetectionState;
  label?: string;
  confidence?: number;
  compact?: boolean;
  showLabel?: boolean;
}

export const DetectionStateIndicator: React.FC<DetectionStateIndicatorProps> = React.memo(({
  state,
  label = 'Detection',
  confidence,
  compact = false,
  showLabel = true
}) => {
  const getStateConfig = () => {
    switch (state) {
      case 'detecting':
        return {
          icon: <CircularProgress size={16} />,
          color: 'info' as const,
          tooltip: 'Detecting...',
          label: 'Detecting'
        };
      case 'detected':
        return {
          icon: <CheckCircle sx={{ fontSize: 16 }} />,
          color: 'success' as const,
          tooltip: confidence ? `Detected (${(confidence * 100).toFixed(0)}% confidence)` : 'Detected',
          label: 'Detected'
        };
      case 'failed':
        return {
          icon: <Error sx={{ fontSize: 16 }} />,
          color: 'error' as const,
          tooltip: 'Detection failed',
          label: 'Failed'
        };
      case 'low_confidence':
        return {
          icon: <Warning sx={{ fontSize: 16 }} />,
          color: 'warning' as const,
          tooltip: confidence ? `Low confidence (${(confidence * 100).toFixed(0)}%)` : 'Low confidence',
          label: 'Low Conf'
        };
      case 'no_detection':
        return {
          icon: <VisibilityOff sx={{ fontSize: 16 }} />,
          color: 'default' as const,
          tooltip: 'Not detected',
          label: 'No Detection'
        };
      case 'idle':
      default:
        return {
          icon: <Visibility sx={{ fontSize: 16 }} />,
          color: 'default' as const,
          tooltip: 'Idle',
          label: 'Idle'
        };
    }
  };

  const config = getStateConfig();

  if (compact) {
    return (
      <Tooltip title={config.tooltip}>
        <Box sx={{ display: 'inline-flex', alignItems: 'center' }}>
          {config.icon}
        </Box>
      </Tooltip>
    );
  }

  return (
    <Tooltip title={config.tooltip}>
      <Chip
        icon={config.icon}
        label={showLabel ? (label || config.label) : ''}
        color={config.color}
        size="small"
        sx={{
          fontWeight: 'bold',
          '& .MuiChip-icon': {
            marginLeft: '8px'
          }
        }}
      />
    </Tooltip>
  );
});

DetectionStateIndicator.displayName = 'DetectionStateIndicator';


/**
 * Detection State Grid Component
 * Shows multiple detection states in a grid layout
 */
interface DetectionStateGridProps {
  detections: Array<{
    type: string;
    state: DetectionState;
    confidence?: number;
  }>;
}

export const DetectionStateGrid: React.FC<DetectionStateGridProps> = React.memo(({ detections }) => {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, padding: 1 }}>
      {detections.map((detection) => (
        <DetectionStateIndicator
          key={detection.type}
          state={detection.state}
          label={detection.type}
          confidence={detection.confidence}
          showLabel={true}
        />
      ))}
    </Box>
  );
});

DetectionStateGrid.displayName = 'DetectionStateGrid';
