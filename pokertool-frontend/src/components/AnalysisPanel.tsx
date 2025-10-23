/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/AnalysisPanel.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+00:00'
fixes:
- date: '2025-10-23'
  summary: Initial implementation of Analysis panel for hand and range analysis
---
POKERTOOL-HEADER-END */

import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
  Divider,
  Tabs,
  Tab,
  Alert,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Calculate,
  Psychology,
  Casino,
  Timeline,
  Assessment,
  EmojiObjects,
} from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';
import { buildWsUrl } from '../config/api';
import { SendMessageFunction } from '../types/common';

interface AnalysisPanelProps {
  sendMessage: SendMessageFunction;
}

type Position = 'UTG' | 'UTG+1' | 'MP' | 'MP+1' | 'CO' | 'BTN' | 'SB' | 'BB';
type Street = 'preflop' | 'flop' | 'turn' | 'river';
type BoardTexture = 'dry' | 'wet' | 'dynamic' | 'static';

interface HandAnalysis {
  handStrength: number;
  equity: number;
  outs: number;
  potOdds: number;
  impliedOdds: number;
  recommendation: string;
  reasoning: string[];
}

interface RangeAnalysis {
  totalCombos: number;
  pairCombos: number;
  suitedCombos: number;
  offSuitCombos: number;
  vpipPercent: number;
  pfrPercent: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ sendMessage }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { messages } = useWebSocket(buildWsUrl());

  const [tabValue, setTabValue] = useState(0);

  // Hand Analysis State
  const [holeCards, setHoleCards] = useState<string>('');
  const [boardCards, setBoardCards] = useState<string>('');
  const [potSize, setPotSize] = useState<number>(100);
  const [betSize, setBetSize] = useState<number>(50);
  const [position, setPosition] = useState<Position>('BTN');
  const [street, setStreet] = useState<Street>('flop');
  const [numOpponents, setNumOpponents] = useState<number>(1);

  // Range Analysis State
  const [rangeInput, setRangeInput] = useState<string>('');
  const [selectedPosition, setSelectedPosition] = useState<Position>('BTN');

  // Analysis Results
  const [handAnalysis, setHandAnalysis] = useState<HandAnalysis | null>(null);
  const [rangeAnalysis, setRangeAnalysis] = useState<RangeAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Listen for analysis results from backend
  React.useEffect(() => {
    if (messages && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];

      if (latestMessage.type === 'hand_analysis_result' && latestMessage.data) {
        const data = latestMessage.data as Record<string, unknown>;
        setHandAnalysis({
          handStrength: typeof data.handStrength === 'number' ? data.handStrength : 0,
          equity: typeof data.equity === 'number' ? data.equity : 0,
          outs: typeof data.outs === 'number' ? data.outs : 0,
          potOdds: typeof data.potOdds === 'number' ? data.potOdds : 0,
          impliedOdds: typeof data.impliedOdds === 'number' ? data.impliedOdds : 0,
          recommendation: typeof data.recommendation === 'string' ? data.recommendation : '',
          reasoning: Array.isArray(data.reasoning) ? data.reasoning.filter((r): r is string => typeof r === 'string') : [],
        });
        setIsAnalyzing(false);
      }

      if (latestMessage.type === 'range_analysis_result' && latestMessage.data) {
        const data = latestMessage.data as Record<string, unknown>;
        setRangeAnalysis({
          totalCombos: typeof data.totalCombos === 'number' ? data.totalCombos : 0,
          pairCombos: typeof data.pairCombos === 'number' ? data.pairCombos : 0,
          suitedCombos: typeof data.suitedCombos === 'number' ? data.suitedCombos : 0,
          offSuitCombos: typeof data.offSuitCombos === 'number' ? data.offSuitCombos : 0,
          vpipPercent: typeof data.vpipPercent === 'number' ? data.vpipPercent : 0,
          pfrPercent: typeof data.pfrPercent === 'number' ? data.pfrPercent : 0,
        });
        setIsAnalyzing(false);
      }
    }
  }, [messages]);

  const handleAnalyzeHand = useCallback(() => {
    setIsAnalyzing(true);
    sendMessage({
      type: 'analyze_hand',
      data: {
        holeCards,
        boardCards,
        potSize,
        betSize,
        position,
        street,
        numOpponents,
      },
    });

    // Mock analysis for demo (remove when backend is ready)
    setTimeout(() => {
      const mockEquity = 45 + Math.random() * 40;
      const mockOuts = Math.floor(Math.random() * 15);
      const calculatedPotOdds = (betSize / (potSize + betSize)) * 100;

      setHandAnalysis({
        handStrength: mockEquity,
        equity: mockEquity,
        outs: mockOuts,
        potOdds: calculatedPotOdds,
        impliedOdds: calculatedPotOdds * 1.5,
        recommendation: mockEquity > 60 ? 'RAISE' : mockEquity > 40 ? 'CALL' : 'FOLD',
        reasoning: [
          `Your hand has approximately ${mockEquity.toFixed(1)}% equity`,
          `You have ~${mockOuts} outs to improve`,
          `Pot odds: ${calculatedPotOdds.toFixed(1)}%`,
          mockEquity > calculatedPotOdds ? 'You have the right odds to call' : 'Insufficient equity to call profitably',
        ],
      });
      setIsAnalyzing(false);
    }, 1000);
  }, [holeCards, boardCards, potSize, betSize, position, street, numOpponents, sendMessage]);

  const handleAnalyzeRange = useCallback(() => {
    setIsAnalyzing(true);
    sendMessage({
      type: 'analyze_range',
      data: {
        range: rangeInput,
        position: selectedPosition,
      },
    });

    // Mock analysis for demo (remove when backend is ready)
    setTimeout(() => {
      const totalHands = rangeInput.split(',').length * 4; // Rough estimate
      setRangeAnalysis({
        totalCombos: totalHands,
        pairCombos: Math.floor(totalHands * 0.2),
        suitedCombos: Math.floor(totalHands * 0.3),
        offSuitCombos: Math.floor(totalHands * 0.5),
        vpipPercent: (totalHands / 1326) * 100,
        pfrPercent: (totalHands / 1326) * 100 * 0.8,
      });
      setIsAnalyzing(false);
    }, 800);
  }, [rangeInput, selectedPosition, sendMessage]);

  const getPositionColor = (pos: Position): string => {
    if (pos === 'UTG' || pos === 'UTG+1') return theme.palette.error.main;
    if (pos === 'MP' || pos === 'MP+1') return theme.palette.warning.main;
    if (pos === 'CO' || pos === 'BTN') return theme.palette.success.main;
    return theme.palette.info.main;
  };

  const getRecommendationColor = (rec: string): string => {
    if (rec === 'RAISE') return theme.palette.success.main;
    if (rec === 'CALL') return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  // Pre-defined ranges for common positions
  const defaultRanges = useMemo(() => ({
    UTG: 'AA,KK,QQ,JJ,TT,99,AKs,AQs,AJs',
    'UTG+1': 'AA,KK,QQ,JJ,TT,99,88,AKs,AQs,AJs,ATs,KQs',
    MP: 'AA,KK,QQ,JJ,TT,99,88,77,AKs,AKo,AQs,AJs,ATs,KQs,KJs',
    'MP+1': 'AA,KK,QQ,JJ,TT,99,88,77,66,AKs,AKo,AQs,AQo,AJs,ATs,KQs,KJs,KTs,QJs',
    CO: 'AA,KK,QQ,JJ,TT,99,88,77,66,55,AKs,AKo,AQs,AQo,AJs,AJo,ATs,KQs,KQo,KJs,KTs,QJs,QTs,JTs',
    BTN: 'AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,KQs,KQo,KJs,KJo,KTs,QJs,QJo,QTs,JTs,J9s,T9s,98s,87s,76s,65s',
    SB: 'AA,KK,QQ,JJ,TT,99,88,77,66,AKs,AKo,AQs,AQo,AJs,ATs,KQs,KJs,QJs',
    BB: 'AA,KK,QQ,JJ,TT,99,88,77,66,55,AKs,AKo,AQs,AQo,AJs,ATs,A9s,KQs,KJs,KTs,QJs,QTs,JTs',
  }), []);

  const loadDefaultRange = useCallback(() => {
    setRangeInput(defaultRanges[selectedPosition]);
  }, [selectedPosition, defaultRanges]);

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Calculate sx={{ fontSize: 40, color: theme.palette.primary.main }} />
          <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight="bold">
            Analysis Panel
          </Typography>
        </Box>
        <Chip
          label="HIGH PRIORITY"
          color="error"
          sx={{ px: 2, py: 2.5, fontSize: '0.9rem', fontWeight: 'bold' }}
        />
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Analyze hands, ranges, and board textures to make optimal decisions.
      </Alert>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant={isMobile ? 'fullWidth' : 'standard'}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<Casino />} label="Hand Analysis" />
          <Tab icon={<Assessment />} label="Range Analysis" />
          <Tab icon={<Timeline />} label="Board Texture" />
          <Tab icon={<EmojiObjects />} label="Recommendations" />
        </Tabs>

        {/* Hand Analysis Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Hand Input
                </Typography>

                <TextField
                  fullWidth
                  label="Hole Cards"
                  placeholder="e.g., AhKd"
                  value={holeCards}
                  onChange={(e) => setHoleCards(e.target.value)}
                  sx={{ mb: 2 }}
                  helperText="Enter your hole cards (e.g., AhKd, QsJs)"
                />

                <TextField
                  fullWidth
                  label="Board Cards"
                  placeholder="e.g., Kh9d3c"
                  value={boardCards}
                  onChange={(e) => setBoardCards(e.target.value)}
                  sx={{ mb: 2 }}
                  helperText="Enter board cards (e.g., Kh9d3c)"
                />

                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Pot Size"
                      value={potSize}
                      onChange={(e) => setPotSize(Number(e.target.value))}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Bet Size"
                      value={betSize}
                      onChange={(e) => setBetSize(Number(e.target.value))}
                    />
                  </Grid>
                </Grid>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Position</InputLabel>
                  <Select
                    value={position}
                    label="Position"
                    onChange={(e) => setPosition(e.target.value as Position)}
                  >
                    <MenuItem value="UTG">UTG (Under the Gun)</MenuItem>
                    <MenuItem value="UTG+1">UTG+1</MenuItem>
                    <MenuItem value="MP">MP (Middle Position)</MenuItem>
                    <MenuItem value="MP+1">MP+1</MenuItem>
                    <MenuItem value="CO">CO (Cutoff)</MenuItem>
                    <MenuItem value="BTN">BTN (Button)</MenuItem>
                    <MenuItem value="SB">SB (Small Blind)</MenuItem>
                    <MenuItem value="BB">BB (Big Blind)</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Street</InputLabel>
                  <Select
                    value={street}
                    label="Street"
                    onChange={(e) => setStreet(e.target.value as Street)}
                  >
                    <MenuItem value="preflop">Pre-flop</MenuItem>
                    <MenuItem value="flop">Flop</MenuItem>
                    <MenuItem value="turn">Turn</MenuItem>
                    <MenuItem value="river">River</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  type="number"
                  label="Number of Opponents"
                  value={numOpponents}
                  onChange={(e) => setNumOpponents(Number(e.target.value))}
                  sx={{ mb: 2 }}
                  inputProps={{ min: 1, max: 9 }}
                />

                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  startIcon={<Calculate />}
                  onClick={handleAnalyzeHand}
                  disabled={isAnalyzing || !holeCards}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Hand'}
                </Button>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              {handAnalysis ? (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom fontWeight="bold">
                    Analysis Results
                  </Typography>

                  <Box sx={{ mb: 3 }}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography>Hand Strength</Typography>
                      <Typography fontWeight="bold">{handAnalysis.handStrength.toFixed(1)}%</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={handAnalysis.handStrength}
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                  </Box>

                  <Card variant="outlined" sx={{ mb: 2, bgcolor: `${getRecommendationColor(handAnalysis.recommendation)}15` }}>
                    <CardContent>
                      <Typography variant="h4" textAlign="center" fontWeight="bold" color={getRecommendationColor(handAnalysis.recommendation)}>
                        {handAnalysis.recommendation}
                      </Typography>
                    </CardContent>
                  </Card>

                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="textSecondary">Equity</Typography>
                          <Typography variant="h5" fontWeight="bold">{handAnalysis.equity.toFixed(1)}%</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="textSecondary">Outs</Typography>
                          <Typography variant="h5" fontWeight="bold">{handAnalysis.outs}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="textSecondary">Pot Odds</Typography>
                          <Typography variant="h5" fontWeight="bold">{handAnalysis.potOdds.toFixed(1)}%</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="textSecondary">Implied Odds</Typography>
                          <Typography variant="h5" fontWeight="bold">{handAnalysis.impliedOdds.toFixed(1)}%</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                    Reasoning:
                  </Typography>
                  {handAnalysis.reasoning.map((reason, index) => (
                    <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                      • {reason}
                    </Typography>
                  ))}
                </Paper>
              ) : (
                <Paper sx={{ p: 3, textAlign: 'center', minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Box>
                    <Psychology sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary">
                      Enter hand details and click "Analyze Hand"
                    </Typography>
                  </Box>
                </Paper>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Range Analysis Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Range Input
                </Typography>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Position</InputLabel>
                  <Select
                    value={selectedPosition}
                    label="Position"
                    onChange={(e) => setSelectedPosition(e.target.value as Position)}
                  >
                    <MenuItem value="UTG">UTG</MenuItem>
                    <MenuItem value="UTG+1">UTG+1</MenuItem>
                    <MenuItem value="MP">MP</MenuItem>
                    <MenuItem value="MP+1">MP+1</MenuItem>
                    <MenuItem value="CO">CO</MenuItem>
                    <MenuItem value="BTN">BTN</MenuItem>
                    <MenuItem value="SB">SB</MenuItem>
                    <MenuItem value="BB">BB</MenuItem>
                  </Select>
                </FormControl>

                <Button
                  fullWidth
                  variant="outlined"
                  onClick={loadDefaultRange}
                  sx={{ mb: 2 }}
                >
                  Load Default {selectedPosition} Range
                </Button>

                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  label="Range"
                  placeholder="e.g., AA,KK,QQ,AKs,AKo"
                  value={rangeInput}
                  onChange={(e) => setRangeInput(e.target.value)}
                  sx={{ mb: 2 }}
                  helperText="Enter hands separated by commas (e.g., AA,KK,AKs)"
                />

                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  startIcon={<Assessment />}
                  onClick={handleAnalyzeRange}
                  disabled={isAnalyzing || !rangeInput}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Range'}
                </Button>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              {rangeAnalysis ? (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom fontWeight="bold">
                    Range Statistics
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Card variant="outlined" sx={{ bgcolor: `${getPositionColor(selectedPosition)}15` }}>
                        <CardContent>
                          <Typography variant="caption" color="textSecondary">Total Combinations</Typography>
                          <Typography variant="h3" fontWeight="bold" color={getPositionColor(selectedPosition)}>
                            {rangeAnalysis.totalCombos}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>

                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ py: 1.5 }}>
                          <Typography variant="caption" color="textSecondary">Pairs</Typography>
                          <Typography variant="h6" fontWeight="bold">{rangeAnalysis.pairCombos}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ py: 1.5 }}>
                          <Typography variant="caption" color="textSecondary">Suited</Typography>
                          <Typography variant="h6" fontWeight="bold">{rangeAnalysis.suitedCombos}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ py: 1.5 }}>
                          <Typography variant="caption" color="textSecondary">Off-suit</Typography>
                          <Typography variant="h6" fontWeight="bold">{rangeAnalysis.offSuitCombos}</Typography>
                        </CardContent>
                      </Card>
                    </Grid>

                    <Grid item xs={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="textSecondary">VPIP %</Typography>
                          <Typography variant="h5" fontWeight="bold">{rangeAnalysis.vpipPercent.toFixed(1)}%</Typography>
                          <LinearProgress variant="determinate" value={rangeAnalysis.vpipPercent} sx={{ mt: 1 }} />
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="textSecondary">PFR %</Typography>
                          <Typography variant="h5" fontWeight="bold">{rangeAnalysis.pfrPercent.toFixed(1)}%</Typography>
                          <LinearProgress variant="determinate" value={rangeAnalysis.pfrPercent} sx={{ mt: 1 }} color="secondary" />
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>

                  <Divider sx={{ my: 3 }} />

                  <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                    Position: {selectedPosition}
                  </Typography>
                  <Chip
                    label={selectedPosition}
                    sx={{
                      bgcolor: getPositionColor(selectedPosition),
                      color: '#fff',
                      fontWeight: 'bold',
                    }}
                  />
                </Paper>
              ) : (
                <Paper sx={{ p: 3, textAlign: 'center', minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Box>
                    <Assessment sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary">
                      Enter a range and click "Analyze Range"
                    </Typography>
                  </Box>
                </Paper>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Board Texture Tab */}
        <TabPanel value={tabValue} index={2}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              Board Texture Analysis
            </Typography>
            <Alert severity="info">
              Board texture analysis coming soon. This will analyze whether the board is dry, wet, dynamic, or static.
            </Alert>
          </Paper>
        </TabPanel>

        {/* Recommendations Tab */}
        <TabPanel value={tabValue} index={3}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              Strategy Recommendations
            </Typography>
            <Alert severity="info">
              Strategy recommendations based on GTO principles coming soon.
            </Alert>
          </Paper>
        </TabPanel>
      </Paper>
    </Box>
  );
};
