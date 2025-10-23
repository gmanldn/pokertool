import React from 'react';
import {
  Box,
  Skeleton,
  CircularProgress,
  LinearProgress,
  Typography,
} from '@mui/material';
import styles from './Loading.module.css';

interface LoadingProps {
  variant?: 'spinner' | 'linear' | 'skeleton' | 'text';
  size?: 'small' | 'medium' | 'large';
  text?: string;
  fullScreen?: boolean;
}

/**
 * Versatile loading component with multiple variants
 * 
 * @example
 * ```tsx
 * // Spinner
 * <Loading variant="spinner" size="large" text="Loading..." />
 * 
 * // Linear progress
 * <Loading variant="linear" />
 * 
 * // Skeleton loader
 * <Loading variant="skeleton" />
 * ```
 */
export const Loading: React.FC<LoadingProps> = ({
  variant = 'spinner',
  size = 'medium',
  text,
  fullScreen = false,
}) => {
  const getSizeValue = () => {
    switch (size) {
      case 'small':
        return 24;
      case 'medium':
        return 40;
      case 'large':
        return 60;
      default:
        return 40;
    }
  };

  const renderContent = () => {
    switch (variant) {
      case 'spinner':
        return (
          <Box className={styles.spinnerContainer}>
            <CircularProgress size={getSizeValue()} />
            {text && (
              <Typography variant="body2" className={styles.loadingText}>
                {text}
              </Typography>
            )}
          </Box>
        );

      case 'linear':
        return (
          <Box className={styles.linearContainer}>
            <LinearProgress />
            {text && (
              <Typography
                variant="caption"
                className={styles.loadingText}
                sx={{ mt: 1 }}
              >
                {text}
              </Typography>
            )}
          </Box>
        );

      case 'skeleton':
        return (
          <Box className={styles.skeletonContainer}>
            <Skeleton variant="rectangular" height={60} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="text" width="60%" />
          </Box>
        );

      case 'text':
        return (
          <Typography variant="body2" className={styles.loadingText}>
            {text || 'Loading...'}
          </Typography>
        );

      default:
        return null;
    }
  };

  if (fullScreen) {
    return (
      <Box className={styles.fullScreenContainer}>{renderContent()}</Box>
    );
  }

  return <Box className={styles.container}>{renderContent()}</Box>;
};

// Specialized skeleton loaders for common UI patterns
export const TableSkeleton: React.FC = () => (
  <Box className={styles.skeletonContainer}>
    <Skeleton variant="rectangular" height={40} sx={{ mb: 2 }} />
    {[...Array(5)].map((_, index) => (
      <Skeleton
        key={index}
        variant="rectangular"
        height={60}
        sx={{ mb: 1 }}
      />
    ))}
  </Box>
);

export const CardSkeleton: React.FC = () => (
  <Box className={styles.cardSkeleton}>
    <Skeleton variant="rectangular" height={200} sx={{ mb: 2 }} />
    <Skeleton variant="text" width="80%" sx={{ mb: 1 }} />
    <Skeleton variant="text" width="60%" />
  </Box>
);

export const DashboardSkeleton: React.FC = () => (
  <Box className={styles.dashboardSkeleton}>
    <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
    <Box className={styles.gridSkeleton}>
      {[...Array(6)].map((_, index) => (
        <Skeleton
          key={index}
          variant="rectangular"
          height={150}
          sx={{ borderRadius: 2 }}
        />
      ))}
    </Box>
  </Box>
);

export const ChartSkeleton: React.FC = () => (
  <Box className={styles.chartSkeleton}>
    <Skeleton variant="rectangular" height={300} sx={{ borderRadius: 2 }} />
    <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
      <Skeleton variant="text" width="30%" />
      <Skeleton variant="text" width="30%" />
      <Skeleton variant="text" width="30%" />
    </Box>
  </Box>
);

export default Loading;
