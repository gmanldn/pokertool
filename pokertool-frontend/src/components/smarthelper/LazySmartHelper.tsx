/**
 * Lazy Loading Wrapper for SmartHelper Components
 *
 * Improves initial page load performance by code-splitting SmartHelper components.
 * Components are loaded on-demand when needed.
 */
import React, { Suspense, lazy } from 'react';
import { Box, CircularProgress, Skeleton } from '@mui/material';

// Lazy load all SmartHelper components
export const LazyRangeAnalyzer = lazy(() =>
  import('./RangeAnalyzer').then(module => ({ default: module.RangeAnalyzer }))
);

export const LazyMultiOpponentCompare = lazy(() =>
  import('./MultiOpponentCompare').then(module => ({ default: module.MultiOpponentCompare }))
);

export const LazySmartHelperSettings = lazy(() =>
  import('./SmartHelperSettings').then(module => ({ default: module.SmartHelperSettings }))
);

export const LazyEquityChart = lazy(() =>
  import('./EquityChart').then(module => ({ default: module.EquityChart }))
);

export const LazyDecisionFactors = lazy(() =>
  import('./DecisionFactors').then(module => ({ default: module.DecisionFactors }))
);

export const LazyPotOddsCalculator = lazy(() =>
  import('./PotOddsCalculator').then(module => ({ default: module.PotOddsCalculator }))
);

/**
 * Loading Skeleton for Range Analyzer
 */
export const RangeAnalyzerSkeleton: React.FC = () => (
  <Box sx={{ p: 2 }}>
    <Skeleton variant="rectangular" height={40} sx={{ mb: 2, borderRadius: 1 }} />
    <Skeleton variant="rectangular" height={50} sx={{ mb: 2, borderRadius: 1 }} />
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(13, 1fr)', gap: 0.5 }}>
      {Array.from({ length: 169 }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" sx={{ aspectRatio: '1', borderRadius: 1 }} />
      ))}
    </Box>
  </Box>
);

/**
 * Loading Skeleton for Multi-Opponent Compare
 */
export const MultiOpponentCompareSkeleton: React.FC = () => (
  <Box sx={{ p: 2 }}>
    <Skeleton variant="rectangular" height={40} sx={{ mb: 2, borderRadius: 1 }} />
    <Box sx={{ display: 'flex', gap: 1 }}>
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton
          key={i}
          variant="rectangular"
          width={160}
          height={180}
          sx={{ borderRadius: 1 }}
        />
      ))}
    </Box>
  </Box>
);

/**
 * Loading Skeleton for Settings Panel
 */
export const SmartHelperSettingsSkeleton: React.FC = () => (
  <Box sx={{ p: 2 }}>
    <Skeleton variant="rectangular" height={40} sx={{ mb: 2, borderRadius: 1 }} />
    {Array.from({ length: 5 }).map((_, i) => (
      <Skeleton
        key={i}
        variant="rectangular"
        height={60}
        sx={{ mb: 1, borderRadius: 1 }}
      />
    ))}
  </Box>
);

/**
 * Loading Skeleton for Equity Chart
 */
export const EquityChartSkeleton: React.FC = () => (
  <Box sx={{ p: 2 }}>
    <Skeleton variant="rectangular" height={40} sx={{ mb: 2, borderRadius: 1 }} />
    <Skeleton variant="rectangular" height={250} sx={{ borderRadius: 1 }} />
  </Box>
);

/**
 * Loading Skeleton for Decision Factors
 */
export const DecisionFactorsSkeleton: React.FC = () => (
  <Box sx={{ p: 2 }}>
    <Skeleton variant="rectangular" height={40} sx={{ mb: 2, borderRadius: 1 }} />
    {Array.from({ length: 6 }).map((_, i) => (
      <Box key={i} sx={{ mb: 1 }}>
        <Skeleton variant="rectangular" height={20} sx={{ mb: 0.5, borderRadius: 1 }} />
        <Skeleton variant="rectangular" height={8} sx={{ borderRadius: 1 }} />
      </Box>
    ))}
  </Box>
);

/**
 * Loading Skeleton for Pot Odds Calculator
 */
