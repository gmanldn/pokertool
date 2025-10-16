/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ModelCalibration.tsx
version: v86.0.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created Model Calibration component for ML drift monitoring
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  CircularProgress,
  Divider,
  Tooltip,
  useTheme,
  useMediaQuery,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Refresh,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Timeline,
} from '@mui/icons-material';
import { buildApiUrl } from '../config/api';

interface CalibrationStats {
  calibrator_method: string;
  total_updates: number;
  drift_status: string;
  last_calibration_metrics?: {
    brier_score: number;
    log_loss: number;
    calibration_error: number;
    num_predictions: number;
    timestamp: string;
  };
}

interface CalibrationMetric {
  timestamp: string;
  brier_score: number;
  log_loss: number;
  calibration_error: number;
  num_predictions: number;
}

interface DriftMetric {
  timestamp: string;
  psi: number;
  kl_divergence: number;
  distribution_shift: number;
  status: string;
  alerts: string[];
}

export const ModelCalibration: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [stats, setStats] = useState<CalibrationStats | null>(null);
  const [metrics, setMetrics] = useState<CalibrationMetric[]>([]);
  const [driftMetrics, setDriftMetrics] = useState<DriftMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch calibration data from API
  const fetchCalibrationData = async () => {
    try {
      setError(null);

      // Fetch stats
      const statsResponse = await fetch(buildApiUrl('/api/ml/calibration/stats'));
      if (!statsResponse.ok) {
        throw new Error(`Stats API returned ${statsResponse.status}`);
      }
      const statsData = await statsResponse.json();
      if (statsData.success) {
        setStats(statsData.data);
      }

      // Fetch metrics
      const metricsResponse = await fetch(buildApiUrl('/api/ml/calibration/metrics'));
      if (!metricsResponse.ok) {
        throw new Error(`Metrics API returned ${metricsResponse.status}`);
      }
      const metricsData = await metricsResponse.json();
      if (metricsData.success) {
        setMetrics(metricsData.metrics || []);
      }

      // Fetch drift metrics
      const driftResponse = await fetch(buildApiUrl('/api/ml/calibration/drift'));
      if (!driftResponse.ok) {
        throw new Error(`Drift API returned ${driftResponse.status}`);
      }
      const driftData = await driftResponse.json();
      if (driftData.success) {
        setDriftMetrics(driftData.drift_metrics || []);
      }

      setLoading(false);
      setRefreshing(false);
    } catch (err) {
      console.error('Failed to fetch calibration data:', err);
      setError('Failed to connect to backend. Is the server running?');
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCalibrationData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchCalibrationData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchCalibrationData();
  };

  const getDriftStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'nominal':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
      case 'retraining':
        return 'error';
      default:
        return 'default';
    }
  };

  const getDriftStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'nominal':
        return <CheckCircle />;
      case 'warning':
        return <Warning />;
      case 'critical':
      case 'retraining':
        return <ErrorIcon />;
      default:
        return <TrendingUp />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getMetricTrend = (values: number[]) => {
    if (values.length < 2) return 'stable';
    const recent = values.slice(-5);
    const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
    const first = recent[0];
    const last = recent[recent.length - 1];

    if (last > avg * 1.1) return 'up';
    if (last < avg * 0.9) return 'down';
    return 'stable';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  const latestDrift = driftMetrics.length > 0 ? driftMetrics[driftMetrics.length - 1] : null;
  const brierScores = metrics.map(m => m.brier_score);
  const logLosses = metrics.map(m => m.log_loss);
  const calibrationErrors = metrics.map(m => m.calibration_error);

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Model Calibration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time ML model drift detection and calibration metrics
          </Typography>
        </Box>
        <Tooltip title="Refresh data">
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <Refresh className={refreshing ? 'rotating' : ''} />
          </IconButton>
        </Tooltip>
      </Box>

      {refreshing && <LinearProgress sx={{ mb: 2 }} />}

      {/* Overall Status */}
      {stats && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Calibration Method
              </Typography>
              <Typography variant="h6">{stats.calibrator_method || 'Not Set'}</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Total Updates
              </Typography>
              <Typography variant="h6">{stats.total_updates.toLocaleString()}</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Drift Status
              </Typography>
              <Chip
                icon={getDriftStatusIcon(stats.drift_status)}
                label={stats.drift_status.toUpperCase()}
                color={getDriftStatusColor(stats.drift_status)}
                sx={{ fontWeight: 'bold' }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Predictions
              </Typography>
              <Typography variant="h6">
                {stats.last_calibration_metrics?.num_predictions.toLocaleString() || '0'}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Latest Calibration Metrics */}
      {stats?.last_calibration_metrics && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Timeline /> Latest Calibration Metrics
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Brier Score
                    </Typography>
                    {brierScores.length > 1 && (
                      getMetricTrend(brierScores) === 'up' ? <TrendingUp color="error" /> :
                      getMetricTrend(brierScores) === 'down' ? <TrendingDown color="success" /> : null
                    )}
                  </Box>
                  <Typography variant="h4" sx={{ mt: 1 }}>
                    {stats.last_calibration_metrics.brier_score.toFixed(4)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Lower is better
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Log Loss
                    </Typography>
                    {logLosses.length > 1 && (
                      getMetricTrend(logLosses) === 'up' ? <TrendingUp color="error" /> :
                      getMetricTrend(logLosses) === 'down' ? <TrendingDown color="success" /> : null
                    )}
                  </Box>
                  <Typography variant="h4" sx={{ mt: 1 }}>
                    {stats.last_calibration_metrics.log_loss.toFixed(4)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Lower is better
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Calibration Error (ECE)
                    </Typography>
                    {calibrationErrors.length > 1 && (
                      getMetricTrend(calibrationErrors) === 'up' ? <TrendingUp color="error" /> :
                      getMetricTrend(calibrationErrors) === 'down' ? <TrendingDown color="success" /> : null
                    )}
                  </Box>
                  <Typography variant="h4" sx={{ mt: 1 }}>
                    {stats.last_calibration_metrics.calibration_error.toFixed(4)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Lower is better
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Last updated: {formatTimestamp(stats.last_calibration_metrics.timestamp)}
          </Typography>
        </Paper>
      )}

      {/* Drift Detection */}
      {latestDrift && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Warning /> Drift Detection Metrics
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    PSI (Population Stability Index)
                  </Typography>
                  <Typography variant="h4">
                    {latestDrift.psi.toFixed(4)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {latestDrift.psi < 0.1 ? 'No significant change' :
                     latestDrift.psi < 0.2 ? 'Moderate shift' : 'Significant shift'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    KL Divergence
                  </Typography>
                  <Typography variant="h4">
                    {latestDrift.kl_divergence.toFixed(4)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Distribution similarity
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Distribution Shift
                  </Typography>
                  <Typography variant="h4">
                    {(latestDrift.distribution_shift * 100).toFixed(2)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Feature drift magnitude
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {latestDrift.alerts.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Active Alerts
              </Typography>
              {latestDrift.alerts.map((alert, idx) => (
                <Alert key={idx} severity="warning" sx={{ mt: 1 }}>
                  {alert}
                </Alert>
              ))}
            </Box>
          )}

          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Last checked: {formatTimestamp(latestDrift.timestamp)}
          </Typography>
        </Paper>
      )}

      {/* Historical Metrics Summary */}
      {metrics.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Historical Data
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Tracking {metrics.length} calibration metric{metrics.length !== 1 ? 's' : ''} and{' '}
            {driftMetrics.length} drift measurement{driftMetrics.length !== 1 ? 's' : ''}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Data is updated in real-time as the model processes predictions
          </Typography>
        </Paper>
      )}

      {/* No Data State */}
      {!stats && !metrics.length && !driftMetrics.length && (
        <Alert severity="info">
          No calibration data available yet. The model calibration system will begin tracking metrics
          once predictions are made.
        </Alert>
      )}
    </Box>
  );
};

export default ModelCalibration;
