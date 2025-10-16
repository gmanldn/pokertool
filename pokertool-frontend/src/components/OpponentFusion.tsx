/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/OpponentFusion.tsx
version: v86.2.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created Sequential Opponent Fusion UI for temporal pattern analysis
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
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Refresh,
  Person,
  Timeline,
  TrendingUp,
} from '@mui/icons-material';
import { buildApiUrl } from '../config/api';

interface OpponentFusionStats {
  tracked_players: number;
  total_hands_analyzed: number;
  active_patterns: number;
  prediction_accuracy: number;
  temporal_window_size: number;
  status: string;
}

export const OpponentFusion: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [stats, setStats] = useState<OpponentFusionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const response = await fetch(buildApiUrl('/api/ml/opponent-fusion/stats'));
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
      console.error('Failed to fetch opponent fusion data:', err);
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
            Sequential Opponent Fusion
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time temporal pattern analysis and opponent modeling
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
                  Tracked Players
                </Typography>
                <Typography variant="h6">{stats.tracked_players}</Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Hands Analyzed
                </Typography>
                <Typography variant="h6">{stats.total_hands_analyzed.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Active Patterns
                </Typography>
                <Typography variant="h6">{stats.active_patterns}</Typography>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUp /> Performance Metrics
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Prediction Accuracy
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      {(stats.prediction_accuracy * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Based on temporal modeling
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Temporal Window Size
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      {stats.temporal_window_size} hands
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Rolling history analyzed
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Person /> Tracked Players
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {stats.tracked_players === 0 ? (
              <Alert severity="info">
                No players currently tracked. Opponent modeling will begin once gameplay starts.
              </Alert>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Tracking {stats.tracked_players} player{stats.tracked_players !== 1 ? 's' : ''} with temporal analysis
              </Typography>
            )}
          </Paper>
        </>
      )}
    </Box>
  );
};

export default OpponentFusion;
