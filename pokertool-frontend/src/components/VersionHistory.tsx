/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/VersionHistory.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Created comprehensive tabbed version history interface
---
POKERTOOL-HEADER-END */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Chip,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemText,
  useTheme,
  Alert,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  InfoOutlined,
  NewReleases,
  Timeline,
  Star,
} from '@mui/icons-material';
import { RELEASE_VERSION } from '../config/releaseVersion';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`version-tabpanel-${index}`}
      aria-labelledby={`version-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `version-tab-${index}`,
    'aria-controls': `version-tabpanel-${index}`,
  };
}

export const VersionHistory: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const theme = useTheme();

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Parse version number
  const versionNumber = RELEASE_VERSION.replace('v', '');
  const [major, minor, patch] = versionNumber.split('.').map(Number);

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box>
          <Stack direction="row" spacing={2} alignItems="center" mb={2}>
            <InfoOutlined color="primary" sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h4" fontWeight="bold">
                Version History
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Track releases, features, and improvements
              </Typography>
            </Box>
          </Stack>
          <Chip
            label={RELEASE_VERSION}
            color="primary"
            size="medium"
            sx={{
              fontFamily: 'monospace',
              fontSize: '1rem',
              fontWeight: 700,
              px: 2,
              py: 2.5,
            }}
          />
        </Box>

        {/* Tabs */}
        <Paper sx={{ width: '100%' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="version history tabs"
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
            }}
          >
            <Tab icon={<InfoOutlined />} iconPosition="start" label="Current Version" {...a11yProps(0)} />
            <Tab icon={<Timeline />} iconPosition="start" label="Changelog" {...a11yProps(1)} />
            <Tab icon={<NewReleases />} iconPosition="start" label="Release Notes" {...a11yProps(2)} />
            <Tab icon={<Star />} iconPosition="start" label="What's New" {...a11yProps(3)} />
          </Tabs>

          {/* Tab 0: Current Version */}
          <TabPanel value={tabValue} index={0}>
            <Stack spacing={3}>
              <Alert severity="info" icon={<InfoOutlined />}>
                You are running the latest version of PokerTool
              </Alert>

              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="overline" color="text.secondary">
                        Version Number
                      </Typography>
                      <Typography variant="h4" fontWeight="bold" color="primary" sx={{ fontFamily: 'monospace' }}>
                        {RELEASE_VERSION}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="overline" color="text.secondary">
                        Release Type
                      </Typography>
                      <Typography variant="h5" fontWeight="bold">
                        {major >= 100 ? 'Production' : 'Beta'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" mt={1}>
                        {major >= 100 ? 'Stable release for production use' : 'Beta release for testing'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="overline" color="text.secondary">
                        Build Number
                      </Typography>
                      <Typography variant="h5" fontWeight="bold" sx={{ fontFamily: 'monospace' }}>
                        {major}.{minor}.{patch}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" mt={1}>
                        Major: {major} • Minor: {minor} • Patch: {patch}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Divider />

              <Box>
                <Typography variant="h6" gutterBottom>
                  Version Components
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Major Version"
                      secondary={`${major} - Significant changes, new architecture, breaking changes`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Minor Version"
                      secondary={`${minor} - New features, enhancements, backward-compatible`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Patch Version"
                      secondary={`${patch} - Bug fixes, small improvements, maintenance`}
                    />
                  </ListItem>
                </List>
              </Box>
            </Stack>
          </TabPanel>

          {/* Tab 1: Changelog */}
          <TabPanel value={tabValue} index={1}>
            <Stack spacing={3}>
              <Typography variant="h5" gutterBottom>
                Recent Changes
              </Typography>

              {/* v100.3.1 */}
              <Card variant="outlined">
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" mb={2}>
                    <Chip label="v100.3.1" color="primary" size="small" sx={{ fontFamily: 'monospace' }} />
                    <Typography variant="caption" color="text.secondary">
                      Current Release
                    </Typography>
                  </Stack>
                  <Typography variant="h6" gutterBottom>
                    Thread Management & Version Display
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="✨ Comprehensive thread management and cleanup system" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="✨ Enhanced version history blade in navigation drawer" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="✨ Tabbed version history interface" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="🔧 Graceful shutdown with signal handlers" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="🧪 31 comprehensive thread management tests" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>

              {/* v100.3.0 */}
              <Card variant="outlined">
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" mb={2}>
                    <Chip label="v100.3.0" size="small" sx={{ fontFamily: 'monospace' }} />
                  </Stack>
                  <Typography variant="h6" gutterBottom>
                    Code Quality & Security Hardening
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="🔒 Enhanced security measures" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="📊 Code quality improvements" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="🧪 Expanded test coverage" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>

              {/* v100.2.0 */}
              <Card variant="outlined">
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" mb={2}>
                    <Chip label="v100.2.0" size="small" sx={{ fontFamily: 'monospace' }} />
                  </Stack>
                  <Typography variant="h6" gutterBottom>
                    Database Query Optimization
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="⚡ Query performance optimization" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="📈 Database profiling tools" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="🔍 Query analysis and monitoring" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>

              {/* v100.1.0 */}
              <Card variant="outlined">
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" mb={2}>
                    <Chip label="v100.1.0" size="small" sx={{ fontFamily: 'monospace' }} />
                  </Stack>
                  <Typography variant="h6" gutterBottom>
                    Centralized Error Handling
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="🛡️ Centralized error handling middleware" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="📝 Enhanced error logging" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="🔔 Error notification system" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>

              {/* v100.0.0 */}
              <Card variant="outlined">
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" mb={2}>
                    <Chip label="v100.0.0" color="success" size="small" sx={{ fontFamily: 'monospace' }} />
                    <Typography variant="caption" color="success.main" fontWeight="bold">
                      Major Release
                    </Typography>
                  </Stack>
                  <Typography variant="h6" gutterBottom>
                    Quality, Reliability, and Bootstrap Excellence
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="🎉 First production-ready major release" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="🚀 Enhanced bootstrap scripts for macOS and Linux" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="✅ Comprehensive test suite" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="📚 Complete documentation" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="🔧 Reliable installation and startup" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Stack>
          </TabPanel>

          {/* Tab 2: Release Notes */}
          <TabPanel value={tabValue} index={2}>
            <Stack spacing={3}>
              <Typography variant="h5" gutterBottom>
                Release Notes - {RELEASE_VERSION}
              </Typography>

              <Alert severity="success">
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  Production Ready
                </Typography>
                <Typography variant="body2">
                  This version has been thoroughly tested and is ready for production use.
                </Typography>
              </Alert>

              <Box>
                <Typography variant="h6" gutterBottom>
                  🎯 Key Features
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Thread Management System"
                      secondary="Comprehensive thread lifecycle management with graceful shutdown, signal handlers, and automatic cleanup on startup and exit"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Version Display Enhancement"
                      secondary="Added tabbed version history interface with current version info, changelog, release notes, and what's new section"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Testing Infrastructure"
                      secondary="31 comprehensive unit tests for thread management ensuring robustness and preventing regressions"
                    />
                  </ListItem>
                </List>
              </Box>

              <Divider />

              <Box>
                <Typography variant="h6" gutterBottom>
                  🔧 Technical Improvements
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="ThreadManager with lifecycle management"
                      secondary="Enhanced ThreadManager class with proper start/stop/cleanup methods and stop event tracking"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="ThreadCleanupManager utility"
                      secondary="New 350-line utility module for centralized thread monitoring and cleanup"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Signal handlers"
                      secondary="SIGTERM and SIGINT handlers for graceful shutdown when application is terminated"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="atexit cleanup"
                      secondary="Automatic cleanup handlers registered to ensure clean exit"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Startup thread cleanup"
                      secondary="Automatic detection and cleanup of orphaned threads from previous runs"
                    />
                  </ListItem>
                </List>
              </Box>

              <Divider />

              <Box>
                <Typography variant="h6" gutterBottom>
                  📝 Known Issues
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  No known issues in this release.
                </Typography>
              </Box>

              <Divider />

              <Box>
                <Typography variant="h6" gutterBottom>
                  ⚠️ Breaking Changes
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  No breaking changes in this release.
                </Typography>
              </Box>
            </Stack>
          </TabPanel>

          {/* Tab 3: What's New */}
          <TabPanel value={tabValue} index={3}>
            <Stack spacing={3}>
              <Typography variant="h5" gutterBottom>
                What's New in {RELEASE_VERSION}
              </Typography>

              <Card variant="outlined" sx={{ bgcolor: theme.palette.mode === 'dark' ? 'primary.dark' : 'primary.light' }}>
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                    <NewReleases color="primary" />
                    <Typography variant="h6" fontWeight="bold">
                      Highlights
                    </Typography>
                  </Stack>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="🎉 Comprehensive Thread Management"
                        secondary="No more orphaned threads! The application now starts and exits cleanly with automatic cleanup of old threads."
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="📊 Version History Dashboard"
                        secondary="New tabbed interface to explore version information, changelog, release notes, and new features."
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="✅ 31 New Tests"
                        secondary="Comprehensive test suite ensuring thread management reliability and preventing regressions."
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>

              <Box>
                <Typography variant="h6" gutterBottom>
                  💡 Why These Changes Matter
                </Typography>
                <Stack spacing={2}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        Clean Startup and Shutdown
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Previously, threads from crashed or improperly closed sessions could linger in the system.
                        Now, every startup checks for and cleans up orphaned threads, ensuring a fresh start every time.
                      </Typography>
                    </CardContent>
                  </Card>

                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        Graceful Shutdown
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Signal handlers (SIGTERM/SIGINT) and atexit handlers ensure that when you close the application,
                        all threads are properly stopped and resources are cleaned up. No more zombie processes!
                      </Typography>
                    </CardContent>
                  </Card>

                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        Better Visibility
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        The new version history interface gives you complete visibility into what version you're running,
                        what's changed, and what's new. No more guessing which features are available!
                      </Typography>
                    </CardContent>
                  </Card>
                </Stack>
              </Box>

              <Divider />

              <Box>
                <Typography variant="h6" gutterBottom>
                  🚀 Getting Started
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  The thread management improvements work automatically in the background. You don't need to do anything
                  to benefit from them.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  To explore version history at any time, simply navigate to this page from the navigation menu.
                </Typography>
              </Box>
            </Stack>
          </TabPanel>
        </Paper>
      </Stack>
    </Box>
  );
};
