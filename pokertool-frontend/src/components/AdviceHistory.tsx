import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Chip,
  IconButton,
  Collapse,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Paper,
  Divider,
  Tooltip,
  Badge
} from '@mui/material';
import {
  History,
  CheckCircle,
  Cancel,
  ExpandMore,
  ExpandLess,
  Replay,
  FilterList,
  Download,
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Warning,
  Star,
  StarBorder
} from '@mui/icons-material';

interface AdviceEntry {
  id: string;
  timestamp: Date;
  handNumber: number;
  position: string;
  holeCards: string;
  boardCards: string;
  potSize: number;
  adviceGiven: {
    action: 'FOLD' | 'CALL' | 'RAISE' | 'CHECK' | 'ALL-IN';
    amount?: number;
    confidence: number;
    ev: number;
    reasoning: string;
  };
  actionTaken: {
    action: 'FOLD' | 'CALL' | 'RAISE' | 'CHECK' | 'ALL-IN';
    amount?: number;
  };
  outcome: {
    won: boolean;
    amount: number;
    showdown?: boolean;
  };
  mistake?: boolean;
  bigPot?: boolean;
  street: 'PREFLOP' | 'FLOP' | 'TURN' | 'RIVER';
}

interface AdviceHistoryProps {
  maxEntries?: number;
  onReplayHand?: (entry: AdviceEntry) => void;
}

