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
  PlayArrow,
  Stop,
  Refresh,
  Fullscreen,
  Casino,
} from '@mui/icons-material';

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
  
  const [tables] = useState<TableData[]>([
    {
      tableId: 'table-1',
      tableName: 'High Stakes 1',
      players: [
        { seat: 1, name: 'Player 1', chips: 10000, isActive: true, isFolded: false },
        { seat: 2, name: 'Player 2', chips: 8500, isActive: false, isFolded: false },
        { seat: 3, name: 'Player 3', chips: 12000, isActive: false, isFolded: true },
        { seat: 4, name: 'Player 4', chips: 9500, isActive: false, isFolded: false },
      ],
      pot: 250,
      communityCards: ['As', 'Kh', '10d'],
      currentAction: 'Player 1 to act',
      isActive: true,
    },
  ]);

  const [selectedTable, setSelectedTable] = useState<string>('table-1');
  const [isTracking, setIsTracking] = useState(false);

  const handleStartTracking = () => {
    setIsTracking(true);
    sendMessage({
      type: 'start_tracking',
      tableId: selectedTable,
    });
  };

  const handleStopTracking = () => {
    setIsTracking(false);
    sendMessage({
      type: 'stop_tracking',
      tableId: selectedTable,
    });
  };

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
        background: 'radial-gradient(ellipse at center, #2e7d32 0%, #1b5e20 100%)',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: 'inset 0 0 50px rgba(0,0,0,0.5)',
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
        <Typography variant="h6" color="white" fontWeight="bold">
          Pot: ${table.pot}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
          {table.communityCards.map((card, index) => (
            <Paper
              key={index}
              sx={{
                width: 40,
                height: 56,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
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
                minWidth: 100,
                opacity: player.isFolded ? 0.5 : 1,
                border: player.isActive ? `2px solid ${theme.palette.primary.main}` : 'none',
              }}
            >
              <CardContent sx={{ p: 1 }}>
                <Typography variant="caption" fontWeight="bold">
                  {player.name}
                </Typography>
                <Typography variant="body2">
                  ${player.chips}
                </Typography>
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
        <Box display="flex" gap={1}>
          {!isTracking ? (
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={handleStartTracking}
              color="success"
            >
              Start Tracking
            </Button>
          ) : (
            <Button
              variant="contained"
              startIcon={<Stop />}
              onClick={handleStopTracking}
              color="error"
            >
              Stop Tracking
            </Button>
          )}
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
            {isTracking && <LinearProgress sx={{ mt: 2 }} />}
          </Paper>
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
