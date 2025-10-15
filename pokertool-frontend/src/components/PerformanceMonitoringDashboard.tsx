import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Alert
} from '@mui/material';
import {
  Speed,
  Memory,
  NetworkCheck,
  Timer,
  Refresh,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  TrendingUp,
  TrendingDown
} from '@mui/icons-material';

interface PerformanceMetrics {
  fps: number;
  renderTime: number;
  apiLatency: number;
  wsLatency: number;
  memoryUsage: number;
  componentRenderCounts: { [key: string]: number };
  slowRenders: Array<{ component: string; time: number; timestamp: number }>;
  apiCalls: Array<{ endpoint: string; duration: number; timestamp: number }>;
}

interface PerformanceBudget {
  fps: { min: number; target: number };
  renderTime: { max: number; warning: number };
  apiLatency: { max: number; warning: number };
  wsLatency: { max: number; warning: number };
  memoryUsage: { max: number; warning: number };
}

const DEFAULT_BUDGETS: PerformanceBudget = {
  fps: { min: 30, target: 60 },
  renderTime: { max: 50, warning: 30 },
  apiLatency: { max: 1000, warning: 500 },
  wsLatency: { max: 200, warning: 100 },
  memoryUsage: { max: 500, warning: 300 }
};

export const PerformanceMonitoringDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    renderTime: 12.5,
    apiLatency: 145,
    wsLatency: 45,
    memoryUsage: 185,
    componentRenderCounts: {
      'AdvicePanel': 142,
      'TableView': 89,
      'OpponentStats': 67,
      'HandHistory': 23,
      'Dashboard': 156
    },
    slowRenders: [],
    apiCalls: []
  });

  const [budgets] = useState<PerformanceBudget>(DEFAULT_BUDGETS);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [monitoring, setMonitoring] = useState(true);

  // Monitor performance
  useEffect(() => {
    if (!monitoring) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'measure') {
          // Track render times
          if (entry.name.includes('React')) {
            setMetrics(prev => {
              const slowRenders = [...prev.slowRenders];
              if (entry.duration > budgets.renderTime.warning) {
                slowRenders.push({
                  component: entry.name,
                  time: entry.duration,
                  timestamp: Date.now()
                });
                // Keep only last 20
                if (slowRenders.length > 20) slowRenders.shift();
              }
              return { ...prev, slowRenders };
            });
          }
        }
      }
    });

    observer.observe({ entryTypes: ['measure', 'navigation'] });

    return () => observer.disconnect();
  }, [monitoring, budgets]);

  // Simulate real-time updates
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        fps: 55 + Math.random() * 10,
        renderTime: 10 + Math.random() * 15,
        apiLatency: 100 + Math.random() * 200,
        wsLatency: 30 + Math.random() * 60,
        memoryUsage: 150 + Math.random() * 100
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Track memory usage
  useEffect(() => {
    const updateMemory = () => {
      if ('memory' in performance && (performance as any).memory) {
        const mem = (performance as any).memory;
        const usedMB = mem.usedJSHeapSize / 1024 / 1024;
        setMetrics(prev => ({ ...prev, memoryUsage: usedMB }));
      }
    };

    const interval = setInterval(updateMemory, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (value: number, max: number, warning: number): string => {
    if (value > max) return '#f44336';
    if (value > warning) return '#ff9800';
    return '#4caf50';
  };

  const getStatusIcon = (value: number, max: number, warning: number) => {
    if (value > max) return <ErrorIcon sx={{ color: '#f44336' }} />;
    if (value > warning) return <Warning sx={{ color: '#ff9800' }} />;
    return <CheckCircle sx={{ color: '#4caf50' }} />;
  };

  const formatBytes = (bytes: number): string => {
    return `${bytes.toFixed(1)} MB`;
  };

  const formatMs = (ms: number): string => {
    return `${ms.toFixed(1)}ms`;
  };

  const getPercentile = (values: number[], percentile: number): number => {
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[index] || 0;
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Speed />
          Performance Monitoring
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label={monitoring ? 'Monitoring ON' : 'Monitoring OFF'}
            color={monitoring ? 'success' : 'default'}
            onClick={() => setMonitoring(!monitoring)}
            size="small"
          />
          <Chip
            label={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            color={autoRefresh ? 'success' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            size="small"
          />
          <IconButton size="small">
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* FPS Metric */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography color="text.secondary">Frame Rate (FPS)</Typography>
                {getStatusIcon(60 - metrics.fps, 30, 10)}
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {metrics.fps.toFixed(0)}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Target: {budgets.fps.target} FPS
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(metrics.fps / budgets.fps.target) * 100}
                sx={{
                  height: 8,
                  borderRadius: 1,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getStatusColor(budgets.fps.target - metrics.fps, 30, 10)
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Render Time */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography color="text.secondary">Render Time</Typography>
                {getStatusIcon(metrics.renderTime, budgets.renderTime.max, budgets.renderTime.warning)}
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {formatMs(metrics.renderTime)}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Budget: &lt;{budgets.renderTime.max}ms
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min((metrics.renderTime / budgets.renderTime.max) * 100, 100)}
                sx={{
                  height: 8,
                  borderRadius: 1,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getStatusColor(metrics.renderTime, budgets.renderTime.max, budgets.renderTime.warning)
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* API Latency */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography color="text.secondary">API Latency</Typography>
                {getStatusIcon(metrics.apiLatency, budgets.apiLatency.max, budgets.apiLatency.warning)}
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {formatMs(metrics.apiLatency)}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Budget: &lt;{budgets.apiLatency.max}ms
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min((metrics.apiLatency / budgets.apiLatency.max) * 100, 100)}
                sx={{
                  height: 8,
                  borderRadius: 1,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getStatusColor(metrics.apiLatency, budgets.apiLatency.max, budgets.apiLatency.warning)
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Memory Usage */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography color="text.secondary">Memory Usage</Typography>
                {getStatusIcon(metrics.memoryUsage, budgets.memoryUsage.max, budgets.memoryUsage.warning)}
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {formatBytes(metrics.memoryUsage)}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Budget: &lt;{formatBytes(budgets.memoryUsage.max)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min((metrics.memoryUsage / budgets.memoryUsage.max) * 100, 100)}
                sx={{
                  height: 8,
                  borderRadius: 1,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getStatusColor(metrics.memoryUsage, budgets.memoryUsage.max, budgets.memoryUsage.warning)
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Component Render Counts */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Component Render Counts
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Component</TableCell>
                      <TableCell align="right">Renders</TableCell>
                      <TableCell align="right">Trend</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(metrics.componentRenderCounts)
                      .sort((a, b) => b[1] - a[1])
                      .map(([component, count]) => (
                        <TableRow key={component}>
                          <TableCell>{component}</TableCell>
                          <TableCell align="right">{count}</TableCell>
                          <TableCell align="right">
                            {count > 100 ? (
                              <TrendingUp sx={{ fontSize: 18, color: '#ff9800' }} />
                            ) : (
                              <TrendingDown sx={{ fontSize: 18, color: '#4caf50' }} />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Slow Renders */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Slow Renders (&gt;{budgets.renderTime.warning}ms)
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {metrics.slowRenders.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CheckCircle sx={{ fontSize: 48, color: '#4caf50', mb: 1 }} />
                  <Typography color="text.secondary">
                    No slow renders detected
                  </Typography>
                </Box>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Component</TableCell>
                        <TableCell align="right">Duration</TableCell>
                        <TableCell align="right">Time</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {metrics.slowRenders.slice(-10).reverse().map((render, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{render.component}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={formatMs(render.time)}
                              size="small"
                              color={render.time > budgets.renderTime.max ? 'error' : 'warning'}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="caption" color="text.secondary">
                              {new Date(render.timestamp).toLocaleTimeString()}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Alerts */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: 'background.paper' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Budget Status
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                {metrics.fps < budgets.fps.min && (
                  <Grid item xs={12}>
                    <Alert severity="error" icon={<ErrorIcon />}>
                      <strong>FPS below minimum:</strong> Current {metrics.fps.toFixed(0)} FPS is below the minimum threshold of {budgets.fps.min} FPS
                    </Alert>
                  </Grid>
                )}
                {metrics.renderTime > budgets.renderTime.max && (
                  <Grid item xs={12}>
                    <Alert severity="error" icon={<ErrorIcon />}>
                      <strong>Render time exceeded:</strong> Current {formatMs(metrics.renderTime)} exceeds budget of {formatMs(budgets.renderTime.max)}
                    </Alert>
                  </Grid>
                )}
                {metrics.apiLatency > budgets.apiLatency.max && (
                  <Grid item xs={12}>
                    <Alert severity="error" icon={<ErrorIcon />}>
                      <strong>API latency exceeded:</strong> Current {formatMs(metrics.apiLatency)} exceeds budget of {formatMs(budgets.apiLatency.max)}
                    </Alert>
                  </Grid>
                )}
                {metrics.memoryUsage > budgets.memoryUsage.max && (
                  <Grid item xs={12}>
                    <Alert severity="error" icon={<ErrorIcon />}>
                      <strong>Memory usage exceeded:</strong> Current {formatBytes(metrics.memoryUsage)} exceeds budget of {formatBytes(budgets.memoryUsage.max)}
                    </Alert>
                  </Grid>
                )}
                {metrics.fps >= budgets.fps.min &&
                 metrics.renderTime <= budgets.renderTime.max &&
                 metrics.apiLatency <= budgets.apiLatency.max &&
                 metrics.memoryUsage <= budgets.memoryUsage.max && (
                  <Grid item xs={12}>
                    <Alert severity="success" icon={<CheckCircle />}>
                      <strong>All metrics within budget!</strong> Application performance is optimal.
                    </Alert>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PerformanceMonitoringDashboard;
