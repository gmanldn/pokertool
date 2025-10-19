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
  Badge,
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
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme as useCustomTheme } from '../contexts/ThemeContext';
import type { BackendStatus } from '../hooks/useBackendLifecycle';
import { useSystemHealth } from '../hooks/useSystemHealth';

interface NavigationProps {
  connected: boolean;
  backendStatus: BackendStatus;
}

export const Navigation: React.FC<NavigationProps> = ({ connected, backendStatus }) => {
  const theme = useTheme();
  const { darkMode, toggleDarkMode } = useCustomTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [debouncedConnected, setDebouncedConnected] = useState(connected);
  const appVersion = (process.env.REACT_APP_VERSION || '').trim();

  // Debounce realtime indicator to reduce flicker on transient disconnects
  useEffect(() => {
    const t = setTimeout(() => setDebouncedConnected(connected), 400);
    return () => clearTimeout(t);
  }, [connected]);

  // System health (used for FullyLoaded indicator)
  const { healthData } = useSystemHealth({ enableWebSocket: true, autoFetch: true, enableCache: true });
  const fullyLoaded = useMemo(() => {
    const backendOnline = backendStatus.state === 'online';
    const healthOk = (healthData?.overall_status || 'unknown') === 'healthy';
    return backendOnline && debouncedConnected && healthOk;
  }, [backendStatus.state, debouncedConnected, healthData]);

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
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

  const backendStatusMeta = useMemo(() => {
    switch (backendStatus.state) {
      case 'online':
        return {
          label: 'Backend: Online',
          color: 'success' as const,
          tooltip: backendStatus.message || 'Backend API reachable.',
        };
      case 'starting':
        return {
          label: 'Backend: Starting…',
          color: 'warning' as const,
          tooltip: backendStatus.message || 'Attempting to start backend API.',
        };
      case 'checking':
        return {
          label: 'Backend: Checking…',
          color: 'info' as const,
          tooltip: backendStatus.message || 'Verifying backend health.',
        };
      default:
        return {
          label: 'Backend: Offline',
          color: 'error' as const,
          tooltip: backendStatus.error || backendStatus.message || 'Backend health check failed. See logs for details.',
        };
    }
  }, [backendStatus]);

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
          PokerTool Pro
        </Typography>
      </Box>
      <Divider />
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ bgcolor: theme.palette.primary.main }}>P</Avatar>
        <Box>
          <Typography variant="subtitle1">Player</Typography>
          <Chip
            icon={<Circle sx={{ fontSize: 8 }} />}
            label={connected ? 'Connected' : 'Offline'}
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
        <Typography variant="body2">Dark Mode</Typography>
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
          
          <Typography variant="h6" sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            {isMobile ? 'PokerTool' : 'PokerTool Pro'}
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

          <Tooltip title={backendStatusMeta.tooltip}>
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
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Critical Service
              </Typography>
              <Chip
                icon={<Circle sx={{ fontSize: 8 }} />}
                label={backendStatusMeta.label}
                size="small"
                color={backendStatusMeta.color}
                variant="outlined"
              />
            </Box>
          </Tooltip>

          <Badge
            color={debouncedConnected ? 'success' : 'error'}
            variant="dot"
            sx={{ mr: 2 }}
          >
            <Chip
              label={debouncedConnected ? 'Realtime Online' : 'Realtime Offline'}
              size="small"
              color={debouncedConnected ? 'success' : 'default'}
              variant={debouncedConnected ? 'filled' : 'outlined'}
            />
          </Badge>

          {/* FullyLoaded indicator */}
          <Tooltip title={fullyLoaded ? 'All core systems healthy' : 'Waiting for all systems to be healthy'}>
            <Chip
              icon={<Circle sx={{ fontSize: 8 }} />}
              label={fullyLoaded ? 'FullyLoaded' : 'Loading…'}
              size="small"
              color={fullyLoaded ? 'success' : 'default'}
              variant={fullyLoaded ? 'filled' : 'outlined'}
              sx={{ mr: 1 }}
            />
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
