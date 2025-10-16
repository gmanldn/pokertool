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

import React, { useState, useEffect, useRef } from 'react';
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
} from '@mui/material';
import {
  Refresh,
  GetApp,
  Search,
  ExpandMore,
  ExpandLess,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  HelpOutline,
} from '@mui/icons-material';
import { buildApiUrl, httpToWs } from '../config/api';

interface HealthStatus {
  feature_name: string;
  category: string;
  status: 'healthy' | 'degraded' | 'failing' | 'unknown';
  last_check: string;
  latency_ms?: number;
  error_message?: string;
  metadata?: Record<string, any>;
  description?: string;
}

interface HealthData {
  timestamp: string;
  overall_status: string;
  categories: Record<string, {
    status: string;
    checks: HealthStatus[];
  }>;
  failing_count: number;
  degraded_count: number;
}

type FilterType = 'all' | 'healthy' | 'failing' | 'degraded' | 'unknown';

export const SystemStatus: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<FilterType>('all');
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch health data from API
  const fetchHealthData = async () => {
    try {
      setError(null);
      const response = await fetch(buildApiUrl('/api/system/health'));
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      const data = await response.json();
      setHealthData(data);
      setLoading(false);
      setRefreshing(false);
    } catch (err) {
      console.error('Failed to fetch health data:', err);
      setError('Failed to connect to backend. Is the server running?');
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Connect to WebSocket for real-time updates
  useEffect(() => {
    fetchHealthData();

    // WebSocket connection for real-time updates
    const connectWebSocket = () => {
      try {
        const wsUrl = httpToWs(buildApiUrl('/ws/system-health'));
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('System health WebSocket connected');
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'health_update') {
            // Update health data with new information
            fetchHealthData();
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('WebSocket closed, reconnecting in 10 seconds...');
          setTimeout(connectWebSocket, 10000);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
        setTimeout(connectWebSocket, 10000);
      }
    };

    connectWebSocket();

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchHealthData();
  };

  const handleExport = () => {
    if (!healthData) return;

    const exportData = {
      exported_at: new Date().toISOString(),
      ...healthData,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system-health-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
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
        return <CheckCircle sx={{ color: getStatusColor(status) }} />;
      case 'degraded':
        return <Warning sx={{ color: getStatusColor(status) }} />;
      case 'failing':
        return <ErrorIcon sx={{ color: getStatusColor(status) }} />;
      default:
        return <HelpOutline sx={{ color: getStatusColor(status) }} />;
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
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
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
            <IconButton onClick={handleRefresh} disabled={refreshing} color="primary">
              {refreshing ? <CircularProgress size={24} /> : <Refresh />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Export health report">
            <IconButton onClick={handleExport} disabled={!healthData}>
              <GetApp />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Overall Status Summary */}
      {healthData && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" sx={{ color: getStatusColor(healthData.overall_status) }}>
                  {getStatusIcon(healthData.overall_status)}
                </Typography>
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
                <Typography variant="h3" color="success.main">
                  {Object.values(healthData.categories).reduce(
                    (sum, cat) => sum + cat.checks.filter(c => c.status === 'healthy').length,
                    0
                  )}
                </Typography>
                <Typography variant="h6" mt={1}>Healthy</Typography>
                <Typography variant="caption" color="textSecondary">
                  Features
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="warning.main">
                  {healthData.degraded_count}
                </Typography>
                <Typography variant="h6" mt={1}>Degraded</Typography>
                <Typography variant="caption" color="textSecondary">
                  Features
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h3" color="error.main">
                  {healthData.failing_count}
                </Typography>
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
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search features..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Box display="flex" gap={1} flexWrap="wrap">
              {(['all', 'healthy', 'failing', 'degraded', 'unknown'] as FilterType[]).map((f) => (
                <Chip
                  key={f}
                  label={f.toUpperCase()}
                  onClick={() => setFilter(f)}
                  color={filter === f ? 'primary' : 'default'}
                  variant={filter === f ? 'filled' : 'outlined'}
                  size="small"
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Health Check Cards by Category */}
      {Object.entries(groupedChecks).map(([category, checks]) => (
        <Box key={category} mb={4}>
          <Typography variant="h6" fontWeight="bold" mb={2}>
            {getCategoryDisplayName(category)} ({checks.length})
          </Typography>
          <Grid container spacing={2}>
            {checks.map((check) => (
              <Grid item xs={12} sm={6} md={4} key={check.feature_name}>
                <Card
                  sx={{
                    height: '100%',
                    borderLeft: `4px solid ${getStatusColor(check.status)}`,
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    }
                  }}
                >
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getStatusIcon(check.status)}
                        <Typography variant="subtitle1" fontWeight="bold">
                          {check.feature_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Typography>
                      </Box>
                      {check.error_message && (
                        <IconButton
                          size="small"
                          onClick={() => toggleCardExpanded(check.feature_name)}
                        >
                          {expandedCards.has(check.feature_name) ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                      )}
                    </Box>

                    <Typography variant="caption" color="textSecondary" display="block" mb={1}>
                      {check.description || 'Health check for ' + check.feature_name}
                    </Typography>

                    <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                      <Chip
                        label={check.status.toUpperCase()}
                        size="small"
                        sx={{
                          backgroundColor: getStatusColor(check.status),
                          color: '#fff',
                          fontWeight: 'bold',
                        }}
                      />
                      <Typography variant="caption" color="textSecondary">
                        {getTimeAgo(check.last_check)}
                      </Typography>
                    </Box>

                    {check.latency_ms && (
                      <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                        Latency: {check.latency_ms.toFixed(2)}ms
                      </Typography>
                    )}

                    {/* Error Details (Collapsible) */}
                    {check.error_message && (
                      <Collapse in={expandedCards.has(check.feature_name)}>
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
