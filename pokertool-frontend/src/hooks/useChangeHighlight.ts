/**
 * useChangeHighlight Hook
 *
 * Hook that detects when a value changes and triggers a highlight animation
 */
import { useEffect, useRef, useState } from 'react';

interface UseChangeHighlightOptions {
  duration?: number;  // Duration of highlight in ms (default: 1000)
  color?: string;     // Highlight color (default: '#4caf50')
}

export function useChangeHighlight<T>(
  value: T,
  options: UseChangeHighlightOptions = {}
): boolean {
  const {
    duration = 1000,
  } = options;

  const [isHighlighted, setIsHighlighted] = useState(false);
  const previousValue = useRef<T>(value);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Check if value changed
    if (previousValue.current !== value) {
      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Trigger highlight
      setIsHighlighted(true);

      // Clear highlight after duration
      timeoutRef.current = setTimeout(() => {
        setIsHighlighted(false);
      }, duration);

      // Update previous value
      previousValue.current = value;
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, duration]);

  return isHighlighted;
}

/**
 * Hook that provides CSS classes for change highlighting
 */
export function useChangeHighlightStyles<T>(
  value: T,
  options: UseChangeHighlightOptions = {}
): React.CSSProperties {
  const { color = '#4caf50' } = options;
  const isHighlighted = useChangeHighlight(value, options);

  if (isHighlighted) {
    return {
      backgroundColor: `${color}33`,  // 20% opacity
      transition: 'background-color 0.3s ease-out',
      boxShadow: `0 0 8px ${color}66`,  // 40% opacity glow
    };
  }

  return {
    transition: 'background-color 0.3s ease-out',
  };
}

/**
 * Hook for highlighting increases vs decreases with different colors
 */
export function useDirectionalChangeHighlight(
  value: number
): {
  isHighlighted: boolean;
  direction: 'up' | 'down' | 'none';
  color: string;
} {
  const [isHighlighted, setIsHighlighted] = useState(false);
  const [direction, setDirection] = useState<'up' | 'down' | 'none'>('none');
  const previousValue = useRef<number>(value);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (previousValue.current !== value) {
      // Determine direction
      const newDirection = value > previousValue.current ? 'up' : 'down';
      setDirection(newDirection);

      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Trigger highlight
      setIsHighlighted(true);

      // Clear highlight after 1 second
      timeoutRef.current = setTimeout(() => {
        setIsHighlighted(false);
        setDirection('none');
      }, 1000);

      // Update previous value
      previousValue.current = value;
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value]);

  const color = direction === 'up' ? '#4caf50' : direction === 'down' ? '#f44336' : 'transparent';

  return { isHighlighted, direction, color };
}
