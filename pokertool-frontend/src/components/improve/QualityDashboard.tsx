/**Quality Metrics Dashboard - Track task completion, tests, coverage, commits*/
import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Box,
  LinearProgress,
  Chip,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {
  CheckCircle as CompletedIcon,
  Assignment as TasksIcon,
  BugReport as TestsIcon,
  Code as CoverageIcon,
  Commit as CommitsIcon,
  TrendingUp as TrendIcon,
  AccessTime as TimeIcon
} from '@mui/icons-material';

export interface QualityMetrics {
  tasksCompleted: number;
  tasksTotal: number;
  testsAdded: number;
  coveragePercent: number;
  coverageDelta: number;
  commitsCount: number;
  linesAdded: number;
  linesDeleted: number;
  avgTaskTime: number;  // in minutes
  successRate: number;  // percentage
  p0Completed: number;
  p1Completed: number;
  p2Completed: number;
  p3Completed: number;
}

export interface QualityDashboardProps {
  metrics?: QualityMetrics;
  loading?: boolean;
}

const DEFAULT_METRICS: QualityMetrics = {
  tasksCompleted: 0,
  tasksTotal: 0,
  testsAdded: 0,
  coveragePercent: 0,
  coverageDelta: 0,
  commitsCount: 0,
  linesAdded: 0,
  linesDeleted: 0,
  avgTaskTime: 0,
  successRate: 0,
  p0Completed: 0,
  p1Completed: 0,
  p2Completed: 0,
  p3Completed: 0
};

export const QualityDashboard: React.FC<QualityDashboardProps> = ({
  metrics = DEFAULT_METRICS,
  loading = false
}) => {
  const completionRate = metrics.tasksTotal > 0
    ? (metrics.tasksCompleted / metrics.tasksTotal) * 100
    : 0;

  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ReactNode;
    color?: string;
    trend?: number;
  }> = ({ title, value, subtitle, icon, color = 'primary.main', trend }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={1}>
          <Box
            sx={{
              bgcolor: color,
              color: 'white',
              p: 1,
              borderRadius: 1,
              mr: 2,
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {icon}
          </Box>
          <Box flex={1}>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              {value}
            </Typography>
          </Box>
          {trend !== undefined && trend !== 0 && (
            <Chip
              label={`${trend > 0 ? '+' : ''}${trend.toFixed(1)}%`}
              size="small"
              color={trend > 0 ? 'success' : 'error'}
              icon={<TrendIcon />}
            />
          )}
        </Box>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Quality Metrics Dashboard
      </Typography>

      <Grid container spacing={2} mb={3}>
        {/* Tasks Completed */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Tasks Completed"
            value={`${metrics.tasksCompleted}/${metrics.tasksTotal}`}
            subtitle={`${completionRate.toFixed(1)}% complete`}
            icon={<CompletedIcon />}
            color="success.main"
          />
        </Grid>

        {/* Tests Added */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Tests Added"
            value={metrics.testsAdded}
            subtitle="New test cases"
            icon={<TestsIcon />}
            color="info.main"
          />
        </Grid>

        {/* Code Coverage */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Coverage"
            value={`${metrics.coveragePercent.toFixed(1)}%`}
            subtitle={metrics.coverageDelta !== 0 ? `${metrics.coverageDelta > 0 ? '+' : ''}${metrics.coverageDelta.toFixed(1)}%` : 'No change'}
            icon={<CoverageIcon />}
            color="secondary.main"
            trend={metrics.coverageDelta}
          />
        </Grid>

        {/* Commits */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Commits"
            value={metrics.commitsCount}
            subtitle={`+${metrics.linesAdded} / -${metrics.linesDeleted} lines`}
            icon={<CommitsIcon />}
            color="warning.main"
          />
        </Grid>
      </Grid>

      {/* Progress Bar */}
      <Box mb={3}>
        <Box display="flex" justifyContent="space-between" mb={1}>
          <Typography variant="body2" color="text.secondary">
            Overall Progress
          </Typography>
          <Typography variant="body2" fontWeight="bold">
            {completionRate.toFixed(1)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={completionRate}
          sx={{ height: 8, borderRadius: 1 }}
        />
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Priority Breakdown */}
      <Box>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Tasks by Priority
        </Typography>
        <Grid container spacing={1}>
          <Grid item xs={3}>
            <Chip
              label={`P0: ${metrics.p0Completed}`}
              color="error"
              size="small"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={3}>
            <Chip
              label={`P1: ${metrics.p1Completed}`}
              color="warning"
              size="small"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={3}>
            <Chip
              label={`P2: ${metrics.p2Completed}`}
              color="info"
              size="small"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={3}>
            <Chip
              label={`P3: ${metrics.p3Completed}`}
              color="default"
              size="small"
              sx={{ width: '100%' }}
            />
          </Grid>
        </Grid>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Additional Stats */}
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Box display="flex" alignItems="center" gap={1}>
            <TimeIcon fontSize="small" color="action" />
            <Box>
              <Typography variant="caption" color="text.secondary">
                Avg Task Time
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {metrics.avgTaskTime.toFixed(1)} min
              </Typography>
            </Box>
          </Box>
        </Grid>
        <Grid item xs={6}>
          <Box display="flex" alignItems="center" gap={1}>
            <TrendIcon fontSize="small" color="action" />
            <Box>
              <Typography variant="caption" color="text.secondary">
                Success Rate
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {metrics.successRate.toFixed(1)}%
              </Typography>
            </Box>
          </Box>
        </Grid>
      </Grid>

      {loading && (
        <Box mt={2}>
          <LinearProgress />
        </Box>
      )}
    </Paper>
  );
};
