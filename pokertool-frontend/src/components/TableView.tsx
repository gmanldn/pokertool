/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/TableView.tsx
version: v28.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
---
POKERTOOL-HEADER-END */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  LinearProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Refresh,
  Fullscreen,
  Casino,
  FiberManualRecord,
} from '@mui/icons-material';
import { AdvicePanel } from './AdvicePanel';
import { DecisionTimer } from './DecisionTimer';
import { HandStrengthMeter } from './HandStrengthMeter';
import { EquityCalculator } from './EquityCalculator';
import { BetSizingRecommendations } from './BetSizingRecommendations';
import { useWebSocket } from '../hooks/useWebSocket';

interface TableViewProps {
  sendMessage: (message: any) => void;
}

interface TableData {
  tableId: string;
  tableName: string;
  players: Player[];
  pot: number;
  communityCards: string[];
  currentAction: string;
  isActive: boolean;
}

interface Player {
  seat: number;
  name: string;
  chips: number;
  cards?: string[];
  isActive: boolean;
  isFolded: boolean;
}

export const TableView: React.FC<TableViewProps> = ({ sendMessage }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // WebSocket connection for real-time advice
  const { messages } = useWebSocket('http://localhost:8000');
  
  // State for tables - will be populated by backend detection
  const [tables, setTables] = useState<TableData[]>([
    {
      tableId: 'table-1',
      tableName: 'Waiting for table detection...',
      players: [],
      pot: 0,
      communityCards: [],
      currentAction: 'No active table detected',
      isActive: false,
    },
  ]);

  // Listen for table updates from WebSocket
  React.useEffect(() => {
    if (messages && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];

      // Handle different message types from backend
      if (latestMessage.type === 'table_update' && latestMessage.data) {
        setTables([latestMessage.data]);
      } else {
        // Handle incremental detection events to update current table
        setTables(prevTables => {
          const currentTable = prevTables[0] || {
            tableId: 'table-1',
            tableName: 'Live Table',
            players: [],
            pot: 0,
            communityCards: [],
            currentAction: '',
            isActive: true,
          };

          let updated = { ...currentTable };

          // Card detection events
          if (latestMessage.type === 'card_detected' || latestMessage.type === 'cards_detected') {
            const cardData = latestMessage.data || latestMessage;
            if (cardData.cards && Array.isArray(cardData.cards)) {
              // Community cards
              if (cardData.type === 'community' || cardData.cardType === 'board') {
                updated.communityCards = cardData.cards;
                updated.currentAction = `${cardData.cards.length} community cards detected`;
              }
              // Hole cards for a specific player
              else if (cardData.seat !== undefined || cardData.playerId !== undefined) {
                const seatNum = cardData.seat || cardData.playerId;
                updated.players = [...updated.players];
                const playerIndex = updated.players.findIndex(p => p.seat === seatNum);
                if (playerIndex >= 0) {
                  updated.players[playerIndex] = { ...updated.players[playerIndex], cards: cardData.cards };
                }
              }
            }
          }

          // Player detection events
          if (latestMessage.type === 'player_detected' || latestMessage.type === 'player_update') {
            const playerData = latestMessage.data || latestMessage;
            if (playerData.seat !== undefined) {
              updated.players = [...updated.players];
              const existingIndex = updated.players.findIndex(p => p.seat === playerData.seat);

              const player: Player = {
                seat: playerData.seat,
                name: playerData.name || `Player ${playerData.seat}`,
                chips: playerData.chips || playerData.stack || 0,
                cards: playerData.cards,
                isActive: playerData.isActive !== undefined ? playerData.isActive : true,
                isFolded: playerData.isFolded || playerData.folded || false,
              };

              if (existingIndex >= 0) {
                updated.players[existingIndex] = player;
              } else {
                updated.players.push(player);
              }
              updated.currentAction = `${player.name} detected`;
            }
          }

          // Pot detection events
          if (latestMessage.type === 'pot_update' || latestMessage.type === 'pot_detected') {
            const potData = latestMessage.data || latestMessage;
            if (potData.pot !== undefined || potData.amount !== undefined) {
              updated.pot = potData.pot || potData.amount;
              updated.currentAction = `Pot: ${updated.pot}`;
            }
          }

          // Action detection events
          if (latestMessage.type === 'action_detected' || latestMessage.type === 'player_action') {
            const actionData = latestMessage.data || latestMessage;
            if (actionData.action) {
              updated.currentAction = actionData.player
                ? `${actionData.player} ${actionData.action}`
                : actionData.action;
            }
          }

          return [updated];
        });
      }
    }
  }, [messages]);

  const [selectedTable, setSelectedTable] = useState<string>('table-1');
  const [detectionActive, setDetectionActive] = useState(true);
  const [playerDetection, setPlayerDetection] = useState(true);
  const [cardDetection, setCardDetection] = useState(true);
  const [potDetection, setPotDetection] = useState(true);

  // Auto-start tracking on mount
  React.useEffect(() => {
    sendMessage({
      type: 'start_tracking',
      tableId: selectedTable,
    });
  }, [selectedTable, sendMessage]);

  const handleRefreshTable = (tableId: string) => {
    sendMessage({
      type: 'refresh_table',
      tableId: tableId,
    });
  };

  const PokerTable = ({ table }: { table: TableData }) => (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: isMobile ? 300 : 400,
        background: 'linear-gradient(135deg, #4a3a6a 0%, #6b5b8a 50%, #5a4a7a 100%)',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4), inset 0 0 60px rgba(0,0,0,0.3)',
        border: '12px solid',
        borderColor: '#3d2f1f',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: -6,
          left: -6,
          right: -6,
          bottom: -6,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #5a4438 0%, #4a3428 50%, #3d2f1f 100%)',
          zIndex: -1,
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        },
      }}
    >
      {/* Pot */}
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
        }}
      >
        <Box
          sx={{
            background: 'rgba(20, 20, 35, 0.85)',
            borderRadius: 2,
            px: 3,
            py: 1,
            mb: 2,
            border: '2px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          }}
        >
          <Typography 
            variant="h6" 
            sx={{ 
              color: '#ffffff',
              fontWeight: 700,
              textShadow: '0 2px 4px rgba(0,0,0,0.5)',
            }}
          >
            Pot: ${table.pot}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
          {table.communityCards.map((card, index) => (
            <Paper
              key={index}
              sx={{
                width: 45,
                height: 64,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                background: '#ffffff',
                borderRadius: 1.5,
                boxShadow: '0 4px 8px rgba(0,0,0,0.3), 0 1px 3px rgba(0,0,0,0.2)',
                border: '1px solid #e0e0e0',
              }}
            >
              {card}
            </Paper>
          ))}
        </Box>
      </Box>

      {/* Players */}
      {table.players.map((player, index) => {
        const angle = (index * 360) / table.players.length - 90;
        const radius = isMobile ? 100 : 140;
        const x = radius * Math.cos((angle * Math.PI) / 180);
        const y = radius * Math.sin((angle * Math.PI) / 180);

        return (
          <Box
            key={player.seat}
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
            }}
          >
            <Card
              sx={{
                minWidth: 110,
                background: player.isActive 
                  ? 'linear-gradient(135deg, rgba(30, 30, 45, 0.95) 0%, rgba(20, 20, 35, 0.95) 100%)'
                  : 'rgba(25, 25, 40, 0.9)',
                opacity: player.isFolded ? 0.5 : 1,
                border: player.isActive 
                  ? `2px solid ${theme.palette.primary.main}` 
                  : '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: 2,
                boxShadow: player.isActive 
                  ? `0 0 12px ${theme.palette.primary.main}40, 0 4px 8px rgba(0,0,0,0.4)`
                  : '0 4px 8px rgba(0,0,0,0.4)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'scale(1.05)',
                  boxShadow: '0 6px 16px rgba(0,0,0,0.5)',
                },
              }}
            >
              <CardContent sx={{ p: 1.5 }}>
                <Typography
                  variant="caption"
                  sx={{
                    fontWeight: 700,
                    color: '#ffffff',
                    textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                    display: 'block',
                    mb: 0.5,
                  }}
                >
                  {player.name}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: player.isActive ? theme.palette.primary.light : '#b0b0b0',
                    fontWeight: 600,
                    mb: player.cards && player.cards.length > 0 ? 0.5 : 0,
                  }}
                >
                  ${player.chips}
                </Typography>
                {/* Hole Cards */}
                {player.cards && player.cards.length > 0 && (
                  <Box sx={{ display: 'flex', gap: 0.3, mt: 0.5, justifyContent: 'center' }}>
                    {player.cards.map((card, cardIdx) => (
                      <Paper
                        key={cardIdx}
                        sx={{
                          width: 22,
                          height: 32,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 'bold',
                          fontSize: '0.65rem',
                          background: '#ffffff',
                          borderRadius: 0.5,
                          boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                          border: '1px solid #e0e0e0',
                          color: card.includes('h') || card.includes('d') ? '#d32f2f' : '#000',
                        }}
                      >
                        {card}
                      </Paper>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        );
      })}
    </Box>
  );

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight="bold">
          Table View
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          {/* Detection Status Indicators */}
          <Box display="flex" gap={1} alignItems="center" sx={{
            background: 'rgba(0, 0, 0, 0.2)',
            borderRadius: 2,
            px: 2,
            py: 1,
          }}>
            <Box display="flex" alignItems="center" gap={0.5}>
              <FiberManualRecord
                sx={{
                  fontSize: 14,
                  color: playerDetection ? '#4caf50' : '#666',
                  animation: playerDetection ? 'pulse 2s infinite' : 'none',
                  '@keyframes pulse': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: 0.5 },
                  },
                }}
              />
              <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>Players</Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <FiberManualRecord
                sx={{
                  fontSize: 14,
                  color: cardDetection ? '#4caf50' : '#666',
                  animation: cardDetection ? 'pulse 2s infinite' : 'none',
                }}
              />
              <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>Cards</Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <FiberManualRecord
                sx={{
                  fontSize: 14,
                  color: potDetection ? '#4caf50' : '#666',
                  animation: potDetection ? 'pulse 2s infinite' : 'none',
                }}
              />
              <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>Pot</Typography>
            </Box>
          </Box>
          <IconButton onClick={() => handleRefreshTable(selectedTable)}>
            <Refresh />
          </IconButton>
          <IconButton>
            <Fullscreen />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Table Selection */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Active Tables
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              {tables.map((table) => (
                <Chip
                  key={table.tableId}
                  label={table.tableName}
                  onClick={() => setSelectedTable(table.tableId)}
                  color={selectedTable === table.tableId ? 'primary' : 'default'}
                  variant={selectedTable === table.tableId ? 'filled' : 'outlined'}
                  icon={<Casino />}
                />
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Table Display */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            {tables
              .filter((t) => t.tableId === selectedTable)
              .map((table) => (
                <PokerTable key={table.tableId} table={table} />
              ))}
            <LinearProgress sx={{ mt: 2 }} />
          </Paper>
        </Grid>

        {/* Smart Advice Panel with new components */}
        <Grid item xs={12} md={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <DecisionTimer timeLimit={30} compact={isMobile} />
            <AdvicePanel messages={messages} compact={isMobile} />
            <HandStrengthMeter strength={75} compact={isMobile} />
            <EquityCalculator
              winEquity={62.5}
              tieEquity={3.5}
              ev={12.5}
              potOdds={33}
              requiredEquity={30}
              compact={isMobile}
            />
          </Box>
        </Grid>

        {/* Bet Sizing */}
        <Grid item xs={12} md={4}>
          <BetSizingRecommendations potSize={250} compact={isMobile} />
        </Grid>

        {/* Table Info */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Table Information
            </Typography>
            {tables
              .filter((t) => t.tableId === selectedTable)
              .map((table) => (
                <Box key={table.tableId}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Table Name
                    </Typography>
                    <Typography variant="body1">{table.tableName}</Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Current Action
                    </Typography>
                    <Typography variant="body1">{table.currentAction}</Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Players
                    </Typography>
                    <Typography variant="body1">
                      {table.players.filter((p) => !p.isFolded).length} / {table.players.length}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Status
                    </Typography>
                    <Chip
                      label={table.isActive ? 'Active' : 'Waiting'}
                      color={table.isActive ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </Box>
              ))}
          </Paper>

          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <Button variant="outlined" fullWidth>
                Add Table
              </Button>
              <Button variant="outlined" fullWidth>
                Table Settings
              </Button>
              <Button variant="outlined" fullWidth>
                Export Hand History
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
