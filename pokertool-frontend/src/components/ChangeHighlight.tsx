/**
 * ChangeHighlight Component
 *
 * Wrapper component that highlights children when value changes
 */
import React, { ReactNode } from 'react';
import { Box } from '@mui/material';
import { useChangeHighlightStyles, useDirectionalChangeHighlight } from '../hooks/useChangeHighlight';

interface ChangeHighlightProps {
  value: any;
  children: ReactNode;
  color?: string;
  duration?: number;
}

export const ChangeHighlight: React.FC<ChangeHighlightProps> = React.memo(({
  value,
  children,
  color = '#4caf50',
  duration = 1000
}) => {
  const styles = useChangeHighlightStyles(value, { color, duration });

  return (
    <Box sx={styles}>
      {children}
    </Box>
  );
});

ChangeHighlight.displayName = 'ChangeHighlight';


/**
 * Directional Change Highlight Component
 * Highlights increases in green, decreases in red
 */
interface DirectionalChangeHighlightProps {
  value: number;
  children: ReactNode;
  showArrow?: boolean;
}

export const DirectionalChangeHighlight: React.FC<DirectionalChangeHighlightProps> = React.memo(({
  value,
  children,
  showArrow = false
}) => {
  const { isHighlighted, direction, color } = useDirectionalChangeHighlight(value);

  const styles: React.CSSProperties = {
    backgroundColor: isHighlighted ? `${color}33` : 'transparent',
    transition: 'background-color 0.3s ease-out',
    boxShadow: isHighlighted ? `0 0 8px ${color}66` : 'none',
    position: 'relative',
    display: 'inline-block',
  };

  return (
    <Box sx={styles}>
      {showArrow && isHighlighted && direction !== 'none' && (
        <Box
          sx={{
            display: 'inline-block',
            marginRight: '4px',
            color,
            fontWeight: 'bold',
            fontSize: '14px'
          }}
        >
          {direction === 'up' ? '↑' : '↓'}
        </Box>
      )}
      {children}
    </Box>
  );
});

DirectionalChangeHighlight.displayName = 'DirectionalChangeHighlight';


/**
 * Flash Highlight Component
 * Quick flash animation when value changes
 */
interface FlashHighlightProps {
  value: any;
  children: ReactNode;
  color?: string;
}

export const FlashHighlight: React.FC<FlashHighlightProps> = React.memo(({
  value,
  children,
  color = '#4caf50'
}) => {
  const styles = useChangeHighlightStyles(value, { color, duration: 500 });

  return (
    <Box
      sx={{
        ...styles,
        animation: styles.backgroundColor !== 'transparent' ? 'flash 0.5s ease-out' : 'none',
        '@keyframes flash': {
          '0%': { opacity: 1 },
          '50%': { opacity: 0.7 },
          '100%': { opacity: 1 }
        }
      }}
    >
      {children}
    </Box>
  );
});

FlashHighlight.displayName = 'FlashHighlight';
