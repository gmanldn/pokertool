/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/TournamentView.tsx
version: v79.0.0
last_commit: '2025-10-15T06:04:00+01:00'
fixes:
- date: '2025-10-15'
  summary: Full implementation of tournament tracking with statistics and bankroll integration
---
POKERTOOL-HEADER-END */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  EmojiEvents,
  Add,
  Delete,
  PlayArrow,
  CheckCircle,
  FilterList,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { useAppSelector, useAppDispatch } from '../store';
import {
  registerTournament,
  startTournament,
  completeTournament,
  deleteTournament,
  setStructureFilter,
  selectFilteredTournaments,
  Tournament,
  TournamentStatus,
  TournamentStructure,
} from '../store/slices/tournamentSlice';
import { recordBuyin, recordCashout } from '../store/slices/bankrollSlice';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export const TournamentView: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const dispatch = useAppDispatch();
  const tournamentState = useAppSelector((state) => state.tournament);
  const filteredTournaments = useAppSelector(selectFilteredTournaments);
  const bankroll = useAppSelector((state) => state.bankroll);

  const [registerDialog, setRegisterDialog] = useState(false);
  const [completeDialog, setCompleteDialog] = useState(false);
  const [selectedTournament, setSelectedTournament] = useState<Tournament | null>(null);
  const [tabValue, setTabValue] = useState(0);

  // Registration form state
  const [name, setName] = useState('');
  const [buyin, setBuyin] = useState('');
  const [rebuy, setRebuy] = useState('0');
  const [addon, setAddon] = useState('0');
  const [totalEntrants, setTotalEntrants] = useState('');
  const [structure, setStructure] = useState<TournamentStructure>('freezeout');
  const [notes, setNotes] = useState('');

  // Completion form state
  const [position, setPosition] = useState('');
  const [prize, setPrize] = useState('');
  const [finalEntrants, setFinalEntrants] = useState('');

  const handleRegisterTournament = () => {
    const buyinNum = parseFloat(buyin);
    const rebuyNum = parseFloat(rebuy);
    const addonNum = parseFloat(addon);
    const entrantsNum = parseInt(totalEntrants);

    if (isNaN(buyinNum) || buyinNum <= 0 || !name) {
      return;
    }

    dispatch(registerTournament({
      name,
      buyin: buyinNum,
      rebuy: rebuyNum || 0,
      addon: addonNum || 0,
      totalEntrants: entrantsNum || 0,
      structure,
      startTime: Date.now(),
      position: null,
      notes: notes || '',
    }));

    // Record buyin in bankroll
    dispatch(recordBuyin({ 
      amount: buyinNum + (rebuyNum || 0) + (addonNum || 0), 
      description: `Tournament: ${name}` 
    }));

    // Reset form
    setName('');
    setBuyin('');
    setRebuy('0');
    setAddon('0');
    setTotalEntrants('');
    setNotes('');
    setRegisterDialog(false);
  };

  const handleCompleteTournament = () => {
    if (!selectedTournament) return;

    const positionNum = parseInt(position);
    const prizeNum = parseFloat(prize);
    const entrantsNum = parseInt(finalEntrants);

    if (isNaN(positionNum) || isNaN(prizeNum)) {
      return;
    }

    dispatch(completeTournament({
      id: selectedTournament.id,
      position: positionNum,
      prize: prizeNum,
      totalEntrants: entrantsNum || selectedTournament.totalEntrants,
    }));

    // Record cashout in bankroll if prize > 0
    if (prizeNum > 0) {
      dispatch(recordCashout({ 
        amount: prizeNum, 
        description: `Tournament win: ${selectedTournament.name}` 
      }));
    }

    setPosition('');
    setPrize('');
    setFinalEntrants('');
    setSelectedTournament(null);
    setCompleteDialog(false);
  };

  const handleDeleteTournament = (id: string) => {
    dispatch(deleteTournament(id));
  };

  const formatCurrency = (value: number) => {
    return `${bankroll.currency} ${value.toFixed(2)}`;
  };

  const getStatusColor = (status: TournamentStatus) => {
    switch (status) {
      case 'registered':
        return 'info';
      case 'active':
        return 'warning';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  // Chart data for tournament results over time
  const resultsChartData = useMemo(() => {
    const completed = filteredTournaments
      .filter(t => t.status === 'completed')
      .sort((a, b) => a.startTime - b.startTime);

    let runningTotal = 0;
    const data = completed.map((t) => {
      const profit = t.prize - t.totalInvestment;
      runningTotal += profit;
      return runningTotal;
    });

    return {
      labels: completed.map((t, i) => `T${i + 1}`),
      datasets: [
        {
          label: 'Cumulative Profit',
          data: data,
          borderColor: theme.palette.primary.main,
          backgroundColor: theme.palette.mode === 'dark' 
            ? 'rgba(76, 175, 80, 0.1)' 
            : 'rgba(46, 125, 50, 0.1)',
          fill: true,
          tension: 0.4,
        },
      ],
    };
  }, [filteredTournaments, theme]);

  // Doughnut chart for ITM vs non-ITM
  const itmChartData = useMemo(() => {
    const completed = filteredTournaments.filter(t => t.status === 'completed');
    const itm = completed.filter(t => t.prize > 0).length;
    const nonItm = completed.length - itm;

    return {
      labels: ['In The Money', 'No Cash'],
      datasets: [
        {
          data: [itm, nonItm],
          backgroundColor: [
            theme.palette.success.main,
            theme.palette.error.main,
          ],
        },
      ],
    };
  }, [filteredTournaments, theme]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: !isMobile,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `${bankroll.currency} ${context.parsed.y.toFixed(2)}`;
          },
        },
      },
    },
  };

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Typography variant={isMobile ? 'h5' : 'h4'} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmojiEvents />
          Tournament Tracker
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setRegisterDialog(true)}
          size={isMobile ? 'small' : 'medium'}
        >
          Register
        </Button>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Tournaments
              </Typography>
              <Typography variant={isMobile ? 'h5' : 'h4'}>
                {tournamentState.stats.totalTournaments}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {tournamentState.stats.activeTournaments} active
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Profit
              </Typography>
              <Typography 
                variant={isMobile ? 'h5' : 'h4'}
                color={tournamentState.stats.totalProfit >= 0 ? 'success.main' : 'error.main'}
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                {tournamentState.stats.totalProfit >= 0 ? <TrendingUp /> : <TrendingDown />}
                {formatCurrency(tournamentState.stats.totalProfit)}
              </Typography>
              <Typography variant="caption" color={tournamentState.stats.roi >= 0 ? 'success.main' : 'error.main'}>
                ROI: {tournamentState.stats.roi.toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                ITM Rate
              </Typography>
              <Typography variant={isMobile ? 'h5' : 'h4'}>
                {tournamentState.stats.itm.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {tournamentState.stats.completedTournaments} completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Best Finish
              </Typography>
              <Typography variant={isMobile ? 'h5' : 'h4'}>
                {tournamentState.stats.bestFinish ? `#${tournamentState.stats.bestFinish}` : 'N/A'}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Biggest: {formatCurrency(tournamentState.stats.biggestCash)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      {tournamentState.stats.completedTournaments > 0 && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Cumulative Profit
              </Typography>
              <Box sx={{ height: isMobile ? 250 : 300 }}>
                <Line data={resultsChartData} options={chartOptions} />
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                ITM Distribution
              </Typography>
              <Box sx={{ height: isMobile ? 250 : 300 }}>
                <Doughnut data={itmChartData} />
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Filters and Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 2 }}>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab label="All" />
            <Tab label="Active" />
            <Tab label="Completed" />
          </Tabs>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <FilterList fontSize="small" />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select
                value={tournamentState.filters.structure}
                onChange={(e) => dispatch(setStructureFilter(e.target.value as TournamentStructure | 'all'))}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="freezeout">Freezeout</MenuItem>
                <MenuItem value="rebuy">Rebuy</MenuItem>
                <MenuItem value="knockout">Knockout</MenuItem>
                <MenuItem value="turbo">Turbo</MenuItem>
                <MenuItem value="hyper-turbo">Hyper Turbo</MenuItem>
                <MenuItem value="satellite">Satellite</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>
      </Paper>

      {/* Tournament List */}
      <Paper>
        <TableContainer>
          <Table size={isMobile ? 'small' : 'medium'}>
            <TableHead>
              <TableRow>
                <TableCell>Tournament</TableCell>
                {!isMobile && <TableCell>Structure</TableCell>}
                <TableCell>Buy-in</TableCell>
                <TableCell align="right">Investment</TableCell>
                <TableCell align="right">Prize</TableCell>
                <TableCell align="right">Profit</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredTournaments
                .filter(t => {
                  if (tabValue === 1) return t.status === 'active' || t.status === 'registered';
                  if (tabValue === 2) return t.status === 'completed';
                  return true;
                })
                .sort((a, b) => b.startTime - a.startTime)
                .map((tournament) => (
                  <TableRow key={tournament.id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {tournament.name}
                      </Typography>
                      {!isMobile && tournament.position && (
                        <Typography variant="caption" color="textSecondary">
                          #{tournament.position} / {tournament.totalEntrants}
                        </Typography>
                      )}
                    </TableCell>
                    {!isMobile && (
                      <TableCell>
                        <Chip label={tournament.structure} size="small" variant="outlined" />
                      </TableCell>
                    )}
                    <TableCell>{formatCurrency(tournament.buyin)}</TableCell>
                    <TableCell align="right">{formatCurrency(tournament.totalInvestment)}</TableCell>
                    <TableCell align="right">{formatCurrency(tournament.prize)}</TableCell>
                    <TableCell 
                      align="right"
                      sx={{ 
                        color: (tournament.prize - tournament.totalInvestment) >= 0 
                          ? 'success.main' 
                          : 'error.main' 
                      }}
                    >
                      {formatCurrency(tournament.prize - tournament.totalInvestment)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={tournament.status}
                        color={getStatusColor(tournament.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                        {tournament.status === 'registered' && (
                          <IconButton
                            size="small"
                            onClick={() => dispatch(startTournament(tournament.id))}
                            color="primary"
                          >
                            <PlayArrow fontSize="small" />
                          </IconButton>
                        )}
                        {tournament.status === 'active' && (
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedTournament(tournament);
                              setCompleteDialog(true);
                            }}
                            color="success"
                          >
                            <CheckCircle fontSize="small" />
                          </IconButton>
                        )}
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteTournament(tournament.id)}
                          color="error"
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        {filteredTournaments.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="textSecondary">
              No tournaments found. Register your first tournament to get started.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setRegisterDialog(true)}
              sx={{ mt: 2 }}
            >
              Register Tournament
            </Button>
          </Box>
        )}
      </Paper>

      {/* Register Tournament Dialog */}
      <Dialog 
        open={registerDialog} 
        onClose={() => setRegisterDialog(false)}
        maxWidth="sm"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>Register Tournament</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Tournament Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
              required
            />
            <FormControl fullWidth>
              <InputLabel>Structure</InputLabel>
              <Select
                value={structure}
                label="Structure"
                onChange={(e) => setStructure(e.target.value as TournamentStructure)}
              >
                <MenuItem value="freezeout">Freezeout</MenuItem>
                <MenuItem value="rebuy">Rebuy</MenuItem>
                <MenuItem value="knockout">Knockout</MenuItem>
                <MenuItem value="turbo">Turbo</MenuItem>
                <MenuItem value="hyper-turbo">Hyper Turbo</MenuItem>
                <MenuItem value="satellite">Satellite</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Buy-in"
              type="number"
              value={buyin}
              onChange={(e) => setBuyin(e.target.value)}
              fullWidth
              required
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              label="Rebuy Amount"
              type="number"
              value={rebuy}
              onChange={(e) => setRebuy(e.target.value)}
              fullWidth
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              label="Add-on Amount"
              type="number"
              value={addon}
              onChange={(e) => setAddon(e.target.value)}
              fullWidth
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              label="Total Entrants (if known)"
              type="number"
              value={totalEntrants}
              onChange={(e) => setTotalEntrants(e.target.value)}
              fullWidth
              inputProps={{ min: 0, step: 1 }}
            />
            <TextField
              label="Notes (Optional)"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              fullWidth
              multiline
              rows={2}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRegisterDialog(false)}>Cancel</Button>
          <Button onClick={handleRegisterTournament} variant="contained">
            Register
          </Button>
        </DialogActions>
      </Dialog>

      {/* Complete Tournament Dialog */}
      <Dialog 
        open={completeDialog} 
        onClose={() => setCompleteDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Complete Tournament</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Final Position"
              type="number"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              fullWidth
              required
              inputProps={{ min: 1, step: 1 }}
            />
            <TextField
              label="Prize Amount"
              type="number"
              value={prize}
              onChange={(e) => setPrize(e.target.value)}
              fullWidth
              required
              inputProps={{ min: 0, step: 0.01 }}
              helperText="Enter 0 if no prize won"
            />
            <TextField
              label="Total Entrants"
              type="number"
              value={finalEntrants}
              onChange={(e) => setFinalEntrants(e.target.value)}
              fullWidth
              inputProps={{ min: 1, step: 1 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompleteDialog(false)}>Cancel</Button>
          <Button onClick={handleCompleteTournament} variant="contained" color="success">
            Complete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
