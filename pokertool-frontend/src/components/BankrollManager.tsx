/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/BankrollManager.tsx
version: v79.0.0
last_commit: '2025-10-15T05:54:00+01:00'
fixes:
- date: '2025-10-15'
  summary: Full implementation of bankroll management with charts and transaction tracking
---
POKERTOOL-HEADER-END */

import React, { useState, useMemo } from 'react';
import { LazyLineChart } from './charts';
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
  Alert,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Add,
  Delete,
  Settings as SettingsIcon,
  Assessment,
  ShowChart,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../store';
import {
  initializeBankroll,
  addDeposit,
  addWithdrawal,
  recordWin,
  recordLoss,
  recordBuyin,
  recordCashout,
  updateLimits,
  setCurrency,
  deleteTransaction,
  selectProfitLoss,
  selectProfitLossPercentage,
  selectStakeRecommendations,
  Transaction,
} from '../store/slices/bankrollSlice';

// Register ChartJS components

export const BankrollManager: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const dispatch = useAppDispatch();
  const bankroll = useAppSelector((state) => state.bankroll);
  const profitLoss = useAppSelector(selectProfitLoss);
  const profitLossPercentage = useAppSelector(selectProfitLossPercentage);
  const stakeRecommendations = useAppSelector(selectStakeRecommendations);

  const [addTransactionDialog, setAddTransactionDialog] = useState(false);
  const [settingsDialog, setSettingsDialog] = useState(false);
  const [transactionType, setTransactionType] = useState<Transaction['type']>('deposit');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');

  // Settings state
  const [stopLossAmount, setStopLossAmount] = useState(bankroll.limits.stopLossAmount?.toString() || '');
  const [stopLossPercentage, setStopLossPercentage] = useState(bankroll.limits.stopLossPercentage?.toString() || '');
  const [dailyLossLimit, setDailyLossLimit] = useState(bankroll.limits.dailyLossLimit?.toString() || '');
  const [sessionLossLimit, setSessionLossLimit] = useState(bankroll.limits.sessionLossLimit?.toString() || '');
  const [currencyValue, setCurrencyValue] = useState(bankroll.currency);

  // Chart data
  const chartData = useMemo(() => {
    const sortedTransactions = [...bankroll.transactions].sort((a, b) => a.timestamp - b.timestamp);
    
    return {
      labels: sortedTransactions.map((t) => 
        new Date(t.timestamp).toLocaleDateString(undefined, { 
          month: 'short', 
          day: 'numeric',
          hour: isMobile ? undefined : '2-digit',
          minute: isMobile ? undefined : '2-digit',
        })
      ),
      datasets: [
        {
          label: 'Bankroll',
          data: sortedTransactions.map((t) => t.balance),
          borderColor: theme.palette.primary.main,
          backgroundColor: theme.palette.mode === 'dark' 
            ? 'rgba(76, 175, 80, 0.1)' 
            : 'rgba(46, 125, 50, 0.1)',
          fill: true,
          tension: 0.4,
        },
      ],
    };
  }, [bankroll.transactions, theme, isMobile]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: { parsed: { y: number | null } }) => {
            const value = context.parsed.y ?? 0;
            return `${bankroll.currency} ${value.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: (value: string | number) => `${bankroll.currency} ${value}`,
        },
      },
      x: {
        ticks: {
          maxRotation: isMobile ? 45 : 0,
          minRotation: isMobile ? 45 : 0,
        },
      },
    },
  };

  const handleAddTransaction = () => {
    const amountNum = parseFloat(amount);
    if (isNaN(amountNum) || amountNum <= 0) {
      return;
    }

    const payload = { amount: amountNum, description: description || undefined };

    switch (transactionType) {
      case 'deposit':
        if (bankroll.currentBalance === 0 && bankroll.transactions.length === 0) {
          dispatch(initializeBankroll({ amount: amountNum, currency: currencyValue }));
        } else {
          dispatch(addDeposit(payload));
        }
        break;
      case 'withdrawal':
        dispatch(addWithdrawal(payload));
        break;
      case 'win':
        dispatch(recordWin(payload));
        break;
      case 'loss':
        dispatch(recordLoss(payload));
        break;
      case 'buyin':
        dispatch(recordBuyin(payload));
        break;
      case 'cashout':
        dispatch(recordCashout(payload));
        break;
    }

    setAmount('');
    setDescription('');
    setAddTransactionDialog(false);
  };

  const handleSaveSettings = () => {
    dispatch(updateLimits({
      stopLossAmount: stopLossAmount ? parseFloat(stopLossAmount) : null,
      stopLossPercentage: stopLossPercentage ? parseFloat(stopLossPercentage) : null,
      dailyLossLimit: dailyLossLimit ? parseFloat(dailyLossLimit) : null,
      sessionLossLimit: sessionLossLimit ? parseFloat(sessionLossLimit) : null,
    }));
    dispatch(setCurrency(currencyValue));
    setSettingsDialog(false);
  };

  const handleDeleteTransaction = (id: string) => {
    dispatch(deleteTransaction(id));
  };

  const formatCurrency = (value: number) => {
    return `${bankroll.currency} ${value.toFixed(2)}`;
  };

  const getTransactionIcon = (type: Transaction['type']) => {
    switch (type) {
      case 'deposit':
      case 'win':
      case 'cashout':
        return <TrendingUp color="success" />;
      case 'withdrawal':
      case 'loss':
      case 'buyin':
        return <TrendingDown color="error" />;
    }
  };

  const getTransactionColor = (type: Transaction['type']) => {
    switch (type) {
      case 'deposit':
      case 'win':
      case 'cashout':
        return 'success';
      case 'withdrawal':
      case 'loss':
      case 'buyin':
        return 'error';
      default:
        return 'default';
    }
  };

  // Check if limits are being approached
  const checkLimits = () => {
    const alerts = [];
    
    if (bankroll.limits.stopLossAmount && profitLoss <= -bankroll.limits.stopLossAmount) {
      alerts.push('Stop loss amount limit reached!');
    }
    
    if (bankroll.limits.stopLossPercentage && profitLossPercentage <= -bankroll.limits.stopLossPercentage) {
      alerts.push('Stop loss percentage limit reached!');
    }

    return alerts;
  };

  const limitAlerts = checkLimits();

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Typography variant={isMobile ? 'h5' : 'h4'} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccountBalance />
          Bankroll Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setSettingsDialog(true)}
            size={isMobile ? 'small' : 'medium'}
          >
            Settings
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setAddTransactionDialog(true)}
            size={isMobile ? 'small' : 'medium'}
          >
            Transaction
          </Button>
        </Box>
      </Box>

      {/* Alerts */}
      {limitAlerts.map((alert, index) => (
        <Alert severity="error" sx={{ mb: 2 }} key={index}>
          {alert}
        </Alert>
      ))}

      {/* Overview Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Current Balance
              </Typography>
              <Typography variant={isMobile ? 'h5' : 'h4'}>
                {formatCurrency(bankroll.currentBalance)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Profit/Loss
              </Typography>
              <Typography 
                variant={isMobile ? 'h5' : 'h4'}
                color={profitLoss >= 0 ? 'success.main' : 'error.main'}
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                {profitLoss >= 0 ? <TrendingUp /> : <TrendingDown />}
                {formatCurrency(profitLoss)}
              </Typography>
              <Typography variant="caption" color={profitLoss >= 0 ? 'success.main' : 'error.main'}>
                {profitLossPercentage >= 0 ? '+' : ''}{profitLossPercentage.toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Peak Balance
              </Typography>
              <Typography variant={isMobile ? 'h5' : 'h4'}>
                {formatCurrency(bankroll.peakBalance)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Lowest Balance
              </Typography>
              <Typography variant={isMobile ? 'h5' : 'h4'}>
                {formatCurrency(bankroll.lowestBalance)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Chart */}
      {bankroll.transactions.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ShowChart />
            Bankroll History
          </Typography>
          <Box sx={{ height: isMobile ? 250 : 400 }}>
            <LazyLineChart data={chartData} options={chartOptions} />
          </Box>
        </Paper>
      )}

      {/* Stake Recommendations */}
      {bankroll.currentBalance > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assessment />
            Recommended Stakes
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Conservative (1-2%)
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {formatCurrency(stakeRecommendations.conservative.min)} - {formatCurrency(stakeRecommendations.conservative.max)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Moderate (2-5%)
                  </Typography>
                  <Typography variant="h6" color="warning.main">
                    {formatCurrency(stakeRecommendations.moderate.min)} - {formatCurrency(stakeRecommendations.moderate.max)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Aggressive (5-10%)
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {formatCurrency(stakeRecommendations.aggressive.min)} - {formatCurrency(stakeRecommendations.aggressive.max)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Transaction History */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Transaction History
        </Typography>
        {bankroll.transactions.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="textSecondary">
              No transactions yet. Add your first transaction to get started.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setAddTransactionDialog(true)}
              sx={{ mt: 2 }}
            >
              Add Initial Deposit
            </Button>
          </Box>
        ) : (
          <TableContainer>
            <Table size={isMobile ? 'small' : 'medium'}>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Type</TableCell>
                  {!isMobile && <TableCell>Description</TableCell>}
                  <TableCell align="right">Amount</TableCell>
                  <TableCell align="right">Balance</TableCell>
                  <TableCell align="center">Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[...bankroll.transactions].reverse().map((transaction) => (
                  <TableRow key={transaction.id}>
                    <TableCell>
                      {new Date(transaction.timestamp).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getTransactionIcon(transaction.type)}
                        label={transaction.type.toUpperCase()}
                        color={getTransactionColor(transaction.type)}
                        size="small"
                      />
                    </TableCell>
                    {!isMobile && <TableCell>{transaction.description}</TableCell>}
                    <TableCell 
                      align="right"
                      sx={{ 
                        color: ['deposit', 'win', 'cashout'].includes(transaction.type) 
                          ? 'success.main' 
                          : 'error.main' 
                      }}
                    >
                      {['deposit', 'win', 'cashout'].includes(transaction.type) ? '+' : '-'}
                      {formatCurrency(transaction.amount)}
                    </TableCell>
                    <TableCell align="right">{formatCurrency(transaction.balance)}</TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteTransaction(transaction.id)}
                        color="error"
                      >
                        <Delete fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Add Transaction Dialog */}
      <Dialog 
        open={addTransactionDialog} 
        onClose={() => setAddTransactionDialog(false)}
        maxWidth="sm"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>Add Transaction</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Transaction Type</InputLabel>
              <Select
                value={transactionType}
                label="Transaction Type"
                onChange={(e) => setTransactionType(e.target.value as Transaction['type'])}
              >
                <MenuItem value="deposit">Deposit</MenuItem>
                <MenuItem value="withdrawal">Withdrawal</MenuItem>
                <MenuItem value="win">Win</MenuItem>
                <MenuItem value="loss">Loss</MenuItem>
                <MenuItem value="buyin">Table Buy-in</MenuItem>
                <MenuItem value="cashout">Table Cashout</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Amount"
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              fullWidth
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              label="Description (Optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddTransactionDialog(false)}>Cancel</Button>
          <Button onClick={handleAddTransaction} variant="contained">
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog 
        open={settingsDialog} 
        onClose={() => setSettingsDialog(false)}
        maxWidth="sm"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>Bankroll Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Currency</InputLabel>
              <Select
                value={currencyValue}
                label="Currency"
                onChange={(e) => setCurrencyValue(e.target.value)}
              >
                <MenuItem value="USD">USD ($)</MenuItem>
                <MenuItem value="EUR">EUR (€)</MenuItem>
                <MenuItem value="GBP">GBP (£)</MenuItem>
                <MenuItem value="CAD">CAD ($)</MenuItem>
                <MenuItem value="AUD">AUD ($)</MenuItem>
              </Select>
            </FormControl>
            <Divider />
            <Typography variant="subtitle2" color="textSecondary">
              Risk Management Limits
            </Typography>
            <TextField
              label="Stop Loss Amount"
              type="number"
              value={stopLossAmount}
              onChange={(e) => setStopLossAmount(e.target.value)}
              fullWidth
              helperText="Maximum amount you're willing to lose"
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              label="Stop Loss Percentage"
              type="number"
              value={stopLossPercentage}
              onChange={(e) => setStopLossPercentage(e.target.value)}
              fullWidth
              helperText="Maximum percentage loss from starting balance"
              inputProps={{ min: 0, max: 100, step: 1 }}
            />
            <TextField
              label="Daily Loss Limit"
              type="number"
              value={dailyLossLimit}
              onChange={(e) => setDailyLossLimit(e.target.value)}
              fullWidth
              helperText="Maximum loss allowed per day"
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              label="Session Loss Limit"
              type="number"
              value={sessionLossLimit}
              onChange={(e) => setSessionLossLimit(e.target.value)}
              fullWidth
              helperText="Maximum loss allowed per session"
              inputProps={{ min: 0, step: 0.01 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveSettings} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
