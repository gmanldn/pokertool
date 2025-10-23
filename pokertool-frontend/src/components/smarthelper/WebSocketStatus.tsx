/**
 * WebSocket Connection Status Indicator
 *
 * Visual indicator for SmartHelper WebSocket connection state with:
 * - Real-time connection status
 * - Latency monitoring
 * - Auto-reconnect countdown
 * - Connection quality visualization
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Chip,
  Tooltip,
  Typography,
  CircularProgress,
  Popover,
  Paper,
  LinearProgress
} from '@mui/material';
import {
  Wifi,
  WifiOff,
  SignalWifiStatusbar4Bar,
  SignalWifiStatusbarConnectedNoInternet4,
  SignalWifiStatusbarNull,
  ErrorOutline,
  CheckCircle,
  Sync
} from '@mui/icons-material';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'reconnecting' | 'error';

export interface ConnectionQuality {
  latency: number; // milliseconds
  jitter: number; // milliseconds variance
  packetLoss: number; // percentage
  quality: 'excellent' | 'good' | 'fair' | 'poor';
}

interface WebSocketStatusProps {
  status: ConnectionStatus;
  quality?: ConnectionQuality;
  reconnectAttempt?: number;
  maxReconnectAttempts?: number;
  reconnectDelay?: number; // seconds
  lastMessageTime?: Date;
  onReconnect?: () => void;
  compact?: boolean;
}

export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({
  status,
  quality,
  reconnectAttempt = 0,
  maxReconnectAttempts = 5,
  reconnectDelay = 0,
  lastMessageTime,
  onReconnect,
  compact = false
}) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [countdown, setCountdown] = useState(reconnectDelay);

  // Countdown timer for reconnection
  useEffect(() => {
    if (status === 'reconnecting' && reconnectDelay > 0) {
      setCountdown(reconnectDelay);

      const interval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [status, reconnectDelay]);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          label: 'Connected',
          color: '#4caf50',
          icon: <Wifi sx={{ fontSize: 16 }} />,
          bgColor: 'rgba(76, 175, 80, 0.1)'
        };
      case 'connecting':
        return {
          label: 'Connecting',
          color: '#2196f3',
          icon: <CircularProgress size={14} sx={{ color: '#2196f3' }} />,
          bgColor: 'rgba(33, 150, 243, 0.1)'
        };
      case 'disconnected':
        return {
          label: 'Disconnected',
          color: '#9e9e9e',
          icon: <WifiOff sx={{ fontSize: 16 }} />,
          bgColor: 'rgba(158, 158, 158, 0.1)'
        };
      case 'reconnecting':
        return {
          label: `Reconnecting (${reconnectAttempt}/${maxReconnectAttempts})`,
          color: '#ff9800',
          icon: <Sync sx={{ fontSize: 16, animation: 'spin 1s linear infinite' }} />,
          bgColor: 'rgba(255, 152, 0, 0.1)'
        };
      case 'error':
        return {
          label: 'Connection Error',
          color: '#f44336',
          icon: <ErrorOutline sx={{ fontSize: 16 }} />,
          bgColor: 'rgba(244, 67, 54, 0.1)'
        };
      default:
        return {
          label: 'Unknown',
          color: '#9e9e9e',
          icon: <WifiOff sx={{ fontSize: 16 }} />,
          bgColor: 'rgba(158, 158, 158, 0.1)'
        };
    }
  };

  const getQualityIcon = () => {
    if (!quality) return null;

    switch (quality.quality) {
      case 'excellent':
        return <SignalWifiStatusbar4Bar sx={{ fontSize: 16, color: '#4caf50' }} />;
      case 'good':
        return <SignalWifiStatusbar4Bar sx={{ fontSize: 16, color: '#8bc34a' }} />;
      case 'fair':
        return <SignalWifiStatusbarConnectedNoInternet4 sx={{ fontSize: 16, color: '#ff9800' }} />;
      case 'poor':
        return <SignalWifiStatusbarNull sx={{ fontSize: 16, color: '#f44336' }} />;
      default:
        return null;
    }
  };

  const formatLatency = (latency: number): string => {
    if (latency < 50) return `${latency}ms (Excellent)`;
    if (latency < 150) return `${latency}ms (Good)`;
    if (latency < 300) return `${latency}ms (Fair)`;
    return `${latency}ms (Poor)`;
  };

  const getTimeSinceLastMessage = (): string => {
    if (!lastMessageTime) return 'Never';

    const now = new Date();
    const diff = now.getTime() - lastMessageTime.getTime();
    const seconds = Math.floor(diff / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };

  const config = getStatusConfig();
  const open = Boolean(anchorEl);

  if (compact) {
    return (
      <Tooltip title={config.label}>
        <Box
          onClick={handleClick}
          sx={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            backgroundColor: config.color,
            cursor: 'pointer',
            boxShadow: `0 0 8px ${config.color}`,
            animation: status === 'connecting' || status === 'reconnecting'
              ? 'pulse 1.5s ease-in-out infinite'
              : 'none',
            '@keyframes pulse': {
              '0%, 100%': { opacity: 1, transform: 'scale(1)' },
              '50%': { opacity: 0.6, transform: 'scale(1.1)' }
            }
          }}
        />
      </Tooltip>
    );
  }

  return (
    <>
      <Chip
        icon={config.icon}
        label={config.label}
        size="small"
        onClick={handleClick}
        sx={{
          height: 24,
          fontSize: '11px',
          fontWeight: 'bold',
          backgroundColor: config.bgColor,
          color: config.color,
          border: `1px solid ${config.color}`,
          cursor: 'pointer',
          '& .MuiChip-icon': {
            color: config.color
          },
          '@keyframes spin': {
            '0%': { transform: 'rotate(0deg)' },
            '100%': { transform: 'rotate(360deg)' }
          }
        }}
      />

      {/* Details Popover */}
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right'
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right'
        }}
      >
        <Paper
          sx={{
            p: 2,
            minWidth: 250,
            backgroundColor: 'rgba(33, 33, 33, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <Typography variant="subtitle2" fontWeight="bold" color="white" sx={{ mb: 1 }}>
            WebSocket Connection
          </Typography>

          {/* Status */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
            {config.icon}
            <Typography variant="body2" color={config.color}>
              {config.label}
            </Typography>
          </Box>

          {/* Connection Quality */}
          {quality && status === 'connected' && (
            <Box sx={{ mb: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="textSecondary">
                  Connection Quality
                </Typography>
                {getQualityIcon()}
              </Box>

              <Box sx={{ mb: 0.5 }}>
                <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
                  Latency: {formatLatency(quality.latency)}
                </Typography>
              </Box>

              {quality.jitter > 0 && (
                <Box sx={{ mb: 0.5 }}>
                  <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
                    Jitter: {quality.jitter.toFixed(0)}ms
                  </Typography>
                </Box>
              )}

              {quality.packetLoss > 0 && (
                <Box sx={{ mb: 0.5 }}>
                  <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
                    Packet Loss: {quality.packetLoss.toFixed(1)}%
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Reconnect Progress */}
          {status === 'reconnecting' && (
            <Box sx={{ mb: 1.5 }}>
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
                Retry {reconnectAttempt} of {maxReconnectAttempts}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(countdown / reconnectDelay) * 100}
                sx={{
                  height: 4,
                  borderRadius: 2,
                  backgroundColor: 'rgba(255, 152, 0, 0.2)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#ff9800'
                  }
                }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px', mt: 0.5, display: 'block' }}>
                Next attempt in {countdown}s
              </Typography>
            </Box>
          )}

          {/* Last Message */}
          {lastMessageTime && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
                Last message: {getTimeSinceLastMessage()}
              </Typography>
            </Box>
          )}

          {/* Manual Reconnect Button */}
          {(status === 'disconnected' || status === 'error') && onReconnect && (
            <Box
              onClick={() => {
                onReconnect();
                handleClose();
              }}
              sx={{
                mt: 1,
                p: 1,
                textAlign: 'center',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                borderRadius: 1,
                cursor: 'pointer',
                border: '1px solid rgba(33, 150, 243, 0.3)',
                '&:hover': {
                  backgroundColor: 'rgba(33, 150, 243, 0.2)'
                }
              }}
            >
              <Typography variant="caption" fontWeight="bold" color="primary.main">
                Reconnect Now
              </Typography>
            </Box>
          )}
        </Paper>
      </Popover>
    </>
  );
};

/**
 * Simple connection indicator dot
 */
interface ConnectionDotProps {
  connected: boolean;
  size?: number;
}

export const ConnectionDot: React.FC<ConnectionDotProps> = ({ connected, size = 8 }) => (
  <Box
    sx={{
      width: size,
      height: size,
      borderRadius: '50%',
      backgroundColor: connected ? '#4caf50' : '#f44336',
      boxShadow: connected ? '0 0 6px #4caf50' : '0 0 6px #f44336',
      animation: connected ? 'none' : 'blink 1s ease-in-out infinite',
      '@keyframes blink': {
        '0%, 100%': { opacity: 1 },
        '50%': { opacity: 0.3 }
      }
    }}
  />
);
