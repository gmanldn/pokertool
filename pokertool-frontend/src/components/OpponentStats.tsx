import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Box,
  Chip,
  IconButton,
  Collapse,
  Tooltip,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
} from '@mui/material';
import {
  ExpandMore,
  ExpandLess,
  TrendingUp,
  TrendingDown,
  Info,
  Warning,
  Person,
} from '@mui/icons-material';

// Types for opponent statistics
interface OpponentStat {
  playerId: string;
  playerName: string;
  position?: string;
  handsPlayed: number;
  vpip: number; // Voluntary Put In Pot %
  pfr: number; // Pre-Flop Raise %
  threeBet: number; // 3-bet %
  aggression: number; // Aggression Factor
  foldToCbet: number; // Fold to continuation bet %
  foldToThreeBet: number; // Fold to 3-bet %
  wtsd: number; // Went to Showdown %
  wonAtShowdown: number; // Won at Showdown %
  totalWinnings: number;
  lastSeen: Date;
  recentHands: HandHistory[];
}

interface HandHistory {
  handId: string;
  action: string;
  result: 'won' | 'lost' | 'folded';
  potSize: number;
  timestamp: Date;
}

type PlayerStyle = 'TAG' | 'LAG' | 'Nit' | 'Fish' | 'Unknown';

interface OpponentStatsProps {
  opponents: OpponentStat[];
  currentHeroPosition?: string;
}

