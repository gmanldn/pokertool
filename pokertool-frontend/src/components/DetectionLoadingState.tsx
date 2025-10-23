/**
 * Detection Loading State Components
 *
 * Loading indicators and skeleton screens for detection processes
 */
import React from 'react';
import {
  Box,
  Skeleton,
  CircularProgress,
  Typography,
  LinearProgress
} from '@mui/material';
import { Visibility } from '@mui/icons-material';

interface DetectionLoadingProps {
  message?: string;
  variant?: 'circular' | 'linear' | 'skeleton';
  size?: 'small' | 'medium' | 'large';
}

export const DetectionLoading: React.FC<DetectionLoadingProps> = React.memo(({
  message = 'Detecting...',
  variant = 'circular',
  size = 'medium'
}) => {
  const sizeMap = {
    small: 20,
    medium: 40,
    large: 60
  };

  if (variant === 'skeleton') {
    return (
      <Box sx={{ width: '100%', padding: 2 }}>
        <Skeleton variant="rectangular" height={40} sx={{ marginBottom: 1 }} />
        <Skeleton variant="text" width="60%" />
        <Skeleton variant="text" width="40%" />
      </Box>
    );
  }

  if (variant === 'linear') {
    return (
      <Box sx={{ width: '100%' }}>
        {message && (
          <Typography variant="caption" color="textSecondary" sx={{ marginBottom: 1 }}>
            {message}
          </Typography>
        )}
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2,
        gap: 1
      }}
    >
      <CircularProgress size={sizeMap[size]} />
      {message && (
        <Typography variant="caption" color="textSecondary">
          {message}
        </Typography>
      )}
    </Box>
  );
});

DetectionLoading.displayName = 'DetectionLoading';


/**
 * Table Detection Skeleton
 * Skeleton screen for table detection state
 */
export const TableDetectionSkeleton: React.FC = React.memo(() => {
  return (
    <Box sx={{ padding: 3 }}>
      {/* Pot skeleton */}
      <Box sx={{ textAlign: 'center', marginBottom: 3 }}>
        <Skeleton variant="text" width={120} height={40} sx={{ margin: '0 auto' }} />
      </Box>

      {/* Board cards skeleton */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, marginBottom: 3 }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} variant="rectangular" width={50} height={70} />
        ))}
      </Box>

      {/* Player seats skeleton */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
          <Box key={i} sx={{ padding: 1 }}>
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="text" width="60%" />
          </Box>
        ))}
      </Box>
    </Box>
  );
});

TableDetectionSkeleton.displayName = 'TableDetectionSkeleton';


/**
 * Card Detection Loading
 * Specialized loading indicator for card detection
 */
export const CardDetectionLoading: React.FC = React.memo(() => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        padding: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        borderRadius: 1
      }}
    >
      <CircularProgress size={20} />
      <Typography variant="caption" color="textSecondary">
        Detecting cards...
      </Typography>
    </Box>
  );
});

CardDetectionLoading.displayName = 'CardDetectionLoading';


/**
 * Player Detection Loading
 */
export const PlayerDetectionLoading: React.FC = React.memo(() => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        padding: 1
      }}
    >
      <CircularProgress size={16} color="info" />
      <Typography variant="caption" color="textSecondary">
        Detecting players...
      </Typography>
    </Box>
  );
});

PlayerDetectionLoading.displayName = 'PlayerDetectionLoading';


/**
 * Pot Detection Loading
 */
export const PotDetectionLoading: React.FC = React.memo(() => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        padding: 1
      }}
    >
      <CircularProgress size={20} color="success" />
      <Typography variant="body2" color="textSecondary">
        Detecting pot...
      </Typography>
    </Box>
  );
});

PotDetectionLoading.displayName = 'PotDetectionLoading';


/**
 * Detection Progress Component
 * Shows progress of multi-step detection process
 */
interface DetectionProgressProps {
  steps: Array<{ name: string; completed: boolean }>;
  currentStep: number;
}

export const DetectionProgress: React.FC<DetectionProgressProps> = React.memo(({
  steps,
  currentStep
}) => {
  const progress = (currentStep / steps.length) * 100;

  return (
    <Box sx={{ width: '100%', padding: 2 }}>
      <Box sx={{ marginBottom: 2 }}>
        <LinearProgress variant="determinate" value={progress} />
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {steps.map((step, index) => (
          <Box
            key={step.name}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              opacity: step.completed ? 0.5 : index === currentStep ? 1 : 0.3
            }}
          >
            {step.completed ? (
              <Box sx={{ color: 'success.main', fontSize: '16px' }}>✓</Box>
            ) : index === currentStep ? (
              <CircularProgress size={16} />
            ) : (
              <Visibility sx={{ fontSize: 16, color: 'text.disabled' }} />
            )}
            <Typography
              variant="caption"
              sx={{
                color: step.completed ? 'success.main' : index === currentStep ? 'text.primary' : 'text.disabled'
              }}
            >
              {step.name}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
});

DetectionProgress.displayName = 'DetectionProgress';
