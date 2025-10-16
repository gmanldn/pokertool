/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ActiveLearning.tsx
version: v86.2.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created Active Learning Interface for model improvement feedback
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
  School,
  CheckCircle,
  Warning,
  TrendingUp,
} from '@mui/icons-material';
import { buildApiUrl } from '../config/api';

interface ActiveLearningStats {
  pending_reviews: number;
  total_feedback: number;
  high_uncertainty_events: number;
  model_accuracy_improvement: number;
  last_retraining: string | null;
  status: string;
}

export const ActiveLearning: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [stats, setStats] = useState<ActiveLearningStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const response = await fetch(buildApiUrl('/api/ml/active-learning/stats'));
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
      console.error('Failed to fetch active learning data:', err);
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

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
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
            Active Learning Feedback
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Continuous model improvement through expert feedback on uncertain predictions
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
                  Pending Reviews
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h6">{stats.pending_reviews}</Typography>
                  {stats.pending_reviews > 0 && <Warning color="warning" />}
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Feedback
                </Typography>
                <Typography variant="h6">{stats.total_feedback.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  High Uncertainty
                </Typography>
                <Typography variant="h6">{stats.high_uncertainty_events}</Typography>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUp /> Model Improvement
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Accuracy Improvement
                    </Typography>
                    <Typography variant="h4" sx={{ mt: 1 }}>
                      +{(stats.model_accuracy_improvement * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      From active learning feedback
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Last Retraining
                    </Typography>
                    <Typography variant="h6" sx={{ mt: 1 }}>
                      {formatDate(stats.last_retraining)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Next: Automated weekly batch
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <School /> Feedback Queue
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {stats.pending_reviews === 0 ? (
              <Alert severity="success" icon={<CheckCircle />}>
                All feedback events have been reviewed. The system is running optimally.
              </Alert>
            ) : (
              <>
                <Alert severity="info" sx={{ mb: 2 }}>
                  {stats.pending_reviews} event{stats.pending_reviews !== 1 ? 's' : ''} awaiting expert review
                </Alert>
                <Typography variant="body2" color="text.secondary">
                  High uncertainty events are automatically queued for human review to improve model accuracy.
                </Typography>
              </>
            )}
          </Paper>
        </>
      )}
    </Box>
  );
};

export default ActiveLearning;
