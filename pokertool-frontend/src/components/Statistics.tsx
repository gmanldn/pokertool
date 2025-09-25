# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool-frontend/src/components/Statistics.tsx
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  useTheme,
  SelectChangeEvent,
} from '@mui/material';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
);

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`statistics-tabpanel-${index}`}
      aria-labelledby={`statistics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  color?: string;
}

export const Statistics: React.FC = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState('30d');
  const [gameType, setGameType] = useState('all');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    setTimeRange(event.target.value);
  };

  const handleGameTypeChange = (event: SelectChangeEvent) => {
    setGameType(event.target.value);
  };

  // Sample data for charts
  const profitChartData = {
    labels: ['Jan 1', 'Jan 2', 'Jan 3', 'Jan 4', 'Jan 5', 'Jan 6', 'Jan 7'],
    datasets: [
      {
        label: 'Profit ($)',
        data: [150, -75, 220, 100, -50, 300, 180],
        borderColor: theme.palette.primary.main,
        backgroundColor: `${theme.palette.primary.main}33`,
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const handStrengthChartData = {
    labels: ['Premium', 'Strong', 'Medium', 'Weak'],
    datasets: [
      {
        label: 'Profit ($)',
        data: [850, 450, 120, -320],
        backgroundColor: ['#4caf50', '#2196f3', '#ff9800', '#f44336'],
      },
    ],
  };

  const handDistributionData = {
    labels: ['Premium (AA-QQ, AK)', 'Strong (JJ-99, AQ-AJ)', 'Medium (88-22, KQ-KJ)', 'Weak (Others)'],
    datasets: [
      {
        data: [120, 280, 420, 680],
        backgroundColor: ['#4caf50', '#2196f3', '#ff9800', '#f44336'],
      },
    ],
  };

  const opponentCountData = {
    labels: ['Tight-Passive', 'Loose-Passive', 'Tight-Aggressive', 'Loose-Aggressive'],
    datasets: [
      {
        label: 'Count',
        data: [15, 12, 8, 5],
        backgroundColor: theme.palette.primary.main,
      },
    ],
  };

  const opponentProfitData = {
    labels: ['Tight-Passive', 'Loose-Passive', 'Tight-Aggressive', 'Loose-Aggressive'],
    datasets: [
      {
        label: 'Profit ($)',
        data: [320, 450, -80, 150],
        backgroundColor: [
          theme.palette.success.main,
          theme.palette.success.main,
          theme.palette.error.main,
          theme.palette.success.main,
        ],
      },
    ],
  };

  const positionData = [
    { position: 'BTN', hands: 1200, profit: 450, vpip: 28, pfr: 22 },
    { position: 'CO', hands: 1150, profit: 380, vpip: 26, pfr: 20 },
    { position: 'MP', hands: 1100, profit: 220, vpip: 18, pfr: 14 },
    { position: 'UTG', hands: 1000, profit: 150, vpip: 15, pfr: 12 },
    { position: 'SB', hands: 800, profit: -120, vpip: 35, pfr: 8 },
    { position: 'BB', hands: 850, profit: -180, vpip: 32, pfr: 6 },
  ];

  const chartOptions = {
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
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: theme.palette.text.primary,
        },
      },
    },
  };

  const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, color }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography color="textSecondary" gutterBottom variant="subtitle2">
          {title}
        </Typography>
        <Typography variant="h4" component="div" sx={{ color: color || theme.palette.primary.main }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography color="textSecondary" variant="body2">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Statistics Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select value={timeRange} label="Time Range" onChange={handleTimeRangeChange}>
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
              <MenuItem value="1y">Last year</MenuItem>
              <MenuItem value="all">All time</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Game Type</InputLabel>
            <Select value={gameType} label="Game Type" onChange={handleGameTypeChange}>
              <MenuItem value="all">All Games</MenuItem>
              <MenuItem value="cash">Cash Games</MenuItem>
              <MenuItem value="tournament">Tournaments</MenuItem>
              <MenuItem value="sng">Sit & Go</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Profit"
            value="$2,450"
            subtitle="+15% vs last period"
            color={theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Hands Played"
            value="8,250"
            subtitle="Average: 275/day"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Win Rate"
            value="12.5 BB/100"
            subtitle="Above average"
            color={theme.palette.info.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="ROI"
            value="18.2%"
            subtitle="Tournament ROI"
            color={theme.palette.warning.main}
          />
        </Grid>
      </Grid>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Session Analysis" />
          <Tab label="Position Stats" />
          <Tab label="Hand Strength" />
          <Tab label="Opponent Analysis" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Profit Trend
              </Typography>
              <Box sx={{ height: '85%' }}>
                <Line data={profitChartData} options={chartOptions} />
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Session Metrics
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Average Session Length
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={75}
                  sx={{ mb: 2, height: 8, borderRadius: 4 }}
                />
                <Typography variant="h6">4.2 hours</Typography>

                <Typography variant="body2" gutterBottom sx={{ mt: 3 }}>
                  VPIP
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={23}
                  sx={{ mb: 2, height: 8, borderRadius: 4 }}
                />
                <Typography variant="h6">23%</Typography>

                <Typography variant="body2" gutterBottom sx={{ mt: 3 }}>
                  PFR
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={18}
                  sx={{ mb: 2, height: 8, borderRadius: 4 }}
                />
                <Typography variant="h6">18%</Typography>

                <Typography variant="body2" gutterBottom sx={{ mt: 3 }}>
                  3-Bet %
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={8}
                  sx={{ mb: 2, height: 8, borderRadius: 4 }}
                />
                <Typography variant="h6">8%</Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Position Analysis
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Position</TableCell>
                  <TableCell align="right">Hands</TableCell>
                  <TableCell align="right">Profit</TableCell>
                  <TableCell align="right">VPIP %</TableCell>
                  <TableCell align="right">PFR %</TableCell>
                  <TableCell align="right">BB/100</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {positionData.map((row) => (
                  <TableRow key={row.position}>
                    <TableCell>
                      <Chip label={row.position} size="small" />
                    </TableCell>
                    <TableCell align="right">{row.hands}</TableCell>
                    <TableCell align="right">
                      <Typography
                        color={row.profit > 0 ? 'success.main' : 'error.main'}
                      >
                        ${row.profit}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{row.vpip}%</TableCell>
                    <TableCell align="right">{row.pfr}%</TableCell>
                    <TableCell align="right">
                      {((row.profit / row.hands) * 100).toFixed(1)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Hand Strength Performance
              </Typography>
              <Box sx={{ height: '85%' }}>
                <Bar data={handStrengthChartData} options={chartOptions} />
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Hand Distribution
              </Typography>
              <Box sx={{ height: '85%' }}>
                <Doughnut data={handDistributionData} options={pieOptions} />
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Opponent Types Encountered
              </Typography>
              <Box sx={{ height: '85%' }}>
                <Bar data={opponentCountData} options={chartOptions} />
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Profit vs Opponent Types
              </Typography>
              <Box sx={{ height: '85%' }}>
                <Bar data={opponentProfitData} options={chartOptions} />
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};
