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

import React, { useState } from 'react';
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
  Button,
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
  PlayArrow,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme as useCustomTheme } from '../contexts/ThemeContext';

interface NavigationProps {
  connected: boolean;
}

export const Navigation: React.FC<NavigationProps> = ({ connected }) => {
  const theme = useTheme();
  const { darkMode, toggleDarkMode } = useCustomTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [startingBackend, setStartingBackend] = useState(false);

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
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const handleStartBackend = async () => {
    setStartingBackend(true);
    try {
      // Call the backend start API endpoint
      const response = await fetch('http://localhost:5001/api/start-backend', {
        method: 'POST',
      });

      if (response.ok) {
        console.log('Backend start request sent successfully');
      } else {
        console.error('Failed to start backend');
      }
    } catch (error) {
      console.error('Error starting backend:', error);
    } finally {
      // Reset button state after 3 seconds
      setTimeout(() => setStartingBackend(false), 3000);
    }
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
          
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {isMobile ? 'PokerTool' : 'PokerTool Pro'}
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
              </Box>
              <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
            </>
          )}

          {!connected && (
            <Tooltip title="Start the backend server">
              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<PlayArrow />}
                onClick={handleStartBackend}
                disabled={startingBackend}
                sx={{ mr: 2 }}
              >
                {startingBackend ? 'Starting...' : 'Start Backend'}
              </Button>
            </Tooltip>
          )}

          <Badge
            color={connected ? 'success' : 'error'}
            variant="dot"
            sx={{ mr: 2 }}
          >
            <Chip
              label={connected ? 'Online' : 'Offline'}
              size="small"
              color={connected ? 'success' : 'default'}
              variant={connected ? 'filled' : 'outlined'}
            />
          </Badge>

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