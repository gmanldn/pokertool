import React from 'react';
import { Box, Typography, Tooltip } from '@mui/material';
import styles from './FrequencyPie.module.css';

export interface ActionFrequency {
  action: 'fold' | 'call' | 'raise';
  frequency: number;
  color: string;
}

interface FrequencyPieProps {
  frequencies: ActionFrequency[];
  size?: number;
}

export const FrequencyPie: React.FC<FrequencyPieProps> = ({ 
  frequencies, 
  size = 120 
}) => {
  // Calculate cumulative angles for each segment
  let currentAngle = -90; // Start from top
  const segments = frequencies.map(({ action, frequency, color }) => {
    const angle = (frequency / 100) * 360;
    const segment = {
      action,
      frequency,
      color,
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
    };
    currentAngle += angle;
    return segment;
  });

  const radius = size / 2;
  const centerX = radius;
  const centerY = radius;

  // Create SVG path for each segment
  const createArc = (startAngle: number, endAngle: number) => {
    const start = polarToCartesian(centerX, centerY, radius, endAngle);
    const end = polarToCartesian(centerX, centerY, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    
    return [
      'M', centerX, centerY,
      'L', start.x, start.y,
      'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y,
      'Z'
    ].join(' ');
  };

  const polarToCartesian = (
    centerX: number, 
    centerY: number, 
    radius: number, 
    angleInDegrees: number
  ) => {
    const angleInRadians = (angleInDegrees * Math.PI) / 180.0;
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians),
    };
  };

  return (
    <Box className={styles.container}>
      <svg width={size} height={size} className={styles.pie}>
        {segments.map((segment, index) => (
          <Tooltip 
            key={index}
            title={`${segment.action.toUpperCase()}: ${segment.frequency.toFixed(1)}%`}
            arrow
          >
            <path
              d={createArc(segment.startAngle, segment.endAngle)}
              fill={segment.color}
              className={styles.segment}
              data-action={segment.action}
            />
          </Tooltip>
        ))}
        {/* Center circle for donut effect */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius * 0.6}
          fill="var(--background-color)"
          className={styles.center}
        />
      </svg>
      
      <Box className={styles.legend}>
        {frequencies.map((freq, index) => (
          <Box key={index} className={styles.legendItem}>
            <Box 
              className={styles.legendColor} 
              sx={{ backgroundColor: freq.color }}
            />
            <Typography variant="caption" className={styles.legendText}>
              {freq.action.charAt(0).toUpperCase() + freq.action.slice(1)}: {freq.frequency.toFixed(0)}%
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default FrequencyPie;