export const OpponentStats: React.FC<OpponentStatsProps> = ({
  opponents,
  currentHeroPosition,
}) => {
  const [expandedPlayer, setExpandedPlayer] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'stats' | 'history'>('stats');

  // Classify player style based on stats
  const classifyPlayerStyle = (stat: OpponentStat): PlayerStyle => {
    const { vpip, pfr, aggression, handsPlayed } = stat;
    
    if (handsPlayed < 20) return 'Unknown';
    
    // Classification logic based on common poker player types
    if (vpip < 15 && pfr < 12) return 'Nit'; // Very tight
    if (vpip > 40 || (vpip > 30 && pfr < 10)) return 'Fish'; // Loose passive
    if (vpip < 25 && pfr > 15 && Math.abs(vpip - pfr) < 7) return 'TAG'; // Tight aggressive
    if (vpip > 25 && pfr > 20) return 'LAG'; // Loose aggressive
    
    return 'Unknown';
  };

  // Get color for player style
  const getStyleColor = (style: PlayerStyle): string => {
    switch (style) {
      case 'TAG': return 'success';
      case 'LAG': return 'warning';
      case 'Nit': return 'info';
      case 'Fish': return 'error';
      default: return 'default';
    }
  };

  // Get recommendations based on opponent tendencies
  const getRecommendations = (stat: OpponentStat): string[] => {
    const recommendations: string[] = [];
    const style = classifyPlayerStyle(stat);

    // Style-based recommendations
    switch (style) {
      case 'Nit':
        recommendations.push('Steal blinds aggressively - folds often pre-flop');
        recommendations.push('Respect their raises - likely has strong hands');
        break;
      case 'Fish':
        recommendations.push('Value bet more frequently - calls with weak hands');
        recommendations.push('Avoid bluffing - unlikely to fold');
        break;
      case 'TAG':
        recommendations.push('Mix up your play - competent opponent');
        recommendations.push('Look for timing tells and bet sizing patterns');
        break;
      case 'LAG':
        recommendations.push('Tighten up range - will apply pressure');
        recommendations.push('Call down lighter - may be bluffing frequently');
        break;
    }

    // Specific stat-based recommendations
    if (stat.foldToThreeBet > 70 && stat.handsPlayed > 30) {
      recommendations.push(`3-bet more often - folds ${stat.foldToThreeBet.toFixed(0)}% to 3-bets`);
    }
    if (stat.foldToCbet > 60 && stat.handsPlayed > 30) {
      recommendations.push(`C-bet frequently - folds ${stat.foldToCbet.toFixed(0)}% to c-bets`);
    }
    if (stat.wtsd < 20 && stat.handsPlayed > 50) {
      recommendations.push('Bluff more on later streets - rarely goes to showdown');
    }
    if (stat.aggression < 1 && stat.handsPlayed > 30) {
      recommendations.push('Value bet thin - passive player, unlikely to raise');
    }

    return recommendations;
  };

  // Get color for stat value (red/yellow/green based on exploitability)
  const getStatColor = (value: number, statType: string): string => {
    switch (statType) {
      case 'vpip':
        if (value < 15) return '#2196F3'; // Nit (blue)
        if (value < 25) return '#4CAF50'; // TAG (green)
        if (value < 35) return '#FF9800'; // LAG (orange)
        return '#F44336'; // Fish (red)
      case 'pfr':
        if (value < 10) return '#2196F3';
        if (value < 20) return '#4CAF50';
        if (value < 30) return '#FF9800';
        return '#F44336';
      case 'aggression':
        if (value < 1) return '#2196F3'; // Passive
        if (value < 2.5) return '#4CAF50'; // Balanced
        return '#FF9800'; // Aggressive
      default:
        return '#757575';
    }
  };

  const toggleExpanded = (playerId: string) => {
    setExpandedPlayer(expandedPlayer === playerId ? null : playerId);
  };

  if (!opponents || opponents.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography color="textSecondary" align="center">
            No opponent data available yet. Play more hands to gather statistics.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Grid container spacing={2}>
      {opponents.map((opponent) => {
        const playerStyle = classifyPlayerStyle(opponent);
        const recommendations = getRecommendations(opponent);
        const isExpanded = expandedPlayer === opponent.playerId;
        const sampleSizeWarning = opponent.handsPlayed < 30;

        return (
          <Grid item xs={12} md={6} key={opponent.playerId}>
            <Card elevation={3}>
              <CardHeader
                avatar={
                  <Avatar sx={{ bgcolor: getStatColor(opponent.vpip, 'vpip') }}>
                    <Person />
                  </Avatar>
                }
                title={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h6">{opponent.playerName}</Typography>
                    <Chip
                      label={playerStyle}
                      color={getStyleColor(playerStyle) as any}
                      size="small"
                    />
                    {opponent.position && (
                      <Chip label={opponent.position} size="small" variant="outlined" />
                    )}
                  </Box>
                }
                subheader={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="caption" color="textSecondary">
                      {opponent.handsPlayed} hands
                    </Typography>
                    {sampleSizeWarning && (
                      <Tooltip title="Small sample size - stats may not be reliable">
                        <Warning fontSize="small" color="warning" />
                      </Tooltip>
                    )}
                  </Box>
                }
                action={
                  <IconButton onClick={() => toggleExpanded(opponent.playerId)}>
                    {isExpanded ? <ExpandLess /> : <ExpandMore />}
                  </IconButton>
                }
              />
              
              <CardContent>
                {/* Main Stats Grid */}
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="caption" color="textSecondary">
                        VPIP
                      </Typography>
                      <Typography
                        variant="h5"
                        style={{ color: getStatColor(opponent.vpip, 'vpip') }}
                      >
                        {opponent.vpip.toFixed(0)}%
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="caption" color="textSecondary">
                        PFR
                      </Typography>
                      <Typography
                        variant="h5"
                        style={{ color: getStatColor(opponent.pfr, 'pfr') }}
                      >
                        {opponent.pfr.toFixed(0)}%
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="caption" color="textSecondary">
                        3-Bet
                      </Typography>
                      <Typography variant="h5">
                        {opponent.threeBet.toFixed(0)}%
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Secondary Stats */}
                <Box mt={2}>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="textSecondary">
                        Aggression Factor
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(opponent.aggression * 25, 100)}
                        sx={{ height: 6, borderRadius: 3, mt: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="textSecondary">
                        Fold to C-Bet: {opponent.foldToCbet.toFixed(0)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={opponent.foldToCbet}
                        sx={{ height: 6, borderRadius: 3, mt: 0.5 }}
                        color={opponent.foldToCbet > 60 ? 'warning' : 'primary'}
                      />
                    </Grid>
                  </Grid>
                </Box>

                {/* Recommendations */}
                {recommendations.length > 0 && !isExpanded && (
                  <Box mt={2} p={1} bgcolor="background.default" borderRadius={1}>
                    <Typography variant="caption" color="primary" fontWeight="bold">
                      💡 {recommendations[0]}
                    </Typography>
                  </Box>
                )}

                {/* Expanded Content */}
                <Collapse in={isExpanded}>
                  <Box mt={2}>
                    <Divider sx={{ my: 2 }} />
                    
                    {/* Additional Stats */}
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="textSecondary">
                          Fold to 3-Bet
                        </Typography>
                        <Typography variant="body1">
                          {opponent.foldToThreeBet.toFixed(0)}%
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="textSecondary">
                          WTSD
                        </Typography>
                        <Typography variant="body1">
                          {opponent.wtsd.toFixed(0)}%
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="textSecondary">
                          Won at Showdown
                        </Typography>
                        <Typography variant="body1">
                          {opponent.wonAtShowdown.toFixed(0)}%
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="textSecondary">
                          Total Winnings
                        </Typography>
                        <Typography
                          variant="body1"
                          color={opponent.totalWinnings >= 0 ? 'success.main' : 'error.main'}
                        >
                          ${Math.abs(opponent.totalWinnings).toFixed(2)}
                          {opponent.totalWinnings >= 0 ? (
                            <TrendingUp fontSize="small" />
                          ) : (
                            <TrendingDown fontSize="small" />
                          )}
                        </Typography>
                      </Grid>
                    </Grid>

                    {/* All Recommendations */}
                    {recommendations.length > 0 && (
                      <>
                        <Typography variant="subtitle2" gutterBottom>
                          Exploitation Recommendations
                        </Typography>
                        <List dense>
                          {recommendations.map((rec, index) => (
                            <ListItem key={index}>
                              <ListItemAvatar>
                                <Info color="primary" fontSize="small" />
                              </ListItemAvatar>
                              <ListItemText primary={rec} />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}

                    {/* Recent Hands */}
                    {opponent.recentHands && opponent.recentHands.length > 0 && (
                      <>
                        <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                          Recent Hands vs This Opponent
                        </Typography>
                        <List dense>
                          {opponent.recentHands.slice(0, 3).map((hand) => (
                            <ListItem key={hand.handId}>
                              <ListItemText
                                primary={`${hand.action} - Pot: $${hand.potSize.toFixed(2)}`}
                                secondary={
                                  <Chip
                                    label={hand.result}
                                    size="small"
                                    color={
                                      hand.result === 'won'
                                        ? 'success'
                                        : hand.result === 'lost'
                                        ? 'error'
                                        : 'default'
                                    }
                                  />
                                }
                              />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}
                  </Box>
                </Collapse>
              </CardContent>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );
};

export default OpponentStats;
