/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/Navigation.tsx
version: v28.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
---
POKERTOOL-HEADER-END */

import React, { useMemo, useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Box,
  Avatar,
  Divider,
  Switch,
  useTheme,
  useMediaQuery,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  TableChart,
  Assessment,
  Checklist as ChecklistIcon,
  AccountBalance,
  EmojiEvents,
  Settings,
  Brightness4,
  Brightness7,
  Visibility,
  School,
  History,
  Circle,
  Article,
  SettingsApplications,
  TrendingUp,
  People,
  Psychology,
  Biotech,
  DeveloperBoard,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useTheme as useCustomTheme } from '../contexts/ThemeContext';
import type { BackendStatus } from '../hooks/useBackendLifecycle';
import { useSystemHealth } from '../hooks/useSystemHealth';
import { buildApiUrl } from '../config/api';

interface NavigationProps {
  connected: boolean;
  backendStatus: BackendStatus;
}

interface StartupStatus {
  total_steps: number;
  steps_completed: number;
  steps_pending?: number;
  is_complete: boolean;
  current_step_info?: {
    name: string;
    description: string;
    number: number;
  };
}

export const Navigation: React.FC<NavigationProps> = ({ connected, backendStatus }) => {
  const { t } = useTranslation();
  const theme = useTheme();
  const { darkMode, toggleDarkMode } = useCustomTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [debouncedConnected, setDebouncedConnected] = useState(connected);
  const appVersion = (process.env.REACT_APP_VERSION || '').trim();
  const [startupStatus, setStartupStatus] = useState<StartupStatus | null>(null);

  // Debounce WebSocket connection status to reduce flicker on transient disconnects
  useEffect(() => {
    const t = setTimeout(() => setDebouncedConnected(connected), 400);
    return () => clearTimeout(t);
  }, [connected]);

  // System health (used for unified status indicator)
  const { healthData } = useSystemHealth({ enableWebSocket: true, autoFetch: true, enableCache: true });

  // Debounce health data to prevent flickering
  const [debouncedHealthStatus, setDebouncedHealthStatus] = useState<string>('unknown');
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedHealthStatus(healthData?.overall_status || 'unknown');
    }, 600);
    return () => clearTimeout(t);
  }, [healthData?.overall_status]);

  // WebSocket + Fallback polling for startup status
  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollInterval: NodeJS.Timeout | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    const fetchStartupStatus = async () => {
      try {
        const response = await fetch(buildApiUrl('/api/backend/startup/status'));
        if (response.ok) {
          const data = await response.json();
          setStartupStatus(data);
        }
      } catch (err) {
        // Silently fail - backend might not be ready yet
      }
    };

    const connectWebSocket = () => {
      try {
        // Connect to backend startup WebSocket
        const wsUrl = buildApiUrl('/ws/backend-startup').replace('http', 'ws');
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('Backend startup WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === 'startup_update' && message.data) {
              setStartupStatus(message.data);
            }
          } catch (err) {
            console.error('Error parsing startup WebSocket message:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('Backend startup WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('Backend startup WebSocket disconnected');
          // Reconnect after 2 seconds if backend is not online
          if (backendStatus.state !== 'online') {
            reconnectTimeout = setTimeout(connectWebSocket, 2000);
          }
        };
      } catch (err) {
        console.error('Error connecting to startup WebSocket:', err);
      }
    };

    // Fetch initial status
    fetchStartupStatus();

    // Try WebSocket connection
    connectWebSocket();

    // Fallback HTTP polling every 500ms (reduced from 2s for faster updates)
    pollInterval = setInterval(() => {
      if (backendStatus.state !== 'online' && (!ws || ws.readyState !== WebSocket.OPEN)) {
        fetchStartupStatus();
      }
    }, 500);

    return () => {
      if (ws) {
        ws.close();
      }
      if (pollInterval) {
        clearInterval(pollInterval);
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [backendStatus.state]);

  // Calculate startup percentage
  const startupPercentage = useMemo(() => {
    if (!startupStatus || startupStatus.is_complete) return null;
    if (startupStatus.total_steps === 0) return 0;
    return Math.round((startupStatus.steps_completed / startupStatus.total_steps) * 100);
  }, [startupStatus]);

  // Unified backend status - consolidated from separate backend/realtime indicators
  const systemStatus = useMemo(() => {
    const backendOnline = backendStatus.state === 'online';
    const wsConnected = debouncedConnected;
    const healthOk = debouncedHealthStatus === 'healthy';

    // Backend is only considered "online" if API + WebSocket + health are all good
    const backendFullyOnline = backendOnline && wsConnected && healthOk;

    if (backendFullyOnline) {
      return { state: 'ready', label: 'Backend Online', color: 'success' as const, percentage: null };
    } else if (!backendOnline || !wsConnected) {
      // Treat WebSocket disconnection same as backend offline
      // Show current step name if available
      let label = 'Backend Offline';
      if (startupStatus?.current_step_info) {
        const stepName = startupStatus.current_step_info.name || 'Unknown Step';
        label = `Waiting for ${stepName}`;
        if (startupPercentage !== null) {
          label += ` (${startupPercentage}%)`;
        }
      } else if (startupPercentage !== null) {
        label = `Backend Offline (${startupPercentage}%)`;
      }
      return { state: 'backend_down', label, color: 'error' as const, percentage: startupPercentage };
    } else if (!healthOk) {
      return { state: 'degraded', label: 'Backend Degraded', color: 'warning' as const, percentage: null };
    } else {
      // Backend starting
      let label = 'Backend Starting';
      if (startupStatus?.current_step_info) {
        const stepName = startupStatus.current_step_info.name || 'Unknown Step';
        label = `Starting: ${stepName}`;
        if (startupPercentage !== null) {
          label += ` (${startupPercentage}%)`;
        }
      } else if (startupPercentage !== null) {
        label = `Backend Starting (${startupPercentage}%)`;
      }
      return { state: 'starting', label, color: 'info' as const, percentage: startupPercentage };
    }
  }, [backendStatus.state, debouncedConnected, debouncedHealthStatus, startupPercentage, startupStatus]);

  // Unified system status tooltip
  const systemStatusTooltip = useMemo(() => {
    const details: string[] = [];

    // Backend status
    details.push(`Backend: ${backendStatus.state}`);

    // Add startup progress if backend is offline
    if (backendStatus.state !== 'online' && startupStatus) {
      details.push(`Startup: ${startupStatus.steps_completed}/${startupStatus.total_steps} steps (${startupPercentage || 0}%)`);
      if (startupStatus.steps_pending) {
        details.push(`Pending: ${startupStatus.steps_pending} tasks`);
      }

      // Add current step details
      if (startupStatus.current_step_info) {
        details.push('---');
        details.push(`Current Step: ${startupStatus.current_step_info.name}`);
        details.push(`Description: ${startupStatus.current_step_info.description}`);
      }
    }

    // WebSocket status
    details.push(`WebSocket: ${debouncedConnected ? 'connected' : 'disconnected'}`);

    // Health status
    details.push(`Health: ${debouncedHealthStatus}`);

    // Add affected categories if health is not OK
    if (healthData && debouncedHealthStatus !== 'healthy') {
      const affectedCategories = Object.entries(healthData.categories || {})
        .filter(([, value]) => value.status !== 'healthy')
        .map(([name, value]) => `${name.charAt(0).toUpperCase() + name.slice(1)}: ${value.status}`);

      if (affectedCategories.length > 0) {
        details.push('---');
        details.push(...affectedCategories);
      }
    }

    return details.join(' • ');
  }, [backendStatus.state, debouncedConnected, debouncedHealthStatus, healthData, startupStatus, startupPercentage]);

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Backend', icon: <DeveloperBoard />, path: '/backend' },
    { text: 'TODO', icon: <ChecklistIcon />, path: '/todo' },
    { text: 'Tables', icon: <TableChart />, path: '/tables' },
    { text: 'Detection Log', icon: <Article />, path: '/detection-log' },
    { text: 'Statistics', icon: <Assessment />, path: '/statistics' },
    { text: 'Bankroll', icon: <AccountBalance />, path: '/bankroll' },
    { text: 'Tournament', icon: <EmojiEvents />, path: '/tournament' },
    { text: 'HUD Overlay', icon: <Visibility />, path: '/hud' },
    { text: 'GTO Trainer', icon: <School />, path: '/gto' },
    { text: 'Hand History', icon: <History />, path: '/history' },
    { text: 'Settings', icon: <Settings />, path: '/settings' },
    { text: 'Model Calibration', icon: <TrendingUp />, path: '/model-calibration' },
    { text: 'Opponent Fusion', icon: <People />, path: '/opponent-fusion' },
    { text: 'Active Learning', icon: <Psychology />, path: '/active-learning' },
    { text: 'Scraping Accuracy', icon: <Biotech />, path: '/scraping-accuracy' },
    { text: 'System Status', icon: <SettingsApplications />, path: '/system-status' },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const drawer = (
    <Box
      sx={{
        width: 250,
        height: '100%',
        backgroundColor: theme.palette.background.paper,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2,
        }}
      >
        <Typography variant="h6" fontWeight="bold" color="primary">
          {t('app.title')}
        </Typography>
      </Box>
      <Divider />
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ bgcolor: theme.palette.primary.main }}>P</Avatar>
        <Box>
          <Typography variant="subtitle1">Player</Typography>
          <Chip
            icon={<Circle sx={{ fontSize: 8 }} />}
            label={connected ? t('status.connected') : t('status.offline')}
            size="small"
            color={connected ? 'success' : 'default'}
            variant="outlined"
          />
        </Box>
      </Box>
      <Divider />
      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                borderRadius: 1,
                mb: 0.5,
                '&.Mui-selected': {
                  backgroundColor: `${theme.palette.primary.main}22`,
                  '&:hover': {
                    backgroundColor: `${theme.palette.primary.main}33`,
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color:
                    location.pathname === item.path
                      ? theme.palette.primary.main
                      : 'inherit',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box sx={{ flexGrow: 1 }} />
      <Divider />
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <IconButton onClick={toggleDarkMode} color="inherit">
          {darkMode ? <Brightness7 /> : <Brightness4 />}
        </IconButton>
        <Typography variant="body2">{t('navigation.darkMode')}</Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Switch checked={darkMode} onChange={toggleDarkMode} />
      </Box>
    </Box>
  );

  return (
    <>
      <AppBar
        position="sticky"
        sx={{
          backgroundColor: theme.palette.background.paper,
          color: theme.palette.text.primary,
          boxShadow: theme.palette.mode === 'dark' ? 1 : 2,
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Typography
            variant="h6"
            sx={{
              flexGrow: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              cursor: 'pointer',
              '&:hover': {
                opacity: 0.8,
              },
            }}
            onClick={() => handleNavigation('/dashboard')}
          >
            {isMobile ? t('app.titleShort') : t('app.title')}
            {!!appVersion && (
              <Chip
                size="small"
                variant="outlined"
                label={appVersion.startsWith('v') ? appVersion : `v${appVersion}`}
                sx={{ ml: 1 }}
              />
            )}
          </Typography>

          {!isMobile && (
            <>
              <Box sx={{ display: 'flex', gap: 2, mr: 2 }}>
                {menuItems.slice(0, 5).map((item) => (
                  <Tooltip key={item.text} title={item.text}>
                    <IconButton
                      color={location.pathname === item.path ? 'primary' : 'inherit'}
                      onClick={() => handleNavigation(item.path)}
                    >
                      {item.icon}
                    </IconButton>
                  </Tooltip>
                ))}
                {/* Add System Status as 6th item */}
                <Tooltip title="System Status">
                  <IconButton
                    color={location.pathname === '/system-status' ? 'primary' : 'inherit'}
                    onClick={() => handleNavigation('/system-status')}
                  >
                    <SettingsApplications />
                  </IconButton>
                </Tooltip>
              </Box>
              <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
            </>
          )}

          {/* Unified System Status Indicator */}
          <Tooltip title={systemStatusTooltip} arrow>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                px: 1.5,
                py: 0.75,
                borderRadius: 2,
                backgroundColor:
                  theme.palette.mode === 'dark'
                    ? theme.palette.background.default
                    : theme.palette.grey[100],
                mr: 2,
                border: `1px solid ${theme.palette.divider}`,
                transition: 'all 0.3s ease',
              }}
            >
              <Chip
                icon={<Circle sx={{ fontSize: 8 }} />}
                label={systemStatus.label}
                size="small"
                color={systemStatus.color}
                variant="filled"
                sx={{
                  transition: 'all 0.3s ease',
                  fontWeight: 'bold',
                }}
              />
            </Box>
          </Tooltip>

          {!isMobile && (
            <IconButton onClick={toggleDarkMode} color="inherit">
              {darkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          )}
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        ModalProps={{
          keepMounted: true, // Better performance on mobile
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
};
