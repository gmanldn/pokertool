/**
 * Micro Charts Grid Component
 *
 * Responsive grid layout organizing all SmartHelper micro-analytics components
 * with collapsible panels for space management and smooth animations
 */
import React, { useState } from 'react';
import {
  Box,
  Grid,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore,
  TrendingUp,
  AttachMoney,
  MyLocation,
  Psychology,
  UnfoldLess,
  UnfoldMore
} from '@mui/icons-material';
import { EquityChart, EquityDataPoint } from './EquityChart';
import { PotOddsVisual } from './PotOddsVisual';
import { PositionStatsCard } from './PositionStatsCard';
import { OpponentTendencyHeatmap } from './OpponentTendencyHeatmap';
import styles from './MicroChartsGrid.module.css';

interface MicroChartsGridProps {
  // Equity data
  equityData?: EquityDataPoint[];
  currentEquity?: number;

  // Pot odds data
  potSize?: number;
  betToCall?: number;
  impliedOdds?: number;

  // Position stats
  positionStats?: {
    position: string;
    vpip: number;
    pfr: number;
    aggression: number;
    winRate?: number;
    handsPlayed: number;
  };
  gtoComparison?: {
    vpip: number;
    pfr: number;
    aggression: number;
  };

  // Opponent data
  opponentStats?: {
    name: string;
    vpip: number;
    pfr: number;
    threebet: number;
    foldToCbet: number;
    foldToThreebet: number;
    aggression: number;
    handsPlayed: number;
  };

  // Layout customization
  showEquityChart?: boolean;
  showPotOdds?: boolean;
  showPositionStats?: boolean;
  showOpponentHeatmap?: boolean;

  // Collapsible panel settings
  enableCollapsiblePanels?: boolean;
  defaultExpandedPanels?: string[]; // Panel IDs to expand by default
}

