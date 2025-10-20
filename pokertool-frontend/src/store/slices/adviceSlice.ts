import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Advice state types
export type ActionType = 'FOLD' | 'CALL' | 'RAISE' | 'CHECK' | 'ALL-IN';

export type ConfidenceLevel = 'VERY_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW' | 'VERY_LOW';

export interface AlternativeAction {
  action: ActionType;
  amount?: number;
  ev: number;
  winProbability: number;
  reasoning: string;
  evDifference: number; // Difference from primary action
}

export interface Advice {
  action: ActionType;
  amount?: number;
  confidence: ConfidenceLevel;
  confidenceScore: number; // 0-100
  ev: number;
  potOdds: number;
  handStrength: number; // 0-100
  reasoning: string;
  alternatives: AlternativeAction[];
  timestamp: number;
}

export interface AdviceState {
  current: Advice | null;
  history: Advice[];
  isLoading: boolean;
  error: string | null;
  lastUpdate: number;
  cacheHitRate: number;
  fromCache: boolean;
}

const initialState: AdviceState = {
  current: null,
  history: [],
  isLoading: false,
  error: null,
  lastUpdate: 0,
  cacheHitRate: 0,
  fromCache: false,
};

const adviceSlice = createSlice({
  name: 'advice',
  initialState,
  reducers: {
    // Receive new advice
    receiveAdvice: (state, action: PayloadAction<Advice>) => {
      state.current = action.payload;
      state.isLoading = false;
      state.error = null;
      state.lastUpdate = Date.now();
      state.fromCache = false;
      
      // Add to history (keep last 50)
      state.history.unshift(action.payload);
      if (state.history.length > 50) {
        state.history = state.history.slice(0, 50);
      }
    },
    
    // Receive cached advice
    receiveCachedAdvice: (state, action: PayloadAction<Advice>) => {
      state.current = action.payload;
      state.isLoading = false;
      state.error = null;
      state.lastUpdate = Date.now();
      state.fromCache = true;
    },
    
    // Request advice (loading state)
    requestAdvice: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    
    // Advice error
    adviceError: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    
    // Update cache hit rate
    updateCacheHitRate: (state, action: PayloadAction<number>) => {
      state.cacheHitRate = action.payload;
    },
    
    // Clear current advice
    clearAdvice: (state) => {
      state.current = null;
      state.isLoading = false;
      state.error = null;
    },
    
    // Clear history
    clearHistory: (state) => {
      state.history = [];
    },
    
    // Interpolate advice (smooth transitions)
    interpolateAdvice: (state, action: PayloadAction<{ field: keyof Advice; value: number }>) => {
      if (state.current && typeof state.current[action.payload.field] === 'number') {
        (state.current as any)[action.payload.field] = action.payload.value;
        state.lastUpdate = Date.now();
      }
    },
  },
});

export const {
  receiveAdvice,
  receiveCachedAdvice,
  requestAdvice,
  adviceError,
  updateCacheHitRate,
  clearAdvice,
  clearHistory,
  interpolateAdvice,
} = adviceSlice.actions;

export default adviceSlice.reducer;
