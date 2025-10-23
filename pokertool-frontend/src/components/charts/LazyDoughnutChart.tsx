/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/charts/LazyDoughnutChart.tsx
version: v103.0.5
last_commit: '2025-10-24T00:00:00+00:00'
fixes:
- date: '2025-10-24'
  summary: Add lazy-loading wrapper for Chart.js Doughnut component to reduce bundle size
---
POKERTOOL-HEADER-END */

import React, { Suspense, lazy } from 'react';
import { Box, CircularProgress } from '@mui/material';

// Lazy load Chart.js Doughnut component
const ChartComponent = lazy(() =>
  import('react-chartjs-2').then(module => {
    // Also register Chart.js components when loaded
    import('chart.js').then(chartModule => {
      chartModule.Chart.register(
        chartModule.ArcElement,
        chartModule.Tooltip,
        chartModule.Legend
      );
    });
    return { default: module.Doughnut };
  })
);

interface LazyDoughnutChartProps {
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

export const LazyDoughnutChart: React.FC<LazyDoughnutChartProps> = ({ data, options, height }) => {
  return (
    <Suspense fallback={<LoadingFallback height={height} />}>
      <ChartComponent data={data} options={options} />
    </Suspense>
  );
};
