/**
 * Equity Chart Component
 *
 * Real-time line graph showing equity evolution throughout the hand
 */
import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

export interface EquityDataPoint {
  street: string;
  equity: number;
  timestamp?: number;
}

interface EquityChartProps {
  data: EquityDataPoint[];
  currentEquity: number;
  title?: string;
}

export const EquityChart: React.FC<EquityChartProps> = React.memo(({
  data,
  currentEquity,
  title = 'Hand Equity Evolution'
}) => {
  const getEquityColor = (equity: number): string => {
    if (equity >= 70) return '#4caf50';
    if (equity >= 50) return '#8bc34a';
    if (equity >= 30) return '#ff9800';
    return '#f44336';
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const equity = payload[0].value;
      return (
        <Box
          sx={{
            backgroundColor: 'rgba(33, 33, 33, 0.95)',
            p: 1.5,
            borderRadius: 1,
            border: `1px solid ${getEquityColor(equity)}`
          }}
        >
          <Typography variant="caption" color="white" fontWeight="bold">
            {payload[0].payload.street}
          </Typography>
          <Typography variant="body2" sx={{ color: getEquityColor(equity), fontWeight: 'bold' }}>
            {equity.toFixed(1)}% Equity
          </Typography>
        </Box>
      );
    }
    return null;
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold" color="white">
          📈 {title}
        </Typography>
        <Box sx={{ textAlign: 'right' }}>
          <Typography variant="caption" color="textSecondary">
            Current
          </Typography>
          <Typography
            variant="h6"
            fontWeight="bold"
            sx={{ color: getEquityColor(currentEquity) }}
          >
            {currentEquity.toFixed(1)}%
          </Typography>
        </Box>
      </Box>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <defs>
            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={getEquityColor(currentEquity)} stopOpacity={0.8} />
              <stop offset="95%" stopColor={getEquityColor(currentEquity)} stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
          <XAxis
            dataKey="street"
            stroke="rgba(255, 255, 255, 0.5)"
            tick={{ fill: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="rgba(255, 255, 255, 0.5)"
            tick={{ fill: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="equity"
            stroke={getEquityColor(currentEquity)}
            strokeWidth={3}
            fill="url(#equityGradient)"
            animationDuration={500}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Equity Bands Legend */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 1, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, backgroundColor: '#4caf50', borderRadius: 1 }} />
          <Typography variant="caption" color="textSecondary">Strong (70%+)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, backgroundColor: '#8bc34a', borderRadius: 1 }} />
          <Typography variant="caption" color="textSecondary">Good (50-70%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, backgroundColor: '#ff9800', borderRadius: 1 }} />
          <Typography variant="caption" color="textSecondary">Marginal (30-50%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, backgroundColor: '#f44336', borderRadius: 1 }} />
          <Typography variant="caption" color="textSecondary">Weak (&lt;30%)</Typography>
        </Box>
      </Box>
    </Paper>
  );
});

EquityChart.displayName = 'EquityChart';


/**
 * Helper function to create equity data points
 */
export function createEquityDataPoint(
  street: string,
  equity: number,
  timestamp?: number
): EquityDataPoint {
  return {
    street,
    equity,
    timestamp: timestamp || Date.now()
  };
}
