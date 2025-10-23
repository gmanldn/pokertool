/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/AutopilotControl.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+00:00'
fixes:
- date: '2025-10-23'
  summary: Initial implementation of Autopilot control panel for automated gameplay
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Button,
  Chip,
  Grid,
  Card,
  CardContent,
  Alert,
  Divider,
  LinearProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Settings,
  Speed,
  TrendingUp,
  AccountBalance,
  Psychology,
  Timeline,
} from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';
import { buildWsUrl } from '../config/api';
import { SendMessageFunction } from '../types/common';

interface AutopilotControlProps {
  sendMessage: SendMessageFunction;
}

type Strategy = 'tight-aggressive' | 'loose-aggressive' | 'balanced' | 'conservative';
type RiskLevel = 'low' | 'medium' | 'high' | 'very-high';

interface AutopilotState {
  isActive: boolean;
  strategy: Strategy;
  riskTolerance: RiskLevel;
  autoReload: boolean;
  stopLoss: number;
  winGoal: number;
  handsPlayed: number;
  currentProfit: number;
  winRate: number;
}

interface AutopilotStats {
  handsPlayed: number;
  handsWon: number;
  totalProfit: number;
  bigBlindsWon: number;
  vpip: number;
  pfr: number;
  aggression: number;
  sessionDuration: number;
}

