/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/styles/theme.ts
version: v76.0.0
last_commit: '2025-10-15T05:21:00Z'
fixes:
- date: '2025-10-15'
  summary: Created optimized dark mode theme with customizable brightness and color schemes
---
POKERTOOL-HEADER-END */

import { createTheme, ThemeOptions, Theme } from '@mui/material/styles';

export enum ColorScheme {
  POKER_GREEN = 'POKER_GREEN',
  PURPLE = 'PURPLE',
  BLUE = 'BLUE',
  TRUE_BLACK = 'TRUE_BLACK',
}

export interface ThemeConfig {
  darkMode: boolean;
  brightness: number; // 0.8 - 1.2
  colorScheme: ColorScheme;
  blueLightReduction: boolean;
}

// Color scheme definitions
const COLOR_SCHEMES = {
  [ColorScheme.POKER_GREEN]: {
    primary: '#4caf50',
    secondary: '#ff9800',
    background: '#1a2e1a',
    paper: '#243324',
  },
  [ColorScheme.PURPLE]: {
    primary: '#9c27b0',
    secondary: '#ff5722',
    background: '#1a1a2e',
    paper: '#2d2d44',
  },
  [ColorScheme.BLUE]: {
    primary: '#2196f3',
    secondary: '#ff9800',
    background: '#0d1b2a',
    paper: '#1b263b',
  },
  [ColorScheme.TRUE_BLACK]: {
    primary: '#4caf50',
    secondary: '#ff9800',
    background: '#000000',
    paper: '#0a0a0a',
  },
};

// Apply blue light reduction filter
const applyBlueLightReduction = (color: string): string => {
  // Reduce blue component by 30%
  if (color.startsWith('#')) {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = Math.floor(parseInt(color.slice(5, 7), 16) * 0.7);
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }
  return color;
};

// Apply brightness adjustment
const applyBrightness = (color: string, brightness: number): string => {
  if (color.startsWith('#')) {
    const r = Math.min(255, Math.floor(parseInt(color.slice(1, 3), 16) * brightness));
    const g = Math.min(255, Math.floor(parseInt(color.slice(3, 5), 16) * brightness));
    const b = Math.min(255, Math.floor(parseInt(color.slice(5, 7), 16) * brightness));
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }
  return color;
};

export const createOptimizedTheme = (config: ThemeConfig): Theme => {
  const scheme = COLOR_SCHEMES[config.colorScheme];
  const { brightness, blueLightReduction } = config;

  // Process colors
  let primaryColor = scheme.primary;
  let secondaryColor = scheme.secondary;
  let backgroundColor = scheme.background;
  let paperColor = scheme.paper;

  // Apply brightness
  if (brightness !== 1) {
    backgroundColor = applyBrightness(backgroundColor, brightness);
    paperColor = applyBrightness(paperColor, brightness);
  }

  // Apply blue light reduction
  if (blueLightReduction) {
    primaryColor = applyBlueLightReduction(primaryColor);
    secondaryColor = applyBlueLightReduction(secondaryColor);
    backgroundColor = applyBlueLightReduction(backgroundColor);
    paperColor = applyBlueLightReduction(paperColor);
  }

  const themeOptions: ThemeOptions = {
    palette: {
      mode: config.darkMode ? 'dark' : 'light',
      primary: {
        main: primaryColor,
        light: applyBrightness(primaryColor, 1.2),
        dark: applyBrightness(primaryColor, 0.8),
      },
      secondary: {
        main: secondaryColor,
        light: applyBrightness(secondaryColor, 1.2),
        dark: applyBrightness(secondaryColor, 0.8),
      },
      background: {
        default: backgroundColor,
        paper: paperColor,
      },
      // Optimized text colors for WCAG AAA compliance
      text: {
        primary: config.darkMode ? '#ffffff' : '#000000',
        secondary: config.darkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
      },
      // Success, error, warning colors
      success: {
        main: '#4caf50',
        light: '#81c784',
        dark: '#388e3c',
      },
      error: {
        main: '#f44336',
        light: '#e57373',
        dark: '#d32f2f',
      },
      warning: {
        main: '#ff9800',
        light: '#ffb74d',
        dark: '#f57c00',
      },
      info: {
        main: '#2196f3',
        light: '#64b5f6',
        dark: '#1976d2',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 600,
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
      },
      h3: {
        fontSize: '1.75rem',
        fontWeight: 600,
      },
      h4: {
        fontSize: '1.5rem',
        fontWeight: 600,
      },
      h5: {
        fontSize: '1.25rem',
        fontWeight: 600,
      },
      h6: {
        fontSize: '1rem',
        fontWeight: 600,
      },
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 8,
            fontWeight: 600,
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backgroundImage: 'none', // Remove default gradient for cleaner look
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backgroundImage: 'none',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      // Optimize contrast for readability
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 600,
          },
        },
      },
    },
    shape: {
      borderRadius: 8,
    },
  };

  return createTheme(themeOptions);
};

// Default theme configuration
export const DEFAULT_THEME_CONFIG: ThemeConfig = {
  darkMode: true,
  brightness: 1.0,
  colorScheme: ColorScheme.POKER_GREEN,
  blueLightReduction: false,
};

// Load theme config from localStorage
export const loadThemeConfig = (): ThemeConfig => {
  try {
    const saved = localStorage.getItem('themeConfig');
    if (saved) {
      return { ...DEFAULT_THEME_CONFIG, ...JSON.parse(saved) };
    }
  } catch (error) {
    console.error('Failed to load theme config:', error);
  }
  return DEFAULT_THEME_CONFIG;
};

// Save theme config to localStorage
export const saveThemeConfig = (config: ThemeConfig): void => {
  try {
    localStorage.setItem('themeConfig', JSON.stringify(config));
  } catch (error) {
    console.error('Failed to save theme config:', error);
  }
};