export const PotOddsCalculatorSkeleton: React.FC = () => (
  <Box sx={{ p: 2 }}>
    <Skeleton variant="rectangular" height={40} sx={{ mb: 2, borderRadius: 1 }} />
    <Skeleton variant="rectangular" height={60} sx={{ mb: 1, borderRadius: 1 }} />
    <Skeleton variant="rectangular" height={60} sx={{ mb: 1, borderRadius: 1 }} />
    <Skeleton variant="rectangular" height={80} sx={{ borderRadius: 1 }} />
  </Box>
);

/**
 * Generic Circular Loading Indicator
 */
export const CircularLoading: React.FC = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: 200,
      p: 2
    }}
  >
    <CircularProgress size={40} />
  </Box>
);

/**
 * Wrapper component that provides Suspense with appropriate fallback
 */
interface LazyWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  useSkeleton?: boolean;
  skeletonComponent?: React.ComponentType;
}

export const LazyWrapper: React.FC<LazyWrapperProps> = ({
  children,
  fallback,
  useSkeleton = true,
  skeletonComponent: SkeletonComponent
}) => {
  let suspenseFallback: React.ReactNode;

  if (fallback) {
    suspenseFallback = fallback;
  } else if (useSkeleton && SkeletonComponent) {
    suspenseFallback = <SkeletonComponent />;
  } else {
    suspenseFallback = <CircularLoading />;
  }

  return <Suspense fallback={suspenseFallback}>{children}</Suspense>;
};

/**
 * Pre-configured lazy wrappers for each component
 */
export const RangeAnalyzerWithSuspense: React.FC<React.ComponentProps<typeof LazyRangeAnalyzer>> = (props) => (
  <LazyWrapper skeletonComponent={RangeAnalyzerSkeleton}>
    <LazyRangeAnalyzer {...props} />
  </LazyWrapper>
);

export const MultiOpponentCompareWithSuspense: React.FC<React.ComponentProps<typeof LazyMultiOpponentCompare>> = (props) => (
  <LazyWrapper skeletonComponent={MultiOpponentCompareSkeleton}>
    <LazyMultiOpponentCompare {...props} />
  </LazyWrapper>
);

export const SmartHelperSettingsWithSuspense: React.FC<React.ComponentProps<typeof LazySmartHelperSettings>> = (props) => (
  <LazyWrapper skeletonComponent={SmartHelperSettingsSkeleton}>
    <LazySmartHelperSettings {...props} />
  </LazyWrapper>
);

export const EquityChartWithSuspense: React.FC<React.ComponentProps<typeof LazyEquityChart>> = (props) => (
  <LazyWrapper skeletonComponent={EquityChartSkeleton}>
    <LazyEquityChart {...props} />
  </LazyWrapper>
);

export const DecisionFactorsWithSuspense: React.FC<React.ComponentProps<typeof LazyDecisionFactors>> = (props) => (
  <LazyWrapper skeletonComponent={DecisionFactorsSkeleton}>
    <LazyDecisionFactors {...props} />
  </LazyWrapper>
);

export const PotOddsCalculatorWithSuspense: React.FC<React.ComponentProps<typeof LazyPotOddsCalculator>> = (props) => (
  <LazyWrapper skeletonComponent={PotOddsCalculatorSkeleton}>
    <LazyPotOddsCalculator {...props} />
  </LazyWrapper>
);

/**
 * Utility function to preload a component
 * Call this on hover or user interaction to improve perceived performance
 */
export const preloadComponent = (componentName: string) => {
  switch (componentName) {
    case 'RangeAnalyzer':
      return import('./RangeAnalyzer');
    case 'MultiOpponentCompare':
      return import('./MultiOpponentCompare');
    case 'SmartHelperSettings':
      return import('./SmartHelperSettings');
    case 'EquityChart':
      return import('./EquityChart');
    case 'DecisionFactors':
      return import('./DecisionFactors');
    case 'PotOddsCalculator':
      return import('./PotOddsCalculator');
    default:
      return Promise.resolve();
  }
};

/**
 * Preload all SmartHelper components
 * Useful for prefetching during idle time
 */
export const preloadAllSmartHelperComponents = () => {
  return Promise.all([
    import('./RangeAnalyzer'),
    import('./MultiOpponentCompare'),
    import('./SmartHelperSettings'),
    import('./EquityChart'),
    import('./DecisionFactors'),
    import('./PotOddsCalculator')
  ]);
};
