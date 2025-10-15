import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Grid, 
  LinearProgress,
  Chip,
  Divider,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  TrendingFlat,
  AccessTime,
  AttachMoney,
  Casino,
  CheckCircle,
  Cancel,
  Info,
  Refresh
} from '@mui/icons-material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

interface SessionStats {
  handsPlayed: number;
  handsWon: number;
  handsLost: number;
  winRate: number;
  roi: number;
  profitLoss: number;
  adviceFollowedCount: number;
  adviceIgnoredCount: number;
  adviceFollowedWinRate: number;
  adviceIgnoredWinRate: number;
  sessionDuration: number;
  handsPerHour: number;
  biggestWin: { amount: number; hand: string };
  biggestLoss: { amount: number; hand: string };
  profitHistory: number[];
  timeLabels: string[];
}

interface SessionPerformanceDashboardProps {
  compact?: boolean;
  onRefresh?: () => void;
}

export const SessionPerformanceDashboard: React.FC<SessionPerformanceDashboardProps> = ({ 
  compact = false,
  onRefresh
}) => {
  const [stats, setStats] = useState<SessionStats>({
    handsPlayed: 142,
    handsWon: 68,
    handsLost: 74,
    winRate: 47.9,
    roi: 12.3,
    profitLoss: 234.50,
    adviceFollowedCount: 98,
    adviceIgnoredCount: 44,
    adviceFollowedWinRate: 52.0,
    adviceIgnoredWinRate: 38.6,
    sessionDuration: 7200, // 2 hours in seconds
    handsPerHour: 71,
    biggestWin: { amount: 450.00, hand: 'AA vs KK - All-in preflop' },
    biggestLoss: { amount: -225.00, hand: 'KK vs AA - Cooler' },
    profitHistory: [0, 50, 120, 80, 150, 200, 180, 234.50],
    timeLabels: ['0m', '15m', '30m', '45m', '1h', '1h15m', '1h30m', '2h']
  });

  const [autoRefresh, setAutoRefresh] = useState(true);

  // Simulate real-time updates
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        handsPlayed: prev.handsPlayed + Math.floor(Math.random() * 2),
        handsWon: prev.handsWon + (Math.random() > 0.5 ? 1 : 0),
        handsLost: prev.handsLost + (Math.random() > 0.5 ? 1 : 0),
        winRate: 47.9 + Math.random() * 5 - 2.5,
        profitLoss: prev.profitLoss + Math.random() * 50 - 20,
        handsPerHour: 71 + Math.floor(Math.random() * 10 - 5)
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const adviceAdherenceRate = stats.handsPlayed > 0
    ? ((stats.adviceFollowedCount / stats.handsPlayed) * 100).toFixed(1)
    : '0';

  const getTrendIcon = (value: number) => {
    if (value > 0) return <TrendingUp sx={{ color: '#4caf50' }} />;
    if (value < 0) return <TrendingDown sx={{ color: '#f44336' }} />;
    return <TrendingFlat sx={{ color: '#ff9800' }} />;
  };

  const chartData = {
    labels: stats.timeLabels,
    datasets: [
      {
        label: 'Profit/Loss ($)',
        data: stats.profitHistory,
        fill: true,
        backgroundColor: stats.profitLoss >= 0 ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
        borderColor: stats.profitLoss >= 0 ? '#4caf50' : '#f44336',
        borderWidth: 2,
        tension: 0.4,
        pointRadius: compact ? 0 : 4,
        pointHoverRadius: compact ? 4 : 6,
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: !compact,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => `$${context.parsed.y.toFixed(2)}`
        }
      }
    },
    scales: {
      x: {
        display: !compact,
        grid: {
          display: false
        }
      },
      y: {
        display: !compact,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)'
        },
        ticks: {
          callback: (value: any) => `$${value}`
        }
      }
    }
  };

  if (compact) {
    // Compact view for integration with other components
    return (
      <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Session Stats</Typography>
            {getTrendIcon(stats.profitLoss)}
          </Box>
          <Grid container spacing={1}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Win Rate</Typography>
              <Typography variant="h6">{stats.winRate.toFixed(1)}%</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">P/L</Typography>
              <Typography 
                variant="h6" 
                sx={{ color: stats.profitLoss >= 0 ? '#4caf50' : '#f44336' }}
              >
                ${stats.profitLoss.toFixed(2)}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Hands</Typography>
              <Typography variant="h6">{stats.handsPlayed}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">ROI</Typography>
              <Typography variant="h6">{stats.roi.toFixed(1)}%</Typography>
            </Grid>
          </Grid>
          <Box sx={{ mt: 2, height: 100 }}>
            <Line data={chartData} options={chartOptions} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Full view
  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Session Performance Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip 
            label={autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
            color={autoRefresh ? "success" : "default"}
            onClick={() => setAutoRefresh(!autoRefresh)}
            size="small"
          />
          <IconButton onClick={onRefresh} size="small">
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Key Metrics Cards */}
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography color="text.secondary" gutterBottom>
                  Win Rate
                </Typography>
                {getTrendIcon(stats.winRate - 50)}
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {stats.winRate.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stats.handsWon}W / {stats.handsLost}L
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={stats.winRate} 
                sx={{ 
                  mt: 1,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: stats.winRate >= 50 ? '#4caf50' : '#ff9800'
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography color="text.secondary" gutterBottom>
                  Profit/Loss
                </Typography>
                <AttachMoney />
              </Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  mb: 1, 
                  color: stats.profitLoss >= 0 ? '#4caf50' : '#f44336' 
                }}
              >
                ${Math.abs(stats.profitLoss).toFixed(2)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ROI: {stats.roi.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography color="text.secondary" gutterBottom>
                  Hands Played
                </Typography>
                <Casino />
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {stats.handsPlayed}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stats.handsPerHour} hands/hour
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography color="text.secondary" gutterBottom>
                  Session Time
                </Typography>
                <AccessTime />
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {formatDuration(stats.sessionDuration)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active play time
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Advice Adherence Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Advice Adherence Analysis
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(76, 175, 80, 0.1)' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <CheckCircle sx={{ color: '#4caf50', mr: 1 }} />
                      <Typography variant="subtitle2">Advice Followed</Typography>
                    </Box>
                    <Typography variant="h6">{stats.adviceFollowedCount} hands</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Win rate: {stats.adviceFollowedWinRate.toFixed(1)}%
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(244, 67, 54, 0.1)' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Cancel sx={{ color: '#f44336', mr: 1 }} />
                      <Typography variant="subtitle2">Advice Ignored</Typography>
                    </Box>
                    <Typography variant="h6">{stats.adviceIgnoredCount} hands</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Win rate: {stats.adviceIgnoredWinRate.toFixed(1)}%
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Adherence Rate</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {adviceAdherenceRate}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={parseFloat(adviceAdherenceRate)} 
                  sx={{ 
                    height: 8,
                    borderRadius: 1,
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: parseFloat(adviceAdherenceRate) >= 70 ? '#4caf50' : '#ff9800'
                    }
                  }}
                />
              </Box>

              <Tooltip title="Following advice resulted in a 13.4% higher win rate in this session">
                <Box sx={{ 
                  mt: 2, 
                  p: 1, 
                  bgcolor: 'rgba(33, 150, 243, 0.1)', 
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <Info sx={{ fontSize: 16, mr: 1, color: '#2196f3' }} />
                  <Typography variant="caption">
                    Win rate difference: +{(stats.adviceFollowedWinRate - stats.adviceIgnoredWinRate).toFixed(1)}% when following advice
                  </Typography>
                </Box>
              </Tooltip>
            </CardContent>
          </Card>
        </Grid>

        {/* Profit Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: 'background.paper', height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session Profit Chart
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ height: 250 }}>
                <Line data={chartData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Best/Worst Hands */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: 'background.paper' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notable Hands
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ 
                    p: 2, 
                    bgcolor: 'rgba(76, 175, 80, 0.05)',
                    border: '1px solid rgba(76, 175, 80, 0.3)'
                  }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Biggest Win
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#4caf50', mb: 1 }}>
                      +${stats.biggestWin.amount.toFixed(2)}
                    </Typography>
                    <Typography variant="body2">
                      {stats.biggestWin.hand}
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Paper sx={{ 
                    p: 2, 
                    bgcolor: 'rgba(244, 67, 54, 0.05)',
                    border: '1px solid rgba(244, 67, 54, 0.3)'
                  }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Biggest Loss
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#f44336', mb: 1 }}>
                      {stats.biggestLoss.amount.toFixed(2)}
                    </Typography>
                    <Typography variant="body2">
                      {stats.biggestLoss.hand}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SessionPerformanceDashboard;
