# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool-frontend/src/components/Dashboard.tsx
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  IconButton,
  Chip,
  LinearProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Casino,
  Timer,
  Refresh,
} from '@mui/icons-material';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { WebSocketMessage } from '../hooks/useWebSocket';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface DashboardProps {
  messages: WebSocketMessage[];
}

interface SessionStats {
  handsPlayed: number;
  vpip: number;
  pfr: number;
  aggression: number;
  winRate: number;
  profit: number;
  duration: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ messages }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [stats, setStats] = useState<SessionStats>({
    handsPlayed: 0,
    vpip: 0,
    pfr: 0,
    aggression: 0,
    winRate: 0,
    profit: 0,
    duration: '00:00:00',
  });

  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    // Process real-time updates from WebSocket
    const latestStatsMessage = messages
      .filter(msg => msg.type === 'stats_update')
      .pop();
    
    if (latestStatsMessage) {
      setStats(prevStats => ({
        ...prevStats,
        ...latestStatsMessage.data,
      }));
      setLastUpdate(new Date());
    }
  }, [messages]);

  const handleRefresh = () => {
    setLoading(true);
    // Simulate refresh
    setTimeout(() => {
      setLoading(false);
      setLastUpdate(new Date());
    }, 1000);
  };

  const profitChartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Profit ($)',
        data: [120, 190, 80, 250, 200, 400, 320],
        borderColor: theme.palette.primary.main,
        backgroundColor: `${theme.palette.primary.main}33`,
        tension: 0.4,
      },
    ],
  };

  const gameTypeData = {
    labels: ['Cash Games', 'Tournaments', 'Sit & Go'],
    datasets: [
      {
        data: [60, 30, 10],
        backgroundColor: [
          theme.palette.primary.main,
          theme.palette.secondary.main,
          theme.palette.warning.main,
        ],
      },
    ],
  };

  const StatCard = ({ title, value, icon, trend, color }: any) => (
    <Card
      sx={{
        height: '100%',
        background: theme.palette.mode === 'dark'
          ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
          : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
        },
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography color="textSecondary" variant="subtitle2" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {value}
            </Typography>
            {trend !== undefined && (
              <Box display="flex" alignItems="center" mt={1}>
                {trend > 0 ? (
                  <TrendingUp color="success" fontSize="small" />
                ) : (
                  <TrendingDown color="error" fontSize="small" />
                )}
                <Typography
                  variant="body2"
                  color={trend > 0 ? 'success.main' : 'error.main'}
                  ml={0.5}
                >
                  {Math.abs(trend)}%
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              backgroundColor: `${color}22`,
              borderRadius: 2,
              p: 1.5,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ flexGrow: 1, p: isMobile ? 2 : 3 }}>
      {loading && <LinearProgress />}
      
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight="bold">
          Dashboard
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Chip
            label={`Last Update: ${lastUpdate.toLocaleTimeString()}`}
            size="small"
            variant="outlined"
          />
          <IconButton onClick={handleRefresh} size="small">
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Stat Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Hands Played"
            value={stats.handsPlayed.toLocaleString()}
            icon={<Casino sx={{ fontSize: 28, color: theme.palette.primary.main }} />}
            trend={12}
            color={theme.palette.primary.main}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Session Profit"
            value={`$${stats.profit.toLocaleString()}`}
            icon={<AttachMoney sx={{ fontSize: 28, color: theme.palette.success.main }} />}
            trend={stats.profit > 0 ? 8 : -5}
            color={theme.palette.success.main}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Win Rate"
            value={`${stats.winRate}%`}
            icon={<TrendingUp sx={{ fontSize: 28, color: theme.palette.info.main }} />}
            trend={3}
            color={theme.palette.info.main}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Session Time"
            value={stats.duration}
            icon={<Timer sx={{ fontSize: 28, color: theme.palette.warning.main }} />}
            color={theme.palette.warning.main}
          />
        </Grid>

        {/* Profit Chart */}
        <Grid item xs={12} lg={8}>
          <Paper
            sx={{
              p: 3,
              height: isMobile ? 300 : 400,
              background: theme.palette.mode === 'dark'
                ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
                : 'white',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Weekly Profit Trend
            </Typography>
            <Box sx={{ height: isMobile ? 240 : 340 }}>
              <Line
                data={profitChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: false,
                    },
                  },
                  scales: {
                    y: {
                      grid: {
                        color: theme.palette.divider,
                      },
                      ticks: {
                        color: theme.palette.text.secondary,
                      },
                    },
                    x: {
                      grid: {
                        display: false,
                      },
                      ticks: {
                        color: theme.palette.text.secondary,
                      },
                    },
                  },
                }}
              />
            </Box>
          </Paper>
        </Grid>

        {/* Game Type Distribution */}
        <Grid item xs={12} lg={4}>
          <Paper
            sx={{
              p: 3,
              height: isMobile ? 300 : 400,
              background: theme.palette.mode === 'dark'
                ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
                : 'white',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Game Type Distribution
            </Typography>
            <Box
              sx={{
                height: isMobile ? 240 : 340,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Doughnut
                data={gameTypeData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                      labels: {
                        color: theme.palette.text.primary,
                      },
                    },
                  },
                }}
              />
            </Box>
          </Paper>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Playing Statistics
            </Typography>
            <Grid container spacing={2} mt={1}>
              <Grid item xs={6} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h5" color="primary" fontWeight="bold">
                    {stats.vpip}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    VPIP
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h5" color="secondary" fontWeight="bold">
                    {stats.pfr}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    PFR
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h5" color="info.main" fontWeight="bold">
                    {stats.aggression}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Aggression Factor
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h5" color="success.main" fontWeight="bold">
                    {stats.handsPlayed}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Hands
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
