/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/charts/LazyBarChart.tsx
version: v103.0.5
last_commit: '2025-10-24T00:00:00+00:00'
fixes:
- date: '2025-10-24'
  summary: Add lazy-loading wrapper for Chart.js Bar component to reduce bundle size
---
POKERTOOL-HEADER-END */

import React, { Suspense, lazy } from 'react';
import { Box, CircularProgress } from '@mui/material';

// Lazy load Chart.js Bar component
const ChartComponent = lazy(() =>
  import('react-chartjs-2').then(module => {
    // Also register Chart.js components when loaded
    import('chart.js').then(chartModule => {
      chartModule.Chart.register(
        chartModule.CategoryScale,
        chartModule.LinearScale,
        chartModule.BarElement,
        chartModule.Title,
        chartModule.Tooltip,
        chartModule.Legend
      );
    });
    return { default: module.Bar };
  })
);

interface LazyBarChartProps {
  data: any;
  options?: any;
  height?: number;
}

const LoadingFallback: React.FC<{ height?: number }> = ({ height = 200 }) => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    height={height}
  >
    <CircularProgress size={40} />
  </Box>
);

export const LazyBarChart: React.FC<LazyBarChartProps> = ({ data, options, height }) => {
  return (
    <Suspense fallback={<LoadingFallback height={height} />}>
      <ChartComponent data={data} options={options} />
    </Suspense>
  );
};
