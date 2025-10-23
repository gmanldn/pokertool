/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ConfidenceVisualization.tsx
version: v76.0.0
last_commit: '2025-10-15T05:20:00Z'
fixes:
- date: '2025-10-15'
  summary: Created enhanced confidence visualization with breakdown and history
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect } from 'react';
import { LazyLineChart, LazyBarChart, LazyDoughnutChart } from './charts';
import {
  Box,
  Typography,
  LinearProgress,
  Tooltip,
  IconButton,
  Collapse,
  Grid,
  Paper,
} from '@mui/material';
import {
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  StarHalf as StarHalfIcon,
  InfoOutlined as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';

// Register ChartJS components

export enum ConfidenceLevel {
  VERY_HIGH = 'VERY_HIGH',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW',
  VERY_LOW = 'VERY_LOW',
}

interface ConfidenceBreakdown {
  handStrength: number;
  position: number;
  opponentModel: number;
  stackDepth: number;
  potSize: number;
}

interface ConfidenceHistoryEntry {
  timestamp: number;
  score: number;
  level: ConfidenceLevel;
}

interface ConfidenceVisualizationProps {
  confidence: ConfidenceLevel;
  confidenceScore: number; // 0-100
  breakdown?: ConfidenceBreakdown;
  history?: ConfidenceHistoryEntry[];
  showHistory?: boolean;
}

// Confidence tier configuration
const CONFIDENCE_TIERS = [
  { level: ConfidenceLevel.VERY_HIGH, min: 90, color: '#4caf50', label: 'Very High' },
  { level: ConfidenceLevel.HIGH, min: 75, color: '#8bc34a', label: 'High' },
  { level: ConfidenceLevel.MEDIUM, min: 60, color: '#ffc107', label: 'Medium' },
  { level: ConfidenceLevel.LOW, min: 40, color: '#ff9800', label: 'Low' },
  { level: ConfidenceLevel.VERY_LOW, min: 0, color: '#f44336', label: 'Very Low' },
];

export const ConfidenceVisualization: React.FC<ConfidenceVisualizationProps> = ({
  confidence,
  confidenceScore,
  breakdown,
  history = [],
  showHistory = true,
}) => {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showHistoryChart, setShowHistoryChart] = useState(false);

  // Get confidence tier
  const tier = CONFIDENCE_TIERS.find(t => t.level === confidence) || CONFIDENCE_TIERS[4];

  // Calculate star rating (0-5 stars)
  const starRating = (confidenceScore / 100) * 5;
  const fullStars = Math.floor(starRating);
  const hasHalfStar = starRating - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  // Render stars
  const renderStars = () => {
    const stars = [];
    
    // Full stars
    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <StarIcon key={`full-${i}`} sx={{ color: tier.color, fontSize: 20 }} />
      );
    }
    
    // Half star
    if (hasHalfStar) {
      stars.push(
        <StarHalfIcon key="half" sx={{ color: tier.color, fontSize: 20 }} />
      );
    }
    
    // Empty stars
    for (let i = 0; i < emptyStars; i++) {
      stars.push(
        <StarBorderIcon key={`empty-${i}`} sx={{ color: 'rgba(255,255,255,0.3)', fontSize: 20 }} />
      );
    }
    
    return stars;
  };

  // Confidence explanation
  const getConfidenceExplanation = () => {
    return `This ${tier.label.toLowerCase()} confidence (${confidenceScore}%) indicates ${
      confidenceScore >= 90
        ? 'very strong certainty in the recommendation. Follow this advice.'
        : confidenceScore >= 75
        ? 'strong confidence. This is a solid play in most situations.'
        : confidenceScore >= 60
        ? 'moderate confidence. Consider other factors carefully.'
        : confidenceScore >= 40
        ? 'lower confidence. Proceed with caution and use your judgment.'
        : 'very low confidence. This is a marginal spot - careful consideration required.'
    }`;
  };

  // Prepare history chart data
  const historyChartData = {
    labels: history.slice(-10).map((_, idx) => `${idx + 1}`),
    datasets: [
      {
        label: 'Confidence Score',
        data: history.slice(-10).map(h => h.score),
        borderColor: tier.color,
        backgroundColor: `${tier.color}40`,
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const historyChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Last 10 Decisions',
        color: '#fff',
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(255,255,255,0.1)',
        },
        ticks: {
          color: '#fff',
        },
      },
      x: {
        grid: {
          color: 'rgba(255,255,255,0.1)',
        },
        ticks: {
          color: '#fff',
        },
      },
    },
  };

  return (
    <Box>
      {/* Main Confidence Display */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Confidence
            </Typography>
            <Tooltip title={getConfidenceExplanation()} arrow>
              <IconButton size="small" sx={{ p: 0 }}>
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
          
          {/* Star Rating */}
          <Box sx={{ display: 'flex', gap: 0.25 }}>
            {renderStars()}
          </Box>
        </Box>

        {/* Confidence Bar with Gradient */}
        <Box sx={{ position: 'relative' }}>
          <LinearProgress
            variant="determinate"
            value={confidenceScore}
            sx={{
              height: 12,
              borderRadius: 6,
              backgroundColor: 'rgba(255,255,255,0.1)',
              '& .MuiLinearProgress-bar': {
                background: `linear-gradient(90deg, ${tier.color}80 0%, ${tier.color} 100%)`,
                borderRadius: 6,
                transition: 'all 0.5s ease',
              },
            }}
          />
          <Typography
            variant="caption"
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontWeight: 'bold',
              color: 'white',
              textShadow: '0 1px 2px rgba(0,0,0,0.8)',
            }}
          >
            {confidenceScore}%
          </Typography>
        </Box>

        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mt: 0.5,
            color: tier.color,
            fontWeight: 'bold',
            textAlign: 'center',
          }}
        >
          {tier.label} Confidence
        </Typography>
      </Box>

      {/* Confidence Breakdown */}
      {breakdown && (
        <Box sx={{ mb: 2 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              mb: 1,
            }}
            onClick={() => setShowBreakdown(!showBreakdown)}
          >
            <Typography variant="caption" color="text.secondary">
              Confidence Breakdown
            </Typography>
            <IconButton size="small">
              {showBreakdown ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={showBreakdown}>
            <Paper sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.05)' }}>
              <Grid container spacing={1}>
                {[
                  { label: 'Hand Strength', value: breakdown.handStrength },
                  { label: 'Position', value: breakdown.position },
                  { label: 'Opponent Model', value: breakdown.opponentModel },
                  { label: 'Stack Depth', value: breakdown.stackDepth },
                  { label: 'Pot Size', value: breakdown.potSize },
                ].map((factor) => (
                  <Grid item xs={12} key={factor.label}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption">{factor.label}</Typography>
                      <Typography variant="caption" fontWeight="bold">
                        {factor.value}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={factor.value}
                      sx={{
                        height: 4,
                        borderRadius: 2,
                        backgroundColor: 'rgba(255,255,255,0.1)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: tier.color,
                          borderRadius: 2,
                        },
                      }}
                    />
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Collapse>
        </Box>
      )}

      {/* Confidence History Chart */}
      {showHistory && history.length > 0 && (
        <Box>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              mb: 1,
            }}
            onClick={() => setShowHistoryChart(!showHistoryChart)}
          >
            <Typography variant="caption" color="text.secondary">
              Confidence History
            </Typography>
            <IconButton size="small">
              {showHistoryChart ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={showHistoryChart}>
            <Paper sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.05)', height: 200 }}>
              <LazyLineChart data={historyChartData} options={historyChartOptions} />
            </Paper>
          </Collapse>
        </Box>
      )}
    </Box>
  );
};

export default ConfidenceVisualization;
