/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ConnectionStatus.tsx
version: v76.0.0
last_commit: '2025-10-15T03:47:00Z'
fixes:
- date: '2025-10-15'
  summary: Created Connection Status indicator component
---
POKERTOOL-HEADER-END */

import React from 'react';
import {
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  Fade,
} from '@mui/material';
import {
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Sync as SyncIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { ConnectionStatus as ConnectionStatusEnum } from '../hooks/useWebSocket';

interface ConnectionStatusProps {
  status: ConnectionStatusEnum;
  reconnectCountdown: number;
  cachedMessageCount: number;
  onReconnect: () => void;
}

// Status configuration
const STATUS_CONFIG = {
  [ConnectionStatusEnum.CONNECTED]: {
    label: 'Connected',
    color: '#4caf50',
    icon: WifiIcon,
    showReconnect: false,
  },
  [ConnectionStatusEnum.CONNECTING]: {
    label: 'Connecting...',
    color: '#2196f3',
    icon: SyncIcon,
    showReconnect: false,
  },
  [ConnectionStatusEnum.DISCONNECTED]: {
    label: 'Disconnected',
    color: '#f44336',
    icon: WifiOffIcon,
    showReconnect: true,
  },
  [ConnectionStatusEnum.RECONNECTING]: {
    label: 'Reconnecting...',
    color: '#ff9800',
    icon: SyncIcon,
    showReconnect: true,
  },
};

export const ConnectionStatusIndicator: React.FC<ConnectionStatusProps> = ({
  status,
  reconnectCountdown,
  cachedMessageCount,
  onReconnect,
}) => {
  const config = STATUS_CONFIG[status];
  const IconComponent = config.icon;

  return (
    <Fade in={true}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          p: 1,
          borderRadius: 1,
          backgroundColor: 'rgba(0,0,0,0.2)',
        }}
      >
        {/* Status Icon */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation:
              status === ConnectionStatusEnum.CONNECTING ||
              status === ConnectionStatusEnum.RECONNECTING
                ? 'spin 2s linear infinite'
                : 'none',
            '@keyframes spin': {
              '0%': { transform: 'rotate(0deg)' },
              '100%': { transform: 'rotate(360deg)' },
            },
          }}
        >
          <IconComponent
            sx={{
              color: config.color,
              fontSize: '1.5rem',
            }}
          />
        </Box>

        {/* Status Label */}
        <Chip
          label={config.label}
          size="small"
          sx={{
            backgroundColor: config.color,
            color: 'white',
            fontWeight: 'bold',
            minWidth: 100,
          }}
        />

        {/* Reconnect Countdown */}
        {status === ConnectionStatusEnum.RECONNECTING && reconnectCountdown > 0 && (
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            ({reconnectCountdown}s)
          </Typography>
        )}

        {/* Cached Messages Count */}
        {cachedMessageCount > 0 && (
          <Tooltip title={`${cachedMessageCount} messages cached for replay`}>
            <Chip
              label={`${cachedMessageCount} cached`}
              size="small"
              sx={{
                backgroundColor: 'rgba(255, 152, 0, 0.2)',
                color: '#ff9800',
                fontWeight: 'bold',
              }}
            />
          </Tooltip>
        )}

        {/* Manual Reconnect Button */}
        {config.showReconnect && (
          <Tooltip title="Reconnect now">
            <IconButton
              size="small"
              onClick={onReconnect}
              sx={{
                color: config.color,
                '&:hover': {
                  backgroundColor: `${config.color}20`,
                },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>
    </Fade>
  );
};

export default ConnectionStatusIndicator;
