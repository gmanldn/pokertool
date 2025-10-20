/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ScrapingAccuracy.tsx
version: v86.2.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created Scraping Accuracy Dashboard for OCR and scraping metrics
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
  IconButton,
  CircularProgress,
  Divider,
  Chip,
  Alert,
  LinearProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Refresh,
  Visibility,
  CheckCircle,
  Build,
} from '@mui/icons-material';
import { buildApiUrl } from '../config/api';

interface ScrapingAccuracyStats {
  overall_accuracy: number;
  pot_corrections: number;
  card_recognition_accuracy: number;
  ocr_corrections: number;
  temporal_consensus_improvements: number;
  total_frames_processed: number;
  status: string;
}

export const ScrapingAccuracy: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [stats, setStats] = useState<ScrapingAccuracyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const response = await fetch(buildApiUrl('/api/scraping/accuracy/stats'));
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        setStats(data.data);
      }
      setLoading(false);
      setRefreshing(false);
    } catch (err) {
      console.error('Failed to fetch scraping accuracy data:', err);
      setError('Failed to connect to backend. Is the server running?');
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.95) return 'success';
    if (accuracy >= 0.85) return 'warning';
    return 'error';
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

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Scraping Accuracy System
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time OCR accuracy tracking and temporal consensus improvements
          </Typography>
        </Box>
        <IconButton onClick={handleRefresh} disabled={refreshing}>
          <Refresh className={refreshing ? 'rotating' : ''} />
        </IconButton>
      </Box>

      {stats && (
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Status
                </Typography>
                <Chip
                  label={stats.status.toUpperCase()}
                  color={stats.status === 'active' ? 'success' : 'default'}
                  sx={{ fontWeight: 'bold' }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Overall Accuracy
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h6">{(stats.overall_accuracy * 100).toFixed(1)}%</Typography>
                  <Chip
                    size="small"
                    label={stats.overall_accuracy >= 0.95 ? 'Excellent' : 'Good'}
                    color={getAccuracyColor(stats.overall_accuracy)}
                  />
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Frames Processed
                </Typography>
                <Typography variant="h6">{stats.total_frames_processed.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Corrections
                </Typography>
                <Typography variant="h6">
                  {(stats.pot_corrections + stats.ocr_corrections).toLocaleString()}
                </Typography>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Visibility /> Recognition Metrics
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Card Recognition
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      {(stats.card_recognition_accuracy * 100).toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={stats.card_recognition_accuracy * 100}
                      sx={{ mt: 1 }}
                      color={getAccuracyColor(stats.card_recognition_accuracy)}
                    />
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Pot Corrections
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      {stats.pot_corrections.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Context-aware validation
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      OCR Corrections
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      {stats.ocr_corrections.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Post-processing rules
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Build /> Accuracy Improvements
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Temporal Consensus
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      {stats.temporal_consensus_improvements.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Multi-frame smoothing corrections
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Alert severity="success" icon={<CheckCircle />}>
                  System is actively improving accuracy through multiple validation strategies
                </Alert>
              </Grid>
            </Grid>
          </Paper>
        </>
      )}
    </Box>
  );
};

export default ScrapingAccuracy;
