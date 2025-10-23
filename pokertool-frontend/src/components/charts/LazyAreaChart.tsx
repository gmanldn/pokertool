/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/charts/LazyAreaChart.tsx
version: v103.0.5
last_commit: '2025-10-24T00:00:00+00:00'
fixes:
- date: '2025-10-24'
  summary: Add lazy-loading wrapper for Recharts AreaChart component to reduce bundle size
---
POKERTOOL-HEADER-END */

import React, { Suspense, lazy } from 'react';
import { Box, CircularProgress } from '@mui/material';

// Lazy load Recharts components
const AreaChartComponent = lazy(() =>
  import('recharts').then(module => ({
    default: module.AreaChart
  }))
);

const Area = lazy(() =>
  import('recharts').then(module => ({
    default: module.Area
  }))
);

const XAxis = lazy(() =>
  import('recharts').then(module => ({
    default: module.XAxis
  }))
);

const YAxis = lazy(() =>
  import('recharts').then(module => ({
    default: module.YAxis
  }))
);

const CartesianGrid = lazy(() =>
  import('recharts').then(module => ({
    default: module.CartesianGrid
  }))
);

const TooltipComponent = lazy(() =>
  import('recharts').then(module => ({
    default: module.Tooltip
  }))
);

const ResponsiveContainer = lazy(() =>
  import('recharts').then(module => ({
    default: module.ResponsiveContainer
  }))
);

interface LazyAreaChartProps {
  data: any[];
  dataKey: string;
  xKey: string;
  width?: number | `${number}%`;
  height?: number;
  fill?: string;
  stroke?: string;
}

const LoadingFallback: React.FC<{ height?: number }> = ({ height = 300 }) => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    height={height}
  >
    <CircularProgress size={40} />
  </Box>
);

export const LazyAreaChart: React.FC<LazyAreaChartProps> = ({
  data,
  dataKey,
  xKey,
  width = '100%' as `${number}%`,
  height = 300,
  fill = '#8884d8',
  stroke = '#8884d8'
}) => {
  return (
    <Suspense fallback={<LoadingFallback height={height} />}>
      <ResponsiveContainer width={width} height={height}>
        <AreaChartComponent data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <TooltipComponent />
          <Area type="monotone" dataKey={dataKey} stroke={stroke} fill={fill} />
        </AreaChartComponent>
      </ResponsiveContainer>
    </Suspense>
  );
};