export const AutopilotControl: React.FC<AutopilotControlProps> = ({ sendMessage }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { messages } = useWebSocket(buildWsUrl());

  const [autopilotState, setAutopilotState] = useState<AutopilotState>({
    isActive: false,
    strategy: 'balanced',
    riskTolerance: 'medium',
    autoReload: true,
    stopLoss: 100,
    winGoal: 200,
    handsPlayed: 0,
    currentProfit: 0,
    winRate: 0,
  });

  const [stats, setStats] = useState<AutopilotStats>({
    handsPlayed: 0,
    handsWon: 0,
    totalProfit: 0,
    bigBlindsWon: 0,
    vpip: 0,
    pfr: 0,
    aggression: 0,
    sessionDuration: 0,
  });

  // Listen for autopilot updates from backend
  useEffect(() => {
    if (messages && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];

      if (latestMessage.type === 'autopilot_state_update' && latestMessage.data) {
        const data = latestMessage.data as Record<string, unknown>;
        setAutopilotState(prev => ({
          ...prev,
          isActive: typeof data.isActive === 'boolean' ? data.isActive : prev.isActive,
          handsPlayed: typeof data.handsPlayed === 'number' ? data.handsPlayed : prev.handsPlayed,
          currentProfit: typeof data.currentProfit === 'number' ? data.currentProfit : prev.currentProfit,
          winRate: typeof data.winRate === 'number' ? data.winRate : prev.winRate,
        }));
      }

      if (latestMessage.type === 'autopilot_stats_update' && latestMessage.data) {
        const data = latestMessage.data as Record<string, unknown>;
        setStats(prev => ({
          ...prev,
          handsPlayed: typeof data.handsPlayed === 'number' ? data.handsPlayed : prev.handsPlayed,
          handsWon: typeof data.handsWon === 'number' ? data.handsWon : prev.handsWon,
          totalProfit: typeof data.totalProfit === 'number' ? data.totalProfit : prev.totalProfit,
          bigBlindsWon: typeof data.bigBlindsWon === 'number' ? data.bigBlindsWon : prev.bigBlindsWon,
          vpip: typeof data.vpip === 'number' ? data.vpip : prev.vpip,
          pfr: typeof data.pfr === 'number' ? data.pfr : prev.pfr,
          aggression: typeof data.aggression === 'number' ? data.aggression : prev.aggression,
          sessionDuration: typeof data.sessionDuration === 'number' ? data.sessionDuration : prev.sessionDuration,
        }));
      }
    }
  }, [messages]);

  const handleToggleAutopilot = () => {
    const newState = !autopilotState.isActive;
    setAutopilotState(prev => ({ ...prev, isActive: newState }));

    sendMessage({
      type: newState ? 'start_autopilot' : 'stop_autopilot',
      data: {
        strategy: autopilotState.strategy,
        riskTolerance: autopilotState.riskTolerance,
        stopLoss: autopilotState.stopLoss,
        winGoal: autopilotState.winGoal,
        autoReload: autopilotState.autoReload,
      },
    });
  };

  const handleStrategyChange = (strategy: Strategy) => {
    setAutopilotState(prev => ({ ...prev, strategy }));
    if (autopilotState.isActive) {
      sendMessage({
        type: 'update_autopilot_settings',
        data: { strategy },
      });
    }
  };

  const handleRiskChange = (riskTolerance: RiskLevel) => {
    setAutopilotState(prev => ({ ...prev, riskTolerance }));
    if (autopilotState.isActive) {
      sendMessage({
        type: 'update_autopilot_settings',
        data: { riskTolerance },
      });
    }
  };

  const getStrategyDescription = (strategy: Strategy): string => {
    const descriptions = {
      'tight-aggressive': 'Play premium hands aggressively. Best for conservative play with high win rate.',
      'loose-aggressive': 'Play many hands aggressively. High variance, requires larger bankroll.',
      'balanced': 'Mix of tight and loose play. Adapts to table dynamics and opponents.',
      'conservative': 'Very selective hand choice. Minimize risk, focus on value.',
    };
    return descriptions[strategy];
  };

  const getRiskColor = (risk: RiskLevel): string => {
    const colors = {
      low: theme.palette.success.main,
      medium: theme.palette.warning.main,
      high: theme.palette.error.main,
      'very-high': theme.palette.error.dark,
    };
    return colors[risk];
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Psychology sx={{ fontSize: 40, color: theme.palette.primary.main }} />
          <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight="bold">
            Autopilot Control
          </Typography>
        </Box>
        <Chip
          label={autopilotState.isActive ? 'ACTIVE' : 'STANDBY'}
          color={autopilotState.isActive ? 'success' : 'default'}
          icon={autopilotState.isActive ? <PlayArrow /> : <Stop />}
          sx={{ px: 2, py: 2.5, fontSize: '1rem', fontWeight: 'bold' }}
        />
      </Box>

      {/* Warning Alert */}
      {!autopilotState.isActive && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <strong>Important:</strong> Autopilot mode will make automated decisions based on your strategy settings.
          Always monitor your session and ensure stop-loss limits are set appropriately.
        </Alert>
      )}

      {autopilotState.isActive && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Autopilot is active with {autopilotState.strategy} strategy.
          Playing hand {autopilotState.handsPlayed} • Profit: ${autopilotState.currentProfit.toFixed(2)}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Control Panel */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={3}>
              <Settings color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Autopilot Settings
              </Typography>
            </Box>

            {/* Master Control */}
            <Box mb={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={autopilotState.isActive}
                    onChange={handleToggleAutopilot}
                    color="primary"
                    size="medium"
                  />
                }
                label={
                  <Typography variant="h6" fontWeight="bold">
                    {autopilotState.isActive ? 'Disable Autopilot' : 'Enable Autopilot'}
                  </Typography>
                }
              />
              {autopilotState.isActive && (
                <LinearProgress sx={{ mt: 1 }} />
              )}
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Strategy Selection */}
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Playing Strategy</InputLabel>
              <Select
                value={autopilotState.strategy}
                label="Playing Strategy"
                onChange={(e) => handleStrategyChange(e.target.value as Strategy)}
                disabled={autopilotState.isActive}
              >
                <MenuItem value="tight-aggressive">
                  <Box>
                    <Typography>Tight-Aggressive (TAG)</Typography>
                    <Typography variant="caption" color="textSecondary">
                      Premium hands only, aggressive play
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="loose-aggressive">
                  <Box>
                    <Typography>Loose-Aggressive (LAG)</Typography>
                    <Typography variant="caption" color="textSecondary">
                      Play many hands, high aggression
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="balanced">
                  <Box>
                    <Typography>Balanced (GTO-Based)</Typography>
                    <Typography variant="caption" color="textSecondary">
                      Adaptive strategy, balanced ranges
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="conservative">
                  <Box>
                    <Typography>Conservative</Typography>
                    <Typography variant="caption" color="textSecondary">
                      Risk-averse, value-focused
                    </Typography>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info" icon={<Speed />} sx={{ mb: 3 }}>
              {getStrategyDescription(autopilotState.strategy)}
            </Alert>

            {/* Risk Tolerance */}
            <Box mb={3}>
              <Typography gutterBottom fontWeight="bold">
                Risk Tolerance
              </Typography>
              <Box sx={{ px: 2 }}>
                <Slider
                  value={
                    autopilotState.riskTolerance === 'low' ? 0 :
                    autopilotState.riskTolerance === 'medium' ? 1 :
                    autopilotState.riskTolerance === 'high' ? 2 : 3
                  }
                  onChange={(_, value) => {
                    const risks: RiskLevel[] = ['low', 'medium', 'high', 'very-high'];
                    handleRiskChange(risks[value as number]);
                  }}
                  min={0}
                  max={3}
                  step={1}
                  marks={[
                    { value: 0, label: 'Low' },
                    { value: 1, label: 'Medium' },
                    { value: 2, label: 'High' },
                    { value: 3, label: 'Very High' },
                  ]}
                  disabled={autopilotState.isActive}
                  sx={{
                    '& .MuiSlider-markLabel': {
                      fontSize: '0.75rem',
                    },
                  }}
                />
              </Box>
              <Chip
                label={autopilotState.riskTolerance.toUpperCase()}
                size="small"
                sx={{
                  backgroundColor: getRiskColor(autopilotState.riskTolerance),
                  color: '#fff',
                  fontWeight: 'bold',
                }}
              />
            </Box>

            {/* Stop Loss */}
            <Box mb={3}>
              <Typography gutterBottom fontWeight="bold">
                Stop Loss: ${autopilotState.stopLoss}
              </Typography>
              <Slider
                value={autopilotState.stopLoss}
                onChange={(_, value) => setAutopilotState(prev => ({ ...prev, stopLoss: value as number }))}
                min={0}
                max={500}
                step={10}
                valueLabelDisplay="auto"
                disabled={autopilotState.isActive}
              />
            </Box>

            {/* Win Goal */}
            <Box mb={3}>
              <Typography gutterBottom fontWeight="bold">
                Win Goal: ${autopilotState.winGoal}
              </Typography>
              <Slider
                value={autopilotState.winGoal}
                onChange={(_, value) => setAutopilotState(prev => ({ ...prev, winGoal: value as number }))}
                min={0}
                max={1000}
                step={25}
                valueLabelDisplay="auto"
                disabled={autopilotState.isActive}
              />
            </Box>

            {/* Auto Reload */}
            <FormControlLabel
              control={
                <Switch
                  checked={autopilotState.autoReload}
                  onChange={(e) => setAutopilotState(prev => ({ ...prev, autoReload: e.target.checked }))}
                  disabled={autopilotState.isActive}
                />
              }
              label="Auto-reload stack when below minimum"
            />
          </Paper>
        </Grid>

        {/* Statistics Panel */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={3}>
              <Timeline color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Session Statistics
              </Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="caption" color="textSecondary">
                      Hands Played
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {stats.handsPlayed}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="caption" color="textSecondary">
                      Hands Won
                    </Typography>
                    <Typography variant="h4" fontWeight="bold" color="success.main">
                      {stats.handsWon}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="caption" color="textSecondary">
                      Total Profit
                    </Typography>
                    <Typography
                      variant="h4"
                      fontWeight="bold"
                      color={stats.totalProfit >= 0 ? 'success.main' : 'error.main'}
                    >
                      ${stats.totalProfit.toFixed(2)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="caption" color="textSecondary">
                      BB/100 Hands
                    </Typography>
                    <Typography
                      variant="h4"
                      fontWeight="bold"
                      color={stats.bigBlindsWon >= 0 ? 'success.main' : 'error.main'}
                    >
                      {stats.bigBlindsWon.toFixed(1)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={3}>
              <TrendingUp color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Playing Style Metrics
              </Typography>
            </Box>

            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2">VPIP (Voluntarily Put In Pot)</Typography>
                <Typography variant="body2" fontWeight="bold">{stats.vpip}%</Typography>
              </Box>
              <LinearProgress variant="determinate" value={stats.vpip} />
            </Box>

            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2">PFR (Pre-Flop Raise)</Typography>
                <Typography variant="body2" fontWeight="bold">{stats.pfr}%</Typography>
              </Box>
              <LinearProgress variant="determinate" value={stats.pfr} color="secondary" />
            </Box>

            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2">Aggression Factor</Typography>
                <Typography variant="body2" fontWeight="bold">{stats.aggression.toFixed(2)}</Typography>
              </Box>
              <LinearProgress variant="determinate" value={Math.min(stats.aggression * 20, 100)} color="warning" />
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box display="flex" alignItems="center" gap={1}>
                <AccountBalance color="action" />
                <Typography variant="body2" color="textSecondary">
                  Session Duration
                </Typography>
              </Box>
              <Typography variant="h6" fontWeight="bold">
                {formatTime(stats.sessionDuration)}
              </Typography>
            </Box>
          </Paper>

          {/* Emergency Stop */}
          {autopilotState.isActive && (
            <Button
              variant="contained"
              color="error"
              fullWidth
              size="large"
              startIcon={<Stop />}
              onClick={handleToggleAutopilot}
              sx={{ mt: 2, py: 1.5 }}
            >
              EMERGENCY STOP
            </Button>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};
