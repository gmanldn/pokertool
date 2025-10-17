/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/SystemStatus.tsx
version: v86.0.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created System Status Monitor component for real-time health monitoring
---
POKERTOOL-HEADER-END */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  TextField,
  Button,
  CircularProgress,
  Collapse,
  Divider,
  Tooltip,
  useTheme,
  useMediaQuery,
  Alert,
  InputAdornment,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Fade,
} from '@mui/material';
import Refresh from '@mui/icons-material/Refresh';
import GetApp from '@mui/icons-material/GetApp';
import Search from '@mui/icons-material/Search';
import ExpandMore from '@mui/icons-material/ExpandMore';
import ExpandLess from '@mui/icons-material/ExpandLess';
import CheckCircle from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import Warning from '@mui/icons-material/Warning';
import HelpOutline from '@mui/icons-material/HelpOutline';
import DescriptionIcon from '@mui/icons-material/Description';
import TableViewIcon from '@mui/icons-material/TableView';
import { useSystemHealth } from '../hooks/useSystemHealth';
import type { HealthStatus, HealthData } from '../hooks/useSystemHealth';

type FilterType = 'all' | 'healthy' | 'failing' | 'degraded' | 'unknown';

export const SystemStatus: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Use custom hook for health data management
  const {
    healthData,
    loading,
    error,
    refreshing,
    fetchHealthData,
    isConnected,
  } = useSystemHealth({
    enableWebSocket: true,
    enableCache: true,
    cacheTTL: 5 * 60 * 1000, // 5 minutes
    onStatusChange: (data) => {
      // Screen reader announcement for status changes
      announceToScreenReader(
        `System status updated. ${data.failing_count} features failing, ${data.degraded_count} degraded.`
      );
    },
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<FilterType>('all');
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);
  const announcerRef = useRef<HTMLDivElement>(null);

  // Screen reader announcer function
  const announceToScreenReader = (message: string) => {
    if (announcerRef.current) {
      announcerRef.current.textContent = message;
    }
  };

  const handleRefresh = async () => {
    announceToScreenReader('Refreshing system health data...');
    await fetchHealthData();
    announceToScreenReader('System health data refreshed.');
  };

  const downloadReport = (content: string, mimeType: string, filename: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const createCsvContent = (data: HealthData, exportedAt: string) => {
    const csvRows: string[][] = [
      ['exported_at', exportedAt],
      ['overall_status', data.overall_status],
      ['failing_count', data.failing_count.toString()],
      ['degraded_count', data.degraded_count.toString()],
      [''],
      ['category', 'feature_name', 'status', 'last_check', 'latency_ms', 'error_message', 'description'],
    ];

    Object.entries(data.categories).forEach(([categoryKey, categoryData]) => {
      categoryData.checks.forEach((check) => {
        csvRows.push([
          getCategoryDisplayName(categoryKey),
          check.feature_name,
          check.status,
          check.last_check,
          check.latency_ms !== undefined ? check.latency_ms.toFixed(2) : '',
          check.error_message ?? '',
          check.description ?? '',
        ]);
      });
    });

    const escapeCsvValue = (value: string) => {
      const stringValue = value ?? '';
      const sanitized = stringValue.replace(/"/g, '""');
      return `"${sanitized}"`;
    };

    return csvRows
      .map((row) => row.length ? row.map((value) => escapeCsvValue(value)).join(',') : '')
      .join('\n');
  };

  const handleExport = (format: 'json' | 'csv') => {
    if (!healthData) return;

    const exportedAt = new Date().toISOString();
    const baseFilename = `system-health-${Date.now()}`;

    if (format === 'json') {
      const exportData = {
        exported_at: exportedAt,
        ...healthData,
      };
      downloadReport(JSON.stringify(exportData, null, 2), 'application/json', `${baseFilename}.json`);
      announceToScreenReader('System health report exported as JSON.');
    } else {
      const csvContent = createCsvContent(healthData, exportedAt);
      downloadReport(csvContent, 'text/csv', `${baseFilename}.csv`);
      announceToScreenReader('System health report exported as CSV.');
    }

    setExportAnchorEl(null);
  };

  const toggleCardExpanded = (featureName: string) => {
    setExpandedCards((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(featureName)) {
        newSet.delete(featureName);
      } else {
        newSet.add(featureName);
      }
      return newSet;
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#4caf50';
      case 'degraded':
        return '#ff9800';
      case 'failing':
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle sx={{ color: getStatusColor(status), transition: 'color 0.3s ease' }} />;
      case 'degraded':
        return <Warning sx={{ color: getStatusColor(status), transition: 'color 0.3s ease' }} />;
      case 'failing':
        return <ErrorIcon sx={{ color: getStatusColor(status), transition: 'color 0.3s ease' }} />;
      default:
        return <HelpOutline sx={{ color: getStatusColor(status), transition: 'color 0.3s ease' }} />;
    }
  };

  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now.getTime() - then.getTime();
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 60) return `${diffSecs} seconds ago`;
    if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)} minutes ago`;
    return `${Math.floor(diffSecs / 3600)} hours ago`;
  };

  const getCategoryDisplayName = (category: string) => {
    const names: Record<string, string> = {
      backend: 'Backend Core',
      scraping: 'Screen Scraping',
      ml: 'ML/Analytics',
      gui: 'GUI Components',
      advanced: 'Advanced Features',
    };
    return names[category] || category;
  };

  // Filter health checks
  const getFilteredChecks = () => {
    if (!healthData) return [];

    const allChecks: HealthStatus[] = [];
    Object.entries(healthData.categories).forEach(([category, data]) => {
      data.checks.forEach((check) => allChecks.push({ ...check, category }));
    });

    let filtered = allChecks;

    // Apply status filter
    if (filter !== 'all') {
      filtered = filtered.filter((check) => check.status === filter);
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (check) =>
          check.feature_name.toLowerCase().includes(query) ||
          check.category.toLowerCase().includes(query) ||
          check.description?.toLowerCase().includes(query)
      );
    }

    return filtered;
  };

  const filteredChecks = getFilteredChecks();

  // Group by category
  const groupedChecks: Record<string, HealthStatus[]> = {};
  filteredChecks.forEach((check) => {
    if (!groupedChecks[check.category]) {
      groupedChecks[check.category] = [];
    }
    groupedChecks[check.category].push(check);
  });

  if (loading) {
    return (
      <Box
        sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}
        role="status"
        aria-live="polite"
        aria-label="Loading system health data"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }} role="main" aria-label="System Status Monitor">
      {/* Screen reader announcer (visually hidden) */}
      <div
        ref={announcerRef}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: 'absolute',
          left: '-10000px',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
        }}
      />

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={2}>
        <Box>
          <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight="bold">
            System Status Monitor
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Real-time health monitoring for all pokertool components
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Tooltip title="Refresh all checks">
            <span style={{ display: 'inline-flex' }}>
              <IconButton
                onClick={handleRefresh}
                disabled={refreshing}
                color="primary"
                aria-label="Refresh all health checks"
                aria-busy={refreshing}
              >
                {refreshing ? <CircularProgress size={24} /> : <Refresh />}
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Export health report">
            <span style={{ display: 'inline-flex' }}>
              <IconButton
                onClick={(event) => setExportAnchorEl(event.currentTarget)}
                disabled={!healthData}
                aria-label="Open export menu"
                aria-haspopup="menu"
                aria-controls={exportAnchorEl ? 'export-menu' : undefined}
                aria-expanded={exportAnchorEl ? true : undefined}
              >
                <GetApp />
              </IconButton>
            </span>
          </Tooltip>
          <Menu
            id="export-menu"
            anchorEl={exportAnchorEl}
            open={Boolean(exportAnchorEl)}
            onClose={() => setExportAnchorEl(null)}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            MenuListProps={{ 'aria-label': 'Export format options' }}
          >
            <MenuItem
              onClick={() => handleExport('json')}
            >
              <ListItemIcon>
                <DescriptionIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Export as JSON" />
            </MenuItem>
            <MenuItem
              onClick={() => handleExport('csv')}
            >
              <ListItemIcon>
                <TableViewIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Export as CSV" />
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Overall Status Summary */}
      {healthData && (
        <Paper
          sx={{ p: 3, mb: 3 }}
          role="region"
          aria-label="System health summary"
        >
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box
                textAlign="center"
                role="status"
                aria-label={`Overall system status: ${healthData.overall_status}`}
              >
                <Fade in timeout={300} key={`overall-${healthData.overall_status}`}>
                  <Typography variant="h3" sx={{ color: getStatusColor(healthData.overall_status), transition: 'color 0.3s ease' }} aria-hidden="true">
                    {getStatusIcon(healthData.overall_status)}
                  </Typography>
                </Fade>
                <Typography variant="h6" mt={1}>
                  {healthData.overall_status.toUpperCase()}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Overall Status
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Fade in timeout={300} key={`count-healthy-${healthData.timestamp}`}>
                  <Typography variant="h3" color="success.main">
                    {Object.values(healthData.categories).reduce(
                      (sum, cat) => sum + cat.checks.filter(c => c.status === 'healthy').length,
                      0
                    )}
                  </Typography>
                </Fade>
                <Typography variant="h6" mt={1}>Healthy</Typography>
                <Typography variant="caption" color="textSecondary">
                  Features
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Fade in timeout={300} key={`count-degraded-${healthData.degraded_count}`}>
                  <Typography variant="h3" color="warning.main">
                    {healthData.degraded_count}
                  </Typography>
                </Fade>
                <Typography variant="h6" mt={1}>Degraded</Typography>
                <Typography variant="caption" color="textSecondary">
                  Features
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Fade in timeout={300} key={`count-failing-${healthData.failing_count}`}>
                  <Typography variant="h3" color="error.main">
                    {healthData.failing_count}
                  </Typography>
                </Fade>
                <Typography variant="h6" mt={1}>Failing</Typography>
                <Typography variant="caption" color="textSecondary">
                  Features
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Filters and Search */}
      <Paper sx={{ p: 2, mb: 3 }} role="search" aria-label="Filter and search health checks">
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search features..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                announceToScreenReader(`Searching for ${e.target.value || 'all features'}`);
              }}
              inputProps={{
                'aria-label': 'Search features by name or category',
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search aria-hidden="true" />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Box display="flex" gap={1} flexWrap="wrap" role="group" aria-label="Filter by status">
              {(['all', 'healthy', 'failing', 'degraded', 'unknown'] as FilterType[]).map((f) => (
                <Chip
                  key={f}
                  label={f.toUpperCase()}
                  onClick={() => {
                    setFilter(f);
                    announceToScreenReader(`Filtered to show ${f} features`);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setFilter(f);
                      announceToScreenReader(`Filtered to show ${f} features`);
                    }
                  }}
                  color={filter === f ? 'primary' : 'default'}
                  variant={filter === f ? 'filled' : 'outlined'}
                  size="small"
                  tabIndex={0}
                  aria-label={`Filter by ${f} status`}
                  aria-pressed={filter === f}
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Health Check Cards by Category */}
      {Object.entries(groupedChecks).map(([category, checks]) => (
        <Box key={category} mb={4} role="region" aria-label={`${getCategoryDisplayName(category)} health checks`}>
          <Typography variant="h6" fontWeight="bold" mb={2}>
            {getCategoryDisplayName(category)} ({checks.length})
          </Typography>
          <Grid container spacing={2}>
            {checks.map((check) => (
              <Grid item xs={12} sm={6} md={4} key={check.feature_name}>
                <Card
                  sx={{
                    height: '100%',
                    borderLeftWidth: 4,
                    borderLeftStyle: 'solid',
                    borderLeftColor: getStatusColor(check.status),
                    transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-left-color 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                    '&:focus-within': {
                      outline: `3px solid ${theme.palette.primary.main}`,
                      outlineOffset: '2px',
                    }
                  }}
                  role="article"
                  aria-label={`${check.feature_name.replace(/_/g, ' ')} health check`}
                >
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Fade in timeout={300} key={`icon-${check.status}`}>
                          <span aria-hidden="true">{getStatusIcon(check.status)}</span>
                        </Fade>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {check.feature_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Typography>
                      </Box>
                      {check.error_message && (
                        <IconButton
                          size="small"
                          onClick={() => toggleCardExpanded(check.feature_name)}
                          aria-label={expandedCards.has(check.feature_name) ? 'Hide error details' : 'Show error details'}
                          aria-expanded={expandedCards.has(check.feature_name)}
                        >
                          {expandedCards.has(check.feature_name) ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                      )}
                    </Box>

                    <Typography variant="caption" color="textSecondary" display="block" mb={1}>
                      {check.description || 'Health check for ' + check.feature_name}
                    </Typography>

                    <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                      <Fade in timeout={200} key={`chip-${check.status}`}>
                        <Chip
                          label={check.status.toUpperCase()}
                          size="small"
                          role="status"
                          aria-label={`Status: ${check.status}`}
                          sx={{
                            backgroundColor: getStatusColor(check.status),
                            color: '#fff',
                            fontWeight: 'bold',
                            transition: 'background-color 0.3s ease, color 0.3s ease',
                            border: theme.palette.mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.3)' : 'none',
                          }}
                        />
                      </Fade>
                      <Typography variant="caption" color="textSecondary" aria-label={`Last checked ${getTimeAgo(check.last_check)}`}>
                        {getTimeAgo(check.last_check)}
                      </Typography>
                    </Box>

                    {check.latency_ms && (
                      <Typography variant="caption" color="textSecondary" display="block" mt={1} aria-label={`Response time: ${check.latency_ms.toFixed(2)} milliseconds`}>
                        Latency: {check.latency_ms.toFixed(2)}ms
                      </Typography>
                    )}

                    {/* Error Details (Collapsible) */}
                    {check.error_message && (
                      <Collapse in={expandedCards.has(check.feature_name)} unmountOnExit>
                        <Divider sx={{ my: 2 }} />
                        <Alert severity="error" sx={{ fontSize: '0.75rem' }}>
                          <Typography variant="caption" fontWeight="bold">
                            Error Details:
                          </Typography>
                          <Typography variant="caption" display="block" mt={0.5}>
                            {check.error_message}
                          </Typography>
                        </Alert>
                      </Collapse>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      ))}

      {/* No Results */}
      {filteredChecks.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary">
            No features found matching your criteria
          </Typography>
          <Button onClick={() => { setFilter('all'); setSearchQuery(''); }} sx={{ mt: 2 }}>
            Clear Filters
          </Button>
        </Paper>
      )}

      {/* Footer Info */}
      {healthData && (
        <Paper sx={{ p: 2, mt: 3 }}>
          <Typography variant="caption" color="textSecondary">
            Last updated: {getTimeAgo(healthData.timestamp)} • Monitoring {filteredChecks.length} features
          </Typography>
        </Paper>
      )}
    </Box>
  );
};