export const MicroChartsGrid: React.FC<MicroChartsGridProps> = React.memo(({
  equityData = [],
  currentEquity = 0,
  potSize = 0,
  betToCall = 0,
  impliedOdds,
  positionStats,
  gtoComparison,
  opponentStats,
  showEquityChart = true,
  showPotOdds = true,
  showPositionStats = true,
  showOpponentHeatmap = true,
  enableCollapsiblePanels = false,
  defaultExpandedPanels = ['equity', 'potOdds', 'position', 'opponent']
}) => {
  const [expandedPanels, setExpandedPanels] = useState<Set<string>>(
    new Set(defaultExpandedPanels)
  );

  const handlePanelChange = (panelId: string) => {
    setExpandedPanels((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(panelId)) {
        newSet.delete(panelId);
      } else {
        newSet.add(panelId);
      }
      return newSet;
    });
  };

  const collapseAll = () => {
    setExpandedPanels(new Set());
  };

  const expandAll = () => {
    setExpandedPanels(new Set(['equity', 'potOdds', 'position', 'opponent']));
  };

  const renderPanel = (
    panelId: string,
    title: string,
    icon: React.ReactNode,
    content: React.ReactNode,
    statusChip?: React.ReactNode
  ) => {
    if (!enableCollapsiblePanels) {
      return content;
    }

    return (
      <Accordion
        expanded={expandedPanels.has(panelId)}
        onChange={() => handlePanelChange(panelId)}
        className={styles.panel}
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          '&:before': { display: 'none' },
          borderRadius: 1,
          overflow: 'hidden'
        }}
      >
        <AccordionSummary
          expandIcon={
            <ExpandMore
              className={expandedPanels.has(panelId) ? styles.expandIconRotated : styles.expandIcon}
              sx={{ color: 'white' }}
            />
          }
          className={styles.panelHeader}
          sx={{
            minHeight: 48,
            '& .MuiAccordionSummary-content': {
              margin: '8px 0',
              alignItems: 'center'
            }
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
            {icon}
            <Typography variant="body2" fontWeight="bold" color="white">
              {title}
            </Typography>
            {statusChip && <Box sx={{ ml: 'auto', mr: 1 }}>{statusChip}</Box>}
          </Box>
        </AccordionSummary>
        <AccordionDetails
          className={expandedPanels.has(panelId) ? styles.panelContentExpanded : styles.panelContentCollapsed}
          sx={{ p: 0 }}
        >
          {content}
        </AccordionDetails>
      </Accordion>
    );
  };

  const hasAnyData = equityData.length > 0 || potSize > 0 || positionStats || opponentStats;

  return (
    <Box sx={{ width: '100%' }}>
      {/* Collapse/Expand All Controls */}
      {enableCollapsiblePanels && hasAnyData && (
        <Box sx={{ display: 'flex', gap: 1, mb: 2, justifyContent: 'flex-end' }}>
          <Tooltip title="Collapse All Panels">
            <IconButton
              size="small"
              onClick={collapseAll}
              className={styles.controlButton}
              sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
            >
              <UnfoldLess fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Expand All Panels">
            <IconButton
              size="small"
              onClick={expandAll}
              className={styles.controlButton}
              sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
            >
              <UnfoldMore fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      <Grid container spacing={2}>
        {/* Equity Chart - Full width top row */}
        {showEquityChart && equityData.length > 0 && (
          <Grid item xs={12} className={styles.staggered}>
            {renderPanel(
              'equity',
              'Hand Equity Evolution',
              <TrendingUp sx={{ fontSize: 20, color: 'primary.main' }} />,
              <EquityChart
                data={equityData}
                currentEquity={currentEquity}
                title="Hand Equity Evolution"
              />,
              <Chip
                label={`${currentEquity.toFixed(1)}%`}
                size="small"
                className={styles.statusChip}
                sx={{
                  height: 20,
                  fontSize: '10px',
                  backgroundColor: currentEquity >= 50 ? '#4caf50' : '#ff9800',
                  color: 'white'
                }}
              />
            )}
          </Grid>
        )}

        {/* Pot Odds and Position Stats - Side by side */}
        {showPotOdds && potSize > 0 && (
          <Grid item xs={12} md={6} className={styles.staggered}>
            {renderPanel(
              'potOdds',
              'Pot Odds',
              <AttachMoney sx={{ fontSize: 20, color: 'primary.main' }} />,
              <PotOddsVisual
                potSize={potSize}
                betToCall={betToCall}
                impliedOdds={impliedOdds}
              />,
              <Chip
                label={`${((betToCall / (potSize + betToCall)) * 100).toFixed(1)}%`}
                size="small"
                className={styles.statusChip}
                sx={{ height: 20, fontSize: '10px' }}
              />
            )}
          </Grid>
        )}

        {showPositionStats && positionStats && (
          <Grid item xs={12} md={showPotOdds && potSize > 0 ? 6 : 12} className={styles.staggered}>
            {renderPanel(
              'position',
              'Position Stats',
              <MyLocation sx={{ fontSize: 20, color: 'primary.main' }} />,
              <PositionStatsCard
                stats={positionStats}
                gtoComparison={gtoComparison}
              />,
              <Chip
                label={positionStats.position}
                size="small"
                className={styles.statusChip}
                sx={{ height: 20, fontSize: '10px', backgroundColor: 'primary.main', color: 'white' }}
              />
            )}
          </Grid>
        )}

        {/* Opponent Heatmap - Full width bottom row */}
        {showOpponentHeatmap && opponentStats && (
          <Grid item xs={12} className={styles.staggered}>
            {renderPanel(
              'opponent',
              'Opponent Tendencies',
              <Psychology sx={{ fontSize: 20, color: 'primary.main' }} />,
              <OpponentTendencyHeatmap opponent={opponentStats} />,
              <Chip
                label={`${opponentStats.handsPlayed} hands`}
                size="small"
                className={styles.statusChip}
                sx={{ height: 20, fontSize: '10px' }}
              />
            )}
          </Grid>
        )}
      </Grid>

      {/* Empty State */}
      {!hasAnyData && (
        <Box
          className={styles.emptyState}
          sx={{
            p: 4,
            textAlign: 'center',
            color: 'rgba(255, 255, 255, 0.5)',
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 2,
            border: '1px dashed rgba(255, 255, 255, 0.1)'
          }}
        >
          <Typography variant="body2">
            📊 Micro-analytics will appear here once you start playing hands
          </Typography>
        </Box>
      )}
    </Box>
  );
});

MicroChartsGrid.displayName = 'MicroChartsGrid';
