/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ErrorBoundary.tsx
version: v76.0.0
last_commit: '2025-10-15T03:47:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Error Boundary with fallback UI and automatic recovery
---
POKERTOOL-HEADER-END */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Collapse,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallbackType?: 'advice' | 'table' | 'stats' | 'general';
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  maxRetries?: number;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
  showDetails: boolean;
  degradedMode: boolean;
}

// Fallback messages by component type
const FALLBACK_CONFIG = {
  advice: {
    title: 'Advice System Error',
    message: 'Unable to load advice panel. The system is working to recover.',
    icon: '🎯',
  },
  table: {
    title: 'Table Display Error',
    message: 'Unable to display table information. Attempting to reconnect.',
    icon: '🃏',
  },
  stats: {
    title: 'Statistics Error',
    message: 'Unable to load statistics. Some data may be temporarily unavailable.',
    icon: '📊',
  },
  general: {
    title: 'Component Error',
    message: 'Something went wrong. The system is attempting to recover.',
    icon: '⚠️',
  },
};

export class ErrorBoundary extends Component<Props, State> {
  private recoveryTimeout: NodeJS.Timeout | null = null;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      showDetails: false,
      degradedMode: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    console.error('ErrorBoundary caught error:', error);
    console.error('Error info:', errorInfo);

    this.setState({
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to backend
    this.logErrorToBackend(error, errorInfo);

    // Attempt automatic recovery
    this.attemptRecovery();
  }

  componentWillUnmount() {
    if (this.recoveryTimeout) {
      clearTimeout(this.recoveryTimeout);
    }
  }

  logErrorToBackend = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      await fetch('/api/log-error', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: {
            message: error.message,
            stack: error.stack,
            name: error.name,
          },
          errorInfo: {
            componentStack: errorInfo.componentStack,
          },
          timestamp: new Date().toISOString(),
          fallbackType: this.props.fallbackType || 'general',
          retryCount: this.state.retryCount,
        }),
      });
    } catch (loggingError) {
      console.error('Failed to log error to backend:', loggingError);
    }
  };

  attemptRecovery = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount < maxRetries) {
      // Wait progressively longer before each retry
      const delay = Math.min(1000 * Math.pow(2, retryCount), 8000);

      console.log(`Attempting automatic recovery in ${delay}ms (attempt ${retryCount + 1}/${maxRetries})`);

      this.recoveryTimeout = setTimeout(() => {
        this.setState(prevState => ({
          retryCount: prevState.retryCount + 1,
        }));
        this.handleReset();
      }, delay);
    } else {
      // Max retries reached - enter degraded mode
      console.warn('Max recovery attempts reached - entering degraded mode');
      this.setState({
        degradedMode: true,
      });
    }
  };

  handleReset = () => {
    if (this.recoveryTimeout) {
      clearTimeout(this.recoveryTimeout);
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    });
  };

  handleManualRetry = () => {
    this.setState({
      retryCount: 0,
      degradedMode: false,
    });
    this.handleReset();
  };

  toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails,
    }));
  };

  render() {
    const { hasError, error, errorInfo, retryCount, showDetails, degradedMode } = this.state;
    const { children, fallbackType = 'general', maxRetries = 3 } = this.props;

    if (!hasError) {
      return children;
    }

    const config = FALLBACK_CONFIG[fallbackType];

    return (
      <Card
        sx={{
          minHeight: 200,
          backgroundColor: 'rgba(244, 67, 54, 0.05)',
          border: '2px solid rgba(244, 67, 54, 0.3)',
        }}
      >
        <CardContent>
          {/* Error Icon and Title */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography variant="h3" sx={{ mr: 2 }}>
              {config.icon}
            </Typography>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" color="error" sx={{ fontWeight: 'bold' }}>
                {config.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {config.message}
              </Typography>
            </Box>
            <ErrorIcon color="error" sx={{ fontSize: '2rem' }} />
          </Box>

          {/* Degraded Mode Alert */}
          {degradedMode && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <AlertTitle>Degraded Mode</AlertTitle>
              This component is experiencing persistent errors. Some functionality may be limited.
              Please try refreshing the page or contact support if the issue persists.
            </Alert>
          )}

          {/* Retry Status */}
          {!degradedMode && retryCount > 0 && retryCount < maxRetries && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <AlertTitle>Automatic Recovery</AlertTitle>
              Recovery attempt {retryCount} of {maxRetries} in progress...
            </Alert>
          )}

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={this.handleManualRetry}
              fullWidth
            >
              Try Again
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<BugReportIcon />}
              onClick={() => window.location.reload()}
              fullWidth
            >
              Reload Page
            </Button>
          </Box>

          {/* Error Details */}
          <Box>
            <Button
              onClick={this.toggleDetails}
              endIcon={
                <ExpandMoreIcon
                  sx={{
                    transform: showDetails ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s',
                  }}
                />
              }
              size="small"
              sx={{ textTransform: 'none' }}
            >
              {showDetails ? 'Hide' : 'Show'} Technical Details
            </Button>

            <Collapse in={showDetails}>
              <Box
                sx={{
                  mt: 2,
                  p: 2,
                  backgroundColor: 'rgba(0, 0, 0, 0.3)',
                  borderRadius: 1,
                  maxHeight: 300,
                  overflowY: 'auto',
                }}
              >
                {error && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="error" sx={{ fontWeight: 'bold' }}>
                      Error:
                    </Typography>
                    <Typography
                      variant="body2"
                      component="pre"
                      sx={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                      }}
                    >
                      {error.toString()}
                    </Typography>
                  </Box>
                )}

                {error?.stack && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                      Stack Trace:
                    </Typography>
                    <Typography
                      variant="body2"
                      component="pre"
                      sx={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                      }}
                    >
                      {error.stack}
                    </Typography>
                  </Box>
                )}

                {errorInfo?.componentStack && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                      Component Stack:
                    </Typography>
                    <Typography
                      variant="body2"
                      component="pre"
                      sx={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                      }}
                    >
                      {errorInfo.componentStack}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Collapse>
          </Box>

          {/* Help Text */}
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
              💡 If this error persists, try clearing your browser cache or using a different browser.
              You can also report this issue to our support team with the technical details above.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }
}

export default ErrorBoundary;