export const AdviceHistory: React.FC<AdviceHistoryProps> = ({ 
  maxEntries = 50,
  onReplayHand 
}) => {
  const [entries, setEntries] = useState<AdviceEntry[]>([]);
  const [filteredEntries, setFilteredEntries] = useState<AdviceEntry[]>([]);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'mistakes' | 'bigpots' | 'followed' | 'ignored'>('all');
  const [selectedEntry, setSelectedEntry] = useState<AdviceEntry | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Generate sample data
  useEffect(() => {
    const sampleEntries: AdviceEntry[] = [
      {
        id: '1',
        timestamp: new Date(Date.now() - 300000),
        handNumber: 142,
        position: 'BTN',
        holeCards: 'A♠K♠',
        boardCards: 'Q♠J♠T♠',
        potSize: 125.50,
        adviceGiven: {
          action: 'RAISE',
          amount: 88,
          confidence: 92,
          ev: 45.25,
          reasoning: 'Nut flush with straight flush draw. Maximum value extraction recommended.'
        },
        actionTaken: {
          action: 'RAISE',
          amount: 88
        },
        outcome: {
          won: true,
          amount: 225.50,
          showdown: true
        },
        mistake: false,
        bigPot: true,
        street: 'FLOP'
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 600000),
        handNumber: 141,
        position: 'CO',
        holeCards: '7♣7♦',
        boardCards: 'A♠K♣Q♥',
        potSize: 45.00,
        adviceGiven: {
          action: 'FOLD',
          confidence: 88,
          ev: -12.50,
          reasoning: 'Low pair on coordinated board. High probability opponent has us beat.'
        },
        actionTaken: {
          action: 'CALL',
          amount: 30
        },
        outcome: {
          won: false,
          amount: -30.00,
          showdown: true
        },
        mistake: true,
        bigPot: false,
        street: 'FLOP'
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 900000),
        handNumber: 140,
        position: 'SB',
        holeCards: 'K♥Q♥',
        boardCards: '',
        potSize: 7.50,
        adviceGiven: {
          action: 'RAISE',
          amount: 10,
          confidence: 75,
          ev: 3.25,
          reasoning: 'Strong broadway cards in position. Standard 3-bet for value and fold equity.'
        },
        actionTaken: {
          action: 'RAISE',
          amount: 10
        },
        outcome: {
          won: true,
          amount: 7.50,
          showdown: false
        },
        mistake: false,
        bigPot: false,
        street: 'PREFLOP'
      },
      {
        id: '4',
        timestamp: new Date(Date.now() - 1200000),
        handNumber: 139,
        position: 'UTG',
        holeCards: 'J♣J♦',
        boardCards: 'A♠K♠Q♠5♣2♥',
        potSize: 185.00,
        adviceGiven: {
          action: 'FOLD',
          confidence: 95,
          ev: -45.00,
          reasoning: 'Board heavily favors opponent range. Multiple made straights and flushes possible.'
        },
        actionTaken: {
          action: 'FOLD'
        },
        outcome: {
          won: false,
          amount: 0,
          showdown: false
        },
        mistake: false,
        bigPot: true,
        street: 'RIVER'
      },
      {
        id: '5',
        timestamp: new Date(Date.now() - 1500000),
        handNumber: 138,
        position: 'MP',
        holeCards: 'A♣K♦',
        boardCards: 'K♠K♣7♥',
        potSize: 65.00,
        adviceGiven: {
          action: 'RAISE',
          amount: 45,
          confidence: 90,
          ev: 28.50,
          reasoning: 'Trip kings with top kicker. Extract maximum value from worse kings and pocket pairs.'
        },
        actionTaken: {
          action: 'CALL',
          amount: 20
        },
        outcome: {
          won: true,
          amount: 85.00,
          showdown: true
        },
        mistake: true,
        bigPot: false,
        street: 'FLOP'
      }
    ];
    setEntries(sampleEntries);
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = [...entries];

    // Apply filter type
    switch (filter) {
      case 'mistakes':
        filtered = filtered.filter(e => e.mistake);
        break;
      case 'bigpots':
        filtered = filtered.filter(e => e.bigPot);
        break;
      case 'followed':
        filtered = filtered.filter(e => 
          e.adviceGiven.action === e.actionTaken.action &&
          (!e.adviceGiven.amount || Math.abs(e.adviceGiven.amount - (e.actionTaken.amount || 0)) < 5)
        );
        break;
      case 'ignored':
        filtered = filtered.filter(e => 
          e.adviceGiven.action !== e.actionTaken.action ||
          (e.adviceGiven.amount && Math.abs(e.adviceGiven.amount - (e.actionTaken.amount || 0)) >= 5)
        );
        break;
    }

    // Apply search term
    if (searchTerm) {
      filtered = filtered.filter(e =>
        e.holeCards.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.position.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.adviceGiven.reasoning.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredEntries(filtered.slice(0, maxEntries));
  }, [entries, filter, searchTerm, maxEntries]);

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const handleReplay = (entry: AdviceEntry) => {
    setSelectedEntry(entry);
    setDetailDialogOpen(true);
    if (onReplayHand) {
      onReplayHand(entry);
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'FOLD': return '#f44336';
      case 'CALL': return '#2196f3';
      case 'RAISE': return '#4caf50';
      case 'CHECK': return '#ff9800';
      case 'ALL-IN': return '#9c27b0';
      default: return '#757575';
    }
  };

  const exportToCSV = () => {
    const headers = ['Time', 'Hand', 'Position', 'Cards', 'Board', 'Advice', 'Action', 'Result', 'P/L'];
    const rows = filteredEntries.map(e => [
      e.timestamp.toLocaleString(),
      e.handNumber,
      e.position,
      e.holeCards,
      e.boardCards || '-',
      `${e.adviceGiven.action}${e.adviceGiven.amount ? ' $' + e.adviceGiven.amount : ''}`,
      `${e.actionTaken.action}${e.actionTaken.amount ? ' $' + e.actionTaken.amount : ''}`,
      e.outcome.won ? 'Won' : 'Lost',
      e.outcome.amount
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `advice-history-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const stats = {
    totalHands: filteredEntries.length,
    mistakes: filteredEntries.filter(e => e.mistake).length,
    followRate: filteredEntries.length > 0 
      ? (filteredEntries.filter(e => e.adviceGiven.action === e.actionTaken.action).length / filteredEntries.length * 100).toFixed(1)
      : '0',
    totalProfit: filteredEntries.reduce((sum, e) => sum + e.outcome.amount, 0)
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <History />
          Advice History
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Download />}
          onClick={exportToCSV}
          size="small"
        >
          Export CSV
        </Button>
      </Box>

      {/* Stats Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
            <Typography variant="body2" color="text.secondary">Total Hands</Typography>
            <Typography variant="h6">{stats.totalHands}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
            <Typography variant="body2" color="text.secondary">Mistakes</Typography>
            <Typography variant="h6" sx={{ color: stats.mistakes > 0 ? '#f44336' : 'inherit' }}>
              {stats.mistakes}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
            <Typography variant="body2" color="text.secondary">Follow Rate</Typography>
            <Typography variant="h6">{stats.followRate}%</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
            <Typography variant="body2" color="text.secondary">Total P/L</Typography>
            <Typography 
              variant="h6" 
              sx={{ color: stats.totalProfit >= 0 ? '#4caf50' : '#f44336' }}
            >
              ${stats.totalProfit.toFixed(2)}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Filters */}
      <Card sx={{ mb: 2, bgcolor: 'background.paper' }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Filter</InputLabel>
              <Select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                label="Filter"
              >
                <MenuItem value="all">All Hands</MenuItem>
                <MenuItem value="mistakes">Mistakes Only</MenuItem>
                <MenuItem value="bigpots">Big Pots Only</MenuItem>
                <MenuItem value="followed">Advice Followed</MenuItem>
                <MenuItem value="ignored">Advice Ignored</MenuItem>
              </Select>
            </FormControl>
            <TextField
              size="small"
              placeholder="Search hands..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              sx={{ minWidth: 200 }}
            />
            <Chip
              label={`${filteredEntries.length} hands shown`}
              size="small"
              color="primary"
            />
          </Box>
        </CardContent>
      </Card>

      {/* History List */}
      <List sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
        {filteredEntries.map((entry, index) => {
          const isExpanded = expandedItems.has(entry.id);
          const adviceFollowed = entry.adviceGiven.action === entry.actionTaken.action;

          return (
            <React.Fragment key={entry.id}>
              {index > 0 && <Divider />}
              <ListItem>
                <ListItemIcon>
                  {entry.mistake ? (
                    <Warning sx={{ color: '#f44336' }} />
                  ) : adviceFollowed ? (
                    <CheckCircle sx={{ color: '#4caf50' }} />
                  ) : (
                    <Cancel sx={{ color: '#ff9800' }} />
                  )}
                </ListItemIcon>
                
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        Hand #{entry.handNumber}
                      </Typography>
                      <Chip 
                        label={entry.position} 
                        size="small" 
                        variant="outlined" 
                      />
                      <Typography variant="body2" color="text.secondary">
                        {entry.holeCards}
                      </Typography>
                      {entry.boardCards && (
                        <Typography variant="body2" color="text.secondary">
                          | {entry.boardCards}
                        </Typography>
                      )}
                      {entry.bigPot && (
                        <Chip 
                          label="BIG POT" 
                          size="small" 
                          color="warning"
                          icon={<AttachMoney />}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Chip
                          label={`Advised: ${entry.adviceGiven.action}${entry.adviceGiven.amount ? ' $' + entry.adviceGiven.amount : ''}`}
                          size="small"
                          sx={{ 
                            bgcolor: getActionColor(entry.adviceGiven.action) + '20',
                            color: getActionColor(entry.adviceGiven.action)
                          }}
                        />
                        <Typography variant="body2">→</Typography>
                        <Chip
                          label={`Played: ${entry.actionTaken.action}${entry.actionTaken.amount ? ' $' + entry.actionTaken.amount : ''}`}
                          size="small"
                          sx={{ 
                            bgcolor: getActionColor(entry.actionTaken.action) + '20',
                            color: getActionColor(entry.actionTaken.action)
                          }}
                        />
                        <Chip
                          label={entry.outcome.won ? `Won $${entry.outcome.amount.toFixed(2)}` : `Lost $${Math.abs(entry.outcome.amount).toFixed(2)}`}
                          size="small"
                          color={entry.outcome.won ? 'success' : 'error'}
                          variant="outlined"
                          icon={entry.outcome.won ? <TrendingUp /> : <TrendingDown />}
                        />
                      </Box>
                      
                      <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                        <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                          <Typography variant="body2" paragraph>
                            <strong>Reasoning:</strong> {entry.adviceGiven.reasoning}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 2 }}>
                            <Chip 
                              label={`Confidence: ${entry.adviceGiven.confidence}%`} 
                              size="small" 
                              variant="outlined"
                            />
                            <Chip 
                              label={`EV: ${entry.adviceGiven.ev >= 0 ? '+' : ''}$${entry.adviceGiven.ev.toFixed(2)}`} 
                              size="small" 
                              variant="outlined"
                              color={entry.adviceGiven.ev >= 0 ? 'success' : 'error'}
                            />
                            <Chip 
                              label={`Pot: $${entry.potSize.toFixed(2)}`} 
                              size="small" 
                              variant="outlined"
                            />
                            <Chip 
                              label={entry.street} 
                              size="small" 
                              variant="outlined"
                            />
                          </Box>
                          
                          {entry.mistake && (
                            <Paper sx={{ mt: 2, p: 1, bgcolor: 'rgba(244, 67, 54, 0.1)' }}>
                              <Typography variant="caption" sx={{ color: '#f44336' }}>
                                ⚠️ Not following advice cost ${Math.abs(entry.outcome.amount - (entry.adviceGiven.ev || 0)).toFixed(2)} in EV
                              </Typography>
                            </Paper>
                          )}
                        </Box>
                      </Collapse>
                      
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        {new Date(entry.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  }
                />
                
                <ListItemSecondaryAction>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <IconButton size="small" onClick={() => handleReplay(entry)}>
                      <Tooltip title="Replay hand details">
                        <Replay />
                      </Tooltip>
                    </IconButton>
                    <IconButton size="small" onClick={() => toggleExpanded(entry.id)}>
                      {isExpanded ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Box>
                </ListItemSecondaryAction>
              </ListItem>
            </React.Fragment>
          );
        })}
        
        {filteredEntries.length === 0 && (
          <ListItem>
            <ListItemText
              primary="No hands found"
              secondary="Adjust your filters or play more hands to see history"
              sx={{ textAlign: 'center', py: 4 }}
            />
          </ListItem>
        )}
      </List>

      {/* Hand Detail Dialog */}
      <Dialog 
        open={detailDialogOpen} 
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedEntry && (
          <>
            <DialogTitle>
              Hand #{selectedEntry.handNumber} - Detailed Replay
            </DialogTitle>
            <DialogContent dividers>
              <Box sx={{ display: 'grid', gap: 2 }}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Hand Information</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Position</Typography>
                      <Typography>{selectedEntry.position}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Street</Typography>
                      <Typography>{selectedEntry.street}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Hole Cards</Typography>
                      <Typography variant="h6">{selectedEntry.holeCards}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Board</Typography>
                      <Typography variant="h6">{selectedEntry.boardCards || 'Preflop'}</Typography>
                    </Grid>
                  </Grid>
                </Paper>

                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Advice Analysis</Typography>
                  <Typography paragraph>{selectedEntry.adviceGiven.reasoning}</Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Chip label={`Confidence: ${selectedEntry.adviceGiven.confidence}%`} />
                    <Chip 
                      label={`EV: $${selectedEntry.adviceGiven.ev.toFixed(2)}`}
                      color={selectedEntry.adviceGiven.ev >= 0 ? 'success' : 'error'}
                    />
                    <Chip label={`Pot: $${selectedEntry.potSize.toFixed(2)}`} />
                  </Box>
                </Paper>

                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Decision & Outcome</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Advised Action</Typography>
                      <Chip 
                        label={`${selectedEntry.adviceGiven.action}${selectedEntry.adviceGiven.amount ? ' $' + selectedEntry.adviceGiven.amount : ''}`}
                        sx={{ 
                          bgcolor: getActionColor(selectedEntry.adviceGiven.action) + '20',
                          color: getActionColor(selectedEntry.adviceGiven.action)
                        }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Actual Action</Typography>
                      <Chip 
                        label={`${selectedEntry.actionTaken.action}${selectedEntry.actionTaken.amount ? ' $' + selectedEntry.actionTaken.amount : ''}`}
                        sx={{ 
                          bgcolor: getActionColor(selectedEntry.actionTaken.action) + '20',
                          color: getActionColor(selectedEntry.actionTaken.action)
                        }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Result</Typography>
                      <Typography 
                        variant="h5" 
                        sx={{ color: selectedEntry.outcome.won ? '#4caf50' : '#f44336' }}
                      >
                        {selectedEntry.outcome.won ? 'Won' : 'Lost'} ${Math.abs(selectedEntry.outcome.amount).toFixed(2)}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

// Add missing Grid import
import { Grid } from '@mui/material';

export default AdviceHistory;
