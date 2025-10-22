/**Provider Benchmarks - Track and compare AI provider performance*/
import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  LinearProgress,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  AttachMoney as CostIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendIcon,
  TrendingDown as TrendDownIcon
} from '@mui/icons-material';

export interface ProviderStats {
  provider: string;
  tasksCompleted: number;
  tasksAttempted: number;
  avgCompletionTime: number; // minutes
  successRate: number; // percentage
  totalCost: number; // dollars
  avgCostPerTask: number; // dollars
  reliability: number; // percentage (uptime)
  lastUsed: Date | null;
}

export interface ProviderBenchmarksProps {
  stats?: ProviderStats[];
  onRefresh?: () => void;
  loading?: boolean;
}

const defaultStats: ProviderStats[] = [
  {
    provider: 'claude-code',
    tasksCompleted: 45,
    tasksAttempted: 50,
    avgCompletionTime: 3.2,
    successRate: 90,
    totalCost: 2.5,
    avgCostPerTask: 0.056,
    reliability: 98,
    lastUsed: new Date()
  },
  {
    provider: 'anthropic',
    tasksCompleted: 38,
    tasksAttempted: 42,
    avgCompletionTime: 2.8,
    successRate: 90.5,
    totalCost: 1.9,
    avgCostPerTask: 0.05,
    reliability: 99,
    lastUsed: new Date()
  },
  {
    provider: 'openrouter',
    tasksCompleted: 28,
    tasksAttempted: 35,
    avgCompletionTime: 4.1,
    successRate: 80,
    totalCost: 1.4,
    avgCostPerTask: 0.05,
    reliability: 95,
    lastUsed: new Date()
  },
  {
    provider: 'openai',
    tasksCompleted: 32,
    tasksAttempted: 38,
    avgCompletionTime: 3.5,
    successRate: 84.2,
    totalCost: 1.6,
    avgCostPerTask: 0.05,
    reliability: 96,
    lastUsed: new Date()
  }
];

export const ProviderBenchmarks: React.FC<ProviderBenchmarksProps> = ({
  stats = defaultStats,
  onRefresh,
  loading = false
}) => {
  const getSuccessRateColor = (rate: number): 'success' | 'warning' | 'error' => {
    if (rate >= 85) return 'success';
    if (rate >= 70) return 'warning';
    return 'error';
  };

  const getReliabilityColor = (reliability: number): string => {
    if (reliability >= 95) return 'success.main';
    if (reliability >= 85) return 'warning.main';
    return 'error.main';
  };

  const formatTime = (minutes: number): string => {
    if (minutes < 1) {
      return `${Math.round(minutes * 60)}s`;
    }
    return `${minutes.toFixed(1)}m`;
  };

  const formatCost = (cost: number): string => {
    return `$${cost.toFixed(3)}`;
  };

  // Calculate recommendations
  const fastestProvider = stats.reduce((prev, current) =>
    prev.avgCompletionTime < current.avgCompletionTime ? prev : current
  );

  const cheapestProvider = stats.reduce((prev, current) =>
    prev.avgCostPerTask < current.avgCostPerTask ? prev : current
  );

  const mostReliable = stats.reduce((prev, current) =>
    prev.successRate > current.successRate ? prev : current
  );

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Provider Benchmarks</Typography>
        {onRefresh && (
          <IconButton onClick={onRefresh} disabled={loading} size="small">
            <RefreshIcon />
          </IconButton>
        )}
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Recommendations */}
      <Box display="flex" gap={1} mb={2} flexWrap="wrap">
        <Chip
          icon={<SpeedIcon />}
          label={`Fastest: ${fastestProvider.provider}`}
          size="small"
          color="primary"
        />
        <Chip
          icon={<CostIcon />}
          label={`Cheapest: ${cheapestProvider.provider}`}
          size="small"
          color="success"
        />
        <Chip
          icon={<SuccessIcon />}
          label={`Most Reliable: ${mostReliable.provider}`}
          size="small"
          color="info"
        />
      </Box>

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Provider</strong></TableCell>
              <TableCell align="right">
                <Tooltip title="Completed / Attempted">
                  <span>Tasks</span>
                </Tooltip>
              </TableCell>
              <TableCell align="right">
                <Tooltip title="Average time per task">
                  <Box display="flex" alignItems="center" justifyContent="flex-end" gap={0.5}>
                    <SpeedIcon fontSize="small" />
                    <span>Speed</span>
                  </Box>
                </Tooltip>
              </TableCell>
              <TableCell align="right">
                <Tooltip title="Success rate">
                  <Box display="flex" alignItems="center" justifyContent="flex-end" gap={0.5}>
                    <SuccessIcon fontSize="small" />
                    <span>Success</span>
                  </Box>
                </Tooltip>
              </TableCell>
              <TableCell align="right">
                <Tooltip title="Total cost (avg per task)">
                  <Box display="flex" alignItems="center" justifyContent="flex-end" gap={0.5}>
                    <CostIcon fontSize="small" />
                    <span>Cost</span>
                  </Box>
                </Tooltip>
              </TableCell>
              <TableCell align="right">
                <Tooltip title="Reliability / uptime">
                  <span>Reliability</span>
                </Tooltip>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stats.map((providerStats) => (
              <TableRow key={providerStats.provider} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {providerStats.provider}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2">
                    {providerStats.tasksCompleted} / {providerStats.tasksAttempted}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={formatTime(providerStats.avgCompletionTime)}
                    size="small"
                    icon={
                      providerStats.provider === fastestProvider.provider ? (
                        <TrendIcon />
                      ) : undefined
                    }
                  />
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={`${providerStats.successRate.toFixed(1)}%`}
                    size="small"
                    color={getSuccessRateColor(providerStats.successRate)}
                  />
                </TableCell>
                <TableCell align="right">
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      {formatCost(providerStats.totalCost)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ({formatCost(providerStats.avgCostPerTask)}/task)
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="right">
                  <LinearProgress
                    variant="determinate"
                    value={providerStats.reliability}
                    sx={{
                      width: 60,
                      height: 8,
                      borderRadius: 1,
                      '& .MuiLinearProgress-bar': {
                        bgcolor: getReliabilityColor(providerStats.reliability)
                      }
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {providerStats.reliability}%
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};
