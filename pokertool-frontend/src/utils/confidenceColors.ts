/**
 * Confidence Coloring Utilities
 *
 * Provides color mappings and utilities for displaying confidence-based colors
 * throughout the application.
 */

export interface ConfidenceColorConfig {
  color: string;
  label: string;
  threshold: number;
}

/**
 * Default confidence color scheme
 * - High (green): >= 80%
 * - Medium (yellow/orange): 60-79%
 * - Low (red): < 60%
 */
export const CONFIDENCE_COLORS: ConfidenceColorConfig[] = [
  { color: '#4caf50', label: 'High', threshold: 0.8 },      // Green
  { color: '#ff9800', label: 'Medium', threshold: 0.6 },    // Orange
  { color: '#f44336', label: 'Low', threshold: 0.0 },       // Red
];

/**
 * Get color for a confidence value
 */
export function getConfidenceColor(confidence: number): string {
  for (const config of CONFIDENCE_COLORS) {
    if (confidence >= config.threshold) {
      return config.color;
    }
  }
  return CONFIDENCE_COLORS[CONFIDENCE_COLORS.length - 1].color;
}

/**
 * Get confidence level label
 */
export function getConfidenceLabel(confidence: number): string {
  for (const config of CONFIDENCE_COLORS) {
    if (confidence >= config.threshold) {
      return config.label;
    }
  }
  return CONFIDENCE_COLORS[CONFIDENCE_COLORS.length - 1].label;
}

/**
 * Get MUI color name for confidence
 */
export function getConfidenceMuiColor(confidence: number): 'success' | 'warning' | 'error' {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.6) return 'warning';
  return 'error';
}

/**
 * Get opacity based on confidence (for subtle effects)
 */
export function getConfidenceOpacity(confidence: number): number {
  return Math.max(0.3, Math.min(1.0, confidence));
}

/**
 * Get CSS styles for confidence-based coloring
 */
export function getConfidenceStyles(confidence: number): React.CSSProperties {
  return {
    color: getConfidenceColor(confidence),
    opacity: getConfidenceOpacity(confidence),
  };
}

/**
 * Get background color with opacity for confidence
 */
export function getConfidenceBackgroundColor(confidence: number, alpha: number = 0.2): string {
  const color = getConfidenceColor(confidence);
  // Convert hex to rgba
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
