import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Settings state types
export type ThemeMode = 'light' | 'dark' | 'poker-green' | 'poker-purple' | 'poker-blue' | 'oled-black';

export type AdviceDetailLevel = 'minimal' | 'compact' | 'detailed' | 'expert';

export interface SettingsState {
  // Display settings
  theme: ThemeMode;
  brightness: number; // 80-120
  blueLightReduction: boolean;
  
  // Advice settings
  adviceDetailLevel: AdviceDetailLevel;
  updateFrequency: number; // 1-5 updates per second
  showAlternatives: boolean;
  showConfidenceBreakdown: boolean;
  
  // Sound settings
  soundEnabled: boolean;
  soundVolume: number; // 0-100
  decisionTimerAlert: boolean;
  lowConfidenceWarning: boolean;
  
  // UI settings
  compactMode: boolean;
  autoHideInactive: boolean;
  showTooltips: boolean;
  tooltipDelay: number; // milliseconds
  
  // Mobile settings
  mobileLayout: boolean;
  bottomNavigation: boolean;
  swipeGestures: boolean;
  
  // Performance settings
  enableCache: boolean;
  cacheSize: number; // max entries
  interpolateValues: boolean;
  
  // Keyboard shortcuts
  keyboardShortcutsEnabled: boolean;
  customShortcuts: Record<string, string>;
  
  // Notifications
  browserNotifications: boolean;
  sessionAlerts: boolean;
}

const initialState: SettingsState = {
  // Display settings
  theme: 'dark',
  brightness: 100,
  blueLightReduction: false,
  
  // Advice settings
  adviceDetailLevel: 'detailed',
  updateFrequency: 2,
  showAlternatives: true,
  showConfidenceBreakdown: true,
  
  // Sound settings
  soundEnabled: true,
  soundVolume: 50,
  decisionTimerAlert: true,
  lowConfidenceWarning: true,
  
  // UI settings
  compactMode: false,
  autoHideInactive: false,
  showTooltips: true,
  tooltipDelay: 500,
  
  // Mobile settings
  mobileLayout: false,
  bottomNavigation: true,
  swipeGestures: true,
  
  // Performance settings
  enableCache: true,
  cacheSize: 100,
  interpolateValues: true,
  
  // Keyboard shortcuts
  keyboardShortcutsEnabled: true,
  customShortcuts: {
    fold: 'f',
    call: 'c',
    raise: 'r',
    check: 'k',
    toggleAdvice: 'a',
    toggleStats: 's',
    toggleHistory: 'h',
    help: '?',
  },
  
  // Notifications
  browserNotifications: false,
  sessionAlerts: true,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    // Update theme
    setTheme: (state, action: PayloadAction<ThemeMode>) => {
      state.theme = action.payload;
    },
    
    // Update brightness
    setBrightness: (state, action: PayloadAction<number>) => {
      state.brightness = Math.min(120, Math.max(80, action.payload));
    },
    
    // Toggle blue light reduction
    toggleBlueLightReduction: (state) => {
      state.blueLightReduction = !state.blueLightReduction;
    },
    
    // Update advice detail level
    setAdviceDetailLevel: (state, action: PayloadAction<AdviceDetailLevel>) => {
      state.adviceDetailLevel = action.payload;
    },
    
    // Update update frequency
    setUpdateFrequency: (state, action: PayloadAction<number>) => {
      state.updateFrequency = Math.min(5, Math.max(1, action.payload));
    },
    
    // Toggle alternatives
    toggleShowAlternatives: (state) => {
      state.showAlternatives = !state.showAlternatives;
    },
    
    // Toggle confidence breakdown
    toggleShowConfidenceBreakdown: (state) => {
      state.showConfidenceBreakdown = !state.showConfidenceBreakdown;
    },
    
    // Toggle sound
    toggleSound: (state) => {
      state.soundEnabled = !state.soundEnabled;
    },
    
    // Update volume
    setSoundVolume: (state, action: PayloadAction<number>) => {
      state.soundVolume = Math.min(100, Math.max(0, action.payload));
    },
    
    // Toggle compact mode
    toggleCompactMode: (state) => {
      state.compactMode = !state.compactMode;
    },
    
    // Toggle auto hide
    toggleAutoHideInactive: (state) => {
      state.autoHideInactive = !state.autoHideInactive;
    },
    
    // Update mobile layout
    setMobileLayout: (state, action: PayloadAction<boolean>) => {
      state.mobileLayout = action.payload;
    },
    
    // Update keyboard shortcut
    updateShortcut: (state, action: PayloadAction<{ key: string; value: string }>) => {
      state.customShortcuts[action.payload.key] = action.payload.value;
    },
    
    // Reset to defaults
    resetSettings: () => initialState,
    
    // Bulk update settings
    updateSettings: (state, action: PayloadAction<Partial<SettingsState>>) => {
      return {
        ...state,
        ...action.payload,
      };
    },
  },
});

export const {
  setTheme,
  setBrightness,
  toggleBlueLightReduction,
  setAdviceDetailLevel,
  setUpdateFrequency,
  toggleShowAlternatives,
  toggleShowConfidenceBreakdown,
  toggleSound,
  setSoundVolume,
  toggleCompactMode,
  toggleAutoHideInactive,
  setMobileLayout,
  updateShortcut,
  resetSettings,
  updateSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;
