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

import React, { useMemo, useRef, useState } from 'react';
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
  Skeleton,
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
import { useSystemHealthTrends, type HealthHistoryEntry } from '../hooks/useSystemHealthTrends';
import type { HealthStatus, HealthData } from '../hooks/useSystemHealth';
import { ErrorBoundary } from './ErrorBoundary';

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

  const [trendHours, setTrendHours] = useState<number>(24);
  const {
    trends,
    history,
    loading: trendsLoading,
    refreshing: trendsRefreshing,
    error: trendsError,
    refresh: refreshTrends,
  } = useSystemHealthTrends(trendHours, { autoFetch: true });

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
    await Promise.all([fetchHealthData(), refreshTrends()]);
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

  const formatFeatureName = (name: string) =>
    name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());

  const formatPercentage = (value?: number) =>
    value === undefined || value === null ? '—' : `${value.toFixed(1)}%`;

  const summarizeHistoryEntry = (entry: HealthHistoryEntry) => {
    const counts: Record<'healthy' | 'degraded' | 'failing' | 'unknown', number> = {
      healthy: 0,
      degraded: 0,
      failing: 0,
      unknown: 0,
    };

    Object.values(entry.results || {}).forEach((result) => {
      counts[result.status] = (counts[result.status] ?? 0) + 1;
    });

    return counts;
  };

  const trendWindowOptions = [6, 12, 24, 48, 168];

  const trendFeatureEntries = useMemo(() => {
    if (!trends) {
      return [];
    }

    return Object.entries(trends.feature_trends)
      .sort(([, a], [, b]) => (b.failing_pct ?? 0) - (a.failing_pct ?? 0))
      .slice(0, 6);
  }, [trends]);

  const recentHistory = useMemo(() => {
    if (!history.length) {
      return [];
    }

    return [...history].slice(-5).reverse();
  }, [history]);

  const handleTrendHoursChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTrendHours(Number(event.target.value));
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

  if (loading && !healthData) {
    return (
      <Box sx={{ p: isMobile ? 2 : 3 }}>
        <Skeleton variant="text" width={isMobile ? 220 : 320} height={isMobile ? 28 : 42} data-testid="system-status-skeleton-heading" />
        <Skeleton variant="text" width={isMobile ? 180 : 260} height={isMobile ? 18 : 24} sx={{ mb: 2 }} />

        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3}>
            {[...Array(4)].map((_, index) => (
              <Grid item xs={12} sm={6} md={3} key={`summary-skeleton-${index}`}>
                <Box textAlign="center">
                  <Skeleton variant="circular" width={54} height={54} sx={{ mx: 'auto' }} />
                  <Skeleton variant="text" width={80} sx={{ mx: 'auto', mt: 1 }} />
                  <Skeleton variant="text" width={60} sx={{ mx: 'auto' }} />
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>

        <Paper sx={{ p: 2, mb: 3 }}>
          <Skeleton variant="rectangular" height={isMobile ? 72 : 56} />
        </Paper>

        <Grid container spacing={2}>
          {[...Array(isMobile ? 1 : 3)].map((_, index) => (
            <Grid item xs={12} sm={6} md={4} key={`card-skeleton-${index}`}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Skeleton variant="text" width="60%" />
                  <Skeleton variant="text" width="40%" />
                  <Skeleton variant="rectangular" height={80} sx={{ mt: 2, borderRadius: 2 }} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

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

      {/* Health Trends */}
      <Paper
        sx={{ p: 3, mb: 3 }}
        role="region"
        aria-label={`System health trends for last ${trendHours} hours`}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
          <Box>
            <Typography variant="h6">Health Trends</Typography>
            {trends && (
              <Typography variant="body2" color="textSecondary">
                {`${trends.summary}. ${trends.data_points} samples collected.`}
              </Typography>
            )}
          </Box>
          <Box display="flex" alignItems="center" gap={2}>
            <TextField
              select
              size="small"
              label="Window"
              value={trendHours}
              onChange={handleTrendHoursChange}
              sx={{ minWidth: 120 }}
              inputProps={{ 'aria-label': 'Select health trend window (hours)' }}
            >
              {trendWindowOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}h
                </MenuItem>
              ))}
            </TextField>
            {trendsRefreshing && <CircularProgress size={20} aria-label="Loading health trends" />}
          </Box>
        </Box>

        {trendsError && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            {trendsError}
          </Alert>
        )}

        {trendsLoading && !trends ? (
          <Grid container spacing={2} mt={1}>
            <Grid item xs={12} md={7}>
              <Skeleton variant="rectangular" height={180} />
            </Grid>
            <Grid item xs={12} md={5}>
              <Skeleton variant="rectangular" height={180} />
            </Grid>
          </Grid>
        ) : trends ? (
          <Grid container spacing={3} mt={1}>
            <Grid item xs={12} md={7}>
              <Typography variant="subtitle1" gutterBottom>
                Watchlist (Top 6 by failure rate)
              </Typography>
              <Grid container spacing={2}>
                {trendFeatureEntries.map(([featureName, stats]) => (
                  <Grid item xs={12} sm={6} key={featureName}>
                    <Paper
                      variant="outlined"
                      sx={{ p: 2, height: '100%' }}
                      aria-label={`Trend summary for ${formatFeatureName(featureName)}`}
                    >
                      <Typography variant="subtitle2" fontWeight="bold">
                        {formatFeatureName(featureName)}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        Healthy uptime: {formatPercentage(stats.healthy_pct)}
                      </Typography>
                      <Grid container spacing={1}>
                        <Grid item xs={4}>
                          <Typography variant="caption" color="success.main">
                            Healthy
                          </Typography>
                          <Typography variant="body2">{stats.healthy}</Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="caption" color="warning.main">
                            Degraded
                          </Typography>
                          <Typography variant="body2">{stats.degraded}</Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="caption" color="error.main">
                            Failing
                          </Typography>
                          <Typography variant="body2">{stats.failing}</Typography>
                        </Grid>
                      </Grid>
                      <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                        Avg latency: {stats.avg_latency_ms !== undefined && stats.avg_latency_ms !== null
                          ? `${stats.avg_latency_ms.toFixed(1)} ms`
                          : 'n/a'}
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
                {!trendFeatureEntries.length && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">
                      Trend analytics will appear after the first scheduled health run completes.
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </Grid>
            <Grid item xs={12} md={5}>
              <Typography variant="subtitle1" gutterBottom>
                Recent samples
              </Typography>
              <Box display="flex" flexDirection="column" gap={1} role="list">
                {recentHistory.length ? recentHistory.map((entry) => {
                  const counts = summarizeHistoryEntry(entry);
                  return (
                    <Paper
                      key={entry.timestamp}
                      variant="outlined"
                      sx={{ p: 2 }}
                      role="listitem"
                      aria-label={`Health sample at ${new Date(entry.timestamp).toLocaleString()}`}
                    >
                      <Typography variant="body2" fontWeight="bold">
                        {new Date(entry.timestamp).toLocaleString()}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Healthy: {counts.healthy} | Degraded: {counts.degraded} | Failing: {counts.failing} | Unknown: {counts.unknown}
                      </Typography>
                    </Paper>
                  );
                }) : (
                  <Typography variant="body2" color="textSecondary">
                    Waiting for historical health samples...
                  </Typography>
                )}
              </Box>
            </Grid>
          </Grid>
        ) : (
          <Typography variant="body2" color="textSecondary" mt={2}>
            Trend analytics are generated once background health checks have persisted enough history.
          </Typography>
        )}
      </Paper>

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

export const SystemStatusWithBoundary: React.FC = () => (
  <ErrorBoundary fallbackType="general">
    <SystemStatus />
  </ErrorBoundary>
);

export default SystemStatusWithBoundary;
