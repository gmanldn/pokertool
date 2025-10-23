import React from 'react';
import { Box, Typography, LinearProgress, Tooltip } from '@mui/material';
import { CheckCircle, Warning, Error } from '@mui/icons-material';
import styles from './ConfidenceMeter.module.css';

interface ConfidenceMeterProps {
  confidence: number; // 0-100
  showLabel?: boolean;
  showIcon?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  confidence,
  showLabel = true,
  showIcon = true,
  size = 'medium',
}) => {
  // Clamp confidence between 0 and 100
  const clampedConfidence = Math.max(0, Math.min(100, confidence));

  // Determine confidence level
  const getConfidenceLevel = () => {
    if (clampedConfidence >= 80) return 'high';
    if (clampedConfidence >= 60) return 'medium';
    if (clampedConfidence >= 40) return 'low';
    return 'very-low';
  };

  const level = getConfidenceLevel();

  // Get color based on confidence level
  const getColor = () => {
    switch (level) {
      case 'high':
        return '#4caf50'; // Green
      case 'medium':
        return '#ff9800'; // Orange
      case 'low':
        return '#ff5722'; // Deep orange
      case 'very-low':
        return '#f44336'; // Red
      default:
        return '#9e9e9e'; // Grey
    }
  };

  // Get icon based on confidence level
  const getIcon = () => {
    switch (level) {
      case 'high':
        return <CheckCircle className={styles.iconHigh} />;
      case 'medium':
        return <Warning className={styles.iconMedium} />;
      case 'low':
      case 'very-low':
        return <Error className={styles.iconLow} />;
      default:
        return null;
    }
  };

  // Get label text
  const getLabelText = () => {
    switch (level) {
      case 'high':
        return 'High Confidence';
      case 'medium':
        return 'Medium Confidence';
      case 'low':
        return 'Low Confidence';
      case 'very-low':
        return 'Very Low Confidence';
      default:
        return 'Unknown';
    }
  };

  const color = getColor();
  const sizeClass = size === 'small' ? styles.sizeSmall : size === 'large' ? styles.sizeLarge : styles.sizeMedium;

  return (
    <Tooltip
      title={`${clampedConfidence.toFixed(0)}% confidence in this recommendation`}
      arrow
    >
      <Box className={`${styles.container} ${sizeClass}`}>
        {showIcon && (
          <Box className={styles.iconContainer}>{getIcon()}</Box>
        )}

        <Box className={styles.meterContainer}>
          {showLabel && (
            <Box className={styles.labelContainer}>
              <Typography variant="caption" className={styles.label}>
                {getLabelText()}
              </Typography>
              <Typography
                variant="caption"
                className={styles.percentage}
                sx={{ color }}
              >
                {clampedConfidence.toFixed(0)}%
              </Typography>
            </Box>
          )}

          <LinearProgress
            variant="determinate"
            value={clampedConfidence}
            className={`${styles.progressBar} ${
              level === 'high' ? styles.progressHigh :
              level === 'medium' ? styles.progressMedium :
              level === 'low' ? styles.progressLow :
              styles.progressVeryLow
            }`}
            sx={{
              '& .MuiLinearProgress-bar': {
                backgroundColor: color,
                transition: 'transform 0.4s ease, background-color 0.3s ease',
              },
              backgroundColor: 'rgba(0, 0, 0, 0.1)',
            }}
          />
        </Box>
      </Box>
    </Tooltip>
  );
};

export default ConfidenceMeter;
