/**
 * Range Analyzer Component
 *
 * Visual range grid showing AA to 22, AKs to 72o with color-coding
 * Allows selecting and editing ranges for hero and villain
 */
import React, { useState } from 'react';
import { Box, Paper, Typography, ToggleButtonGroup, ToggleButton, Chip, Tooltip } from '@mui/material';
import { Casino, Person, Psychology } from '@mui/icons-material';

export type HandCategory = 'pair' | 'suited' | 'offsuit';

export interface Hand {
  notation: string;
  category: HandCategory;
  selected: boolean;
  frequency: number;
}

interface RangeAnalyzerProps {
  title?: string;
  initialRange?: string[];
  onRangeChange?: (range: string[]) => void;
  readOnly?: boolean;
}

export const RangeAnalyzer: React.FC<RangeAnalyzerProps> = React.memo(({
  title = 'Range Analyzer',
  initialRange = [],
  onRangeChange,
  readOnly = false
}) => {
  const [selectedHands, setSelectedHands] = useState<Set<string>>(new Set(initialRange));
  const [selectionMode, setSelectionMode] = useState<'add' | 'remove'>('add');

  // Generate all possible hands
  const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
  const allHands: Hand[][] = [];

  // Build 13x13 grid
  for (let row = 0; row < 13; row++) {
    const rowHands: Hand[] = [];
    for (let col = 0; col < 13; col++) {
      const rank1 = ranks[row];
      const rank2 = ranks[col];

      let notation: string;
      let category: HandCategory;

      if (row === col) {
        // Pocket pairs (diagonal)
        notation = `${rank1}${rank2}`;
        category = 'pair';
      } else if (row < col) {
        // Suited (upper triangle)
        notation = `${rank2}${rank1}s`;
        category = 'suited';
      } else {
        // Offsuit (lower triangle)
        notation = `${rank1}${rank2}o`;
        category = 'offsuit';
      }

      rowHands.push({
        notation,
        category,
        selected: selectedHands.has(notation),
        frequency: selectedHands.has(notation) ? 100 : 0
      });
    }
    allHands.push(rowHands);
  }

  const handleHandClick = (hand: Hand) => {
    if (readOnly) return;

    const newSelected = new Set(selectedHands);

    if (selectionMode === 'add') {
      newSelected.add(hand.notation);
    } else {
      newSelected.delete(hand.notation);
    }

    setSelectedHands(newSelected);
    if (onRangeChange) {
      onRangeChange(Array.from(newSelected));
    }
  };

  const getHandColor = (hand: Hand): string => {
    if (!hand.selected) return 'transparent';

    switch (hand.category) {
      case 'pair':
        return '#f44336';  // Red for pairs
      case 'suited':
        return '#2196f3';  // Blue for suited
      case 'offsuit':
        return '#4caf50';  // Green for offsuit
      default:
        return '#9e9e9e';
    }
  };

  const getBorderColor = (hand: Hand): string => {
    if (!hand.selected) return 'rgba(255, 255, 255, 0.1)';
    return getHandColor(hand);
  };

  const clearRange = () => {
    setSelectedHands(new Set());
    if (onRangeChange) {
      onRangeChange([]);
    }
  };

  const selectAll = () => {
    const allNotations = allHands.flat().map(h => h.notation);
    setSelectedHands(new Set(allNotations));
    if (onRangeChange) {
      onRangeChange(allNotations);
    }
  };

  const selectPremium = () => {
    // Select top 5% of hands
    const premium = [
      'AA', 'KK', 'QQ', 'JJ', 'TT',
      'AKs', 'AQs', 'AJs', 'ATs',
      'AKo'
    ];
    setSelectedHands(new Set(premium));
    if (onRangeChange) {
      onRangeChange(premium);
    }
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        backgroundColor: 'rgba(33, 33, 33, 0.9)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 2
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Casino sx={{ color: 'primary.main', fontSize: 24 }} />
          <Typography variant="subtitle1" fontWeight="bold" color="white">
            {title}
          </Typography>
        </Box>
        <Chip
          label={`${selectedHands.size} hands`}
          size="small"
          sx={{
            backgroundColor: 'primary.main',
            color: 'white'
          }}
        />
      </Box>

      {/* Controls */}
      {!readOnly && (
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <ToggleButtonGroup
            value={selectionMode}
            exclusive
            onChange={(_, mode) => mode && setSelectionMode(mode)}
            size="small"
          >
            <ToggleButton value="add" sx={{ fontSize: '12px' }}>
              Add
            </ToggleButton>
            <ToggleButton value="remove" sx={{ fontSize: '12px' }}>
              Remove
            </ToggleButton>
          </ToggleButtonGroup>

          <Chip
            label="Clear"
            size="small"
            onClick={clearRange}
            sx={{ cursor: 'pointer' }}
          />
          <Chip
            label="All"
            size="small"
            onClick={selectAll}
            sx={{ cursor: 'pointer' }}
          />
          <Chip
            label="Premium"
            size="small"
            onClick={selectPremium}
            sx={{ cursor: 'pointer', backgroundColor: '#f44336', color: 'white' }}
          />
        </Box>
      )}

      {/* Range Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(13, 1fr)',
          gap: 0.5,
          maxWidth: 650,
          margin: '0 auto'
        }}
      >
        {allHands.map((row, rowIndex) =>
          row.map((hand, colIndex) => (
            <Tooltip
              key={`${rowIndex}-${colIndex}`}
              title={hand.notation}
              arrow
            >
              <Box
                onClick={() => handleHandClick(hand)}
                sx={{
                  aspectRatio: '1',
                  backgroundColor: hand.selected ? getHandColor(hand) + '44' : 'rgba(255, 255, 255, 0.03)',
                  border: `2px solid ${getBorderColor(hand)}`,
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: readOnly ? 'default' : 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': readOnly ? {} : {
                    transform: 'scale(1.1)',
                    boxShadow: `0 0 8px ${getBorderColor(hand)}`,
                    zIndex: 1
                  }
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '10px',
                    fontWeight: hand.selected ? 'bold' : 'normal',
                    color: hand.selected ? getHandColor(hand) : 'rgba(255, 255, 255, 0.5)',
                    userSelect: 'none'
                  }}
                >
                  {hand.notation}
                </Typography>
              </Box>
            </Tooltip>
          ))
        )}
      </Box>

      {/* Legend */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 2, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, backgroundColor: '#f44336', borderRadius: 1 }} />
          <Typography variant="caption" color="textSecondary">Pairs</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, backgroundColor: '#2196f3', borderRadius: 1 }} />
          <Typography variant="caption" color="textSecondary">Suited</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, backgroundColor: '#4caf50', borderRadius: 1 }} />
          <Typography variant="caption" color="textSecondary">Offsuit</Typography>
        </Box>
      </Box>
    </Paper>
  );
});

RangeAnalyzer.displayName = 'RangeAnalyzer';
