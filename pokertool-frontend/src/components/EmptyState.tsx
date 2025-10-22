/**
 * Empty State Component
 *
 * Displays helpful messages and guidance when no data is available.
 * Provides context-specific messages and optional actions to guide users.
 */
import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import {
  Inbox,
  SearchOff,
  FilterAltOff,
  ErrorOutline,
  CloudOff,
  HourglassEmpty,
  PlayArrow,
  TableChart,
  Timeline,
  Assessment,
  PlayCircleOutline
} from '@mui/icons-material';

export type EmptyStateVariant =
  | 'no-data'           // No data exists yet
  | 'no-results'        // Search/filter returned no results
  | 'error'             // Error state
  | 'offline'           // Offline/disconnected
  | 'loading'           // Loading/processing
  | 'no-hands'          // No poker hands played
  | 'no-sessions'       // No sessions recorded
  | 'no-stats'          // No statistics available
  | 'no-analysis';      // No analysis available

interface EmptyStateProps {
  variant?: EmptyStateVariant;
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
  showBackground?: boolean;
}

const getVariantConfig = (variant: EmptyStateVariant) => {
  switch (variant) {
    case 'no-hands':
      return {
        icon: <TableChart sx={{ fontSize: 64, color: 'primary.main', opacity: 0.5 }} />,
        title: 'No Hands Yet',
        message: 'Start playing poker to see your hands appear here. The system will automatically detect and record your gameplay.',
        actionLabel: 'View Dashboard'
      };

    case 'no-sessions':
      return {
        icon: <PlayCircleOutline sx={{ fontSize: 64, color: 'primary.main', opacity: 0.5 }} />,
        title: 'No Sessions Recorded',
        message: 'Your poker sessions will appear here once you start playing. Each session is automatically tracked from start to finish.',
        actionLabel: 'Start Playing'
      };

    case 'no-stats':
      return {
        icon: <Assessment sx={{ fontSize: 64, color: 'primary.main', opacity: 0.5 }} />,
        title: 'No Statistics Available',
        message: 'Play some hands to generate statistics. You\'ll see detailed metrics about your play style, win rates, and tendencies.',
        actionLabel: 'View Guide'
      };

    case 'no-analysis':
      return {
        icon: <Timeline sx={{ fontSize: 64, color: 'primary.main', opacity: 0.5 }} />,
        title: 'No Analysis Available',
        message: 'Complete some hands to unlock analysis features. The SmartHelper will provide detailed insights into your decisions.',
        actionLabel: 'Learn More'
      };

    case 'no-results':
      return {
        icon: <SearchOff sx={{ fontSize: 64, color: 'warning.main', opacity: 0.5 }} />,
        title: 'No Results Found',
        message: 'Try adjusting your search criteria or filters. You can broaden your search to find more matches.',
        actionLabel: 'Clear Filters'
      };

    case 'error':
      return {
        icon: <ErrorOutline sx={{ fontSize: 64, color: 'error.main', opacity: 0.5 }} />,
        title: 'Something Went Wrong',
        message: 'We encountered an error loading this data. Please try again or contact support if the problem persists.',
        actionLabel: 'Retry'
      };

    case 'offline':
      return {
        icon: <CloudOff sx={{ fontSize: 64, color: 'text.secondary', opacity: 0.5 }} />,
        title: 'You\'re Offline',
        message: 'Some features require an internet connection. Please check your connection and try again.',
        actionLabel: 'Retry Connection'
      };

    case 'loading':
      return {
        icon: <HourglassEmpty sx={{ fontSize: 64, color: 'info.main', opacity: 0.5 }} />,
        title: 'Loading Data',
        message: 'Please wait while we fetch your data. This should only take a moment.',
        actionLabel: null
      };

    case 'no-data':
    default:
      return {
        icon: <Inbox sx={{ fontSize: 64, color: 'text.secondary', opacity: 0.5 }} />,
        title: 'No Data',
        message: 'There\'s nothing here yet. Get started by performing an action.',
        actionLabel: 'Get Started'
      };
  }
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  variant = 'no-data',
  title,
  message,
  actionLabel,
  onAction,
  icon,
  showBackground = true
}) => {
  const config = getVariantConfig(variant);

  const displayTitle = title || config.title;
  const displayMessage = message || config.message;
  const displayActionLabel = actionLabel !== undefined ? actionLabel : config.actionLabel;
  const displayIcon = icon || config.icon;

  const content = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        minHeight: 300,
        p: 4
      }}
    >
      {/* Icon */}
      <Box sx={{ mb: 3 }}>
        {displayIcon}
      </Box>

      {/* Title */}
      <Typography
        variant="h6"
        color="text.primary"
        fontWeight="bold"
        sx={{ mb: 1.5 }}
      >
        {displayTitle}
      </Typography>

      {/* Message */}
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{
          maxWidth: 500,
          mb: 3,
          lineHeight: 1.6
        }}
      >
        {displayMessage}
      </Typography>

      {/* Action Button */}
      {displayActionLabel && onAction && (
        <Button
          variant="contained"
          color="primary"
          onClick={onAction}
          startIcon={<PlayArrow />}
          sx={{
            textTransform: 'none',
            px: 3,
            py: 1
          }}
        >
          {displayActionLabel}
        </Button>
      )}
    </Box>
  );

  if (!showBackground) {
    return content;
  }

  return (
    <Paper
      elevation={0}
      sx={{
        backgroundColor: 'rgba(255, 255, 255, 0.02)',
        border: '1px dashed rgba(255, 255, 255, 0.1)',
        borderRadius: 2
      }}
    >
      {content}
    </Paper>
  );
};

/**
 * Specific empty state variants for common use cases
 */

export const NoHandsEmptyState: React.FC<{ onAction?: () => void }> = ({ onAction }) => (
  <EmptyState variant="no-hands" onAction={onAction} />
);

export const NoSessionsEmptyState: React.FC<{ onAction?: () => void }> = ({ onAction }) => (
  <EmptyState variant="no-sessions" onAction={onAction} />
);

export const NoStatsEmptyState: React.FC<{ onAction?: () => void }> = ({ onAction }) => (
  <EmptyState variant="no-stats" onAction={onAction} />
);

export const NoAnalysisEmptyState: React.FC<{ onAction?: () => void }> = ({ onAction }) => (
  <EmptyState variant="no-analysis" onAction={onAction} />
);

export const NoResultsEmptyState: React.FC<{ onClearFilters?: () => void }> = ({ onClearFilters }) => (
  <EmptyState
    variant="no-results"
    actionLabel={onClearFilters ? 'Clear Filters' : undefined}
    onAction={onClearFilters}
  />
);

export const ErrorEmptyState: React.FC<{ onRetry?: () => void; message?: string }> = ({ onRetry, message }) => (
  <EmptyState
    variant="error"
    message={message}
    actionLabel={onRetry ? 'Retry' : undefined}
    onAction={onRetry}
  />
);

export const OfflineEmptyState: React.FC<{ onRetry?: () => void }> = ({ onRetry }) => (
  <EmptyState variant="offline" onAction={onRetry} />
);

export const LoadingEmptyState: React.FC = () => (
  <EmptyState variant="loading" showBackground={false} />
);
