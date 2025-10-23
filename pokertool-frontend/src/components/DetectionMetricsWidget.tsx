import React from 'react';
import { Paper, Typography, Box, Grid } from '@mui/material';
import { CheckCircle, Error, Speed } from '@mui/icons-material';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = React.memo(({ title, value, icon, color }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <Box sx={{ color, display: 'flex', alignItems: 'center' }}>
      {icon}
    </Box>
    <Box>
      <Typography variant="caption" color="textSecondary">
        {title}
      </Typography>
      <Typography variant="h6" fontWeight="bold">
        {value}
      </Typography>
    </Box>
  </Box>
));

export const DetectionMetricsWidget: React.FC = () => {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Detection Metrics
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <MetricCard
            title="Accuracy"
            value="98.5%"
            icon={<CheckCircle />}
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={4}>
          <MetricCard
            title="Errors"
            value="3"
            icon={<Error />}
            color="#f44336"
          />
        </Grid>
        <Grid item xs={4}>
          <MetricCard
            title="FPS"
            value="24"
            icon={<Speed />}
            color="#2196f3"
          />
        </Grid>
      </Grid>
    </Paper>
  );
};
