import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Session state types
export interface HandRecord {
  id: string;
  timestamp: number;
  result: 'win' | 'loss' | 'tie';
  amount: number;
  adviceGiven: string;
  actionTaken: string;
  followedAdvice: boolean;
}

export interface SessionStats {
  handsPlayed: number;
  handsWon: number;
  handsLost: number;
  totalProfit: number;
  winRate: number;
  roi: number;
  adviceFollowedCount: number;
  adviceIgnoredCount: number;
  adviceFollowedWinRate: number;
  adviceIgnoredWinRate: number;
  biggestWin: number;
  biggestLoss: number;
  currentStreak: number;
  bestStreak: number;
  worstStreak: number;
}

export interface SessionState {
  sessionId: string;
  startTime: number;
  endTime: number | null;
  connected: boolean;
  hands: HandRecord[];
  stats: SessionStats;
  isActive: boolean;
}

const initialStats: SessionStats = {
  handsPlayed: 0,
  handsWon: 0,
  handsLost: 0,
  totalProfit: 0,
  winRate: 0,
  roi: 0,
  adviceFollowedCount: 0,
  adviceIgnoredCount: 0,
  adviceFollowedWinRate: 0,
  adviceIgnoredWinRate: 0,
  biggestWin: 0,
  biggestLoss: 0,
  currentStreak: 0,
  bestStreak: 0,
  worstStreak: 0,
};

const initialState: SessionState = {
  sessionId: '',
  startTime: 0,
  endTime: null,
  connected: false,
  hands: [],
  stats: initialStats,
  isActive: false,
};

const sessionSlice = createSlice({
  name: 'session',
  initialState,
  reducers: {
    // Start new session
    startSession: (state) => {
      state.sessionId = `session-${Date.now()}`;
      state.startTime = Date.now();
      state.endTime = null;
      state.isActive = true;
      state.hands = [];
      state.stats = { ...initialStats };
    },
    
    // End session
    endSession: (state) => {
      state.endTime = Date.now();
      state.isActive = false;
      state.connected = false;
    },
    
    // Update connection status
    setConnected: (state, action: PayloadAction<boolean>) => {
      state.connected = action.payload;
    },
    
    // Add hand result
    addHandResult: (state, action: PayloadAction<Omit<HandRecord, 'id'>>) => {
      const hand: HandRecord = {
        id: `hand-${Date.now()}`,
        ...action.payload,
      };
      
      state.hands.push(hand);
      
      // Update stats
      state.stats.handsPlayed++;
      
      if (hand.result === 'win') {
        state.stats.handsWon++;
        state.stats.currentStreak = Math.max(0, state.stats.currentStreak) + 1;
        state.stats.bestStreak = Math.max(state.stats.bestStreak, state.stats.currentStreak);
        
        if (hand.amount > state.stats.biggestWin) {
          state.stats.biggestWin = hand.amount;
        }
      } else if (hand.result === 'loss') {
        state.stats.handsLost++;
        state.stats.currentStreak = Math.min(0, state.stats.currentStreak) - 1;
        state.stats.worstStreak = Math.min(state.stats.worstStreak, state.stats.currentStreak);
        
        if (Math.abs(hand.amount) > Math.abs(state.stats.biggestLoss)) {
          state.stats.biggestLoss = hand.amount;
        }
      }
      
      // Track advice adherence
      if (hand.followedAdvice) {
        state.stats.adviceFollowedCount++;
      } else {
        state.stats.adviceIgnoredCount++;
      }
      
      // Update profit
      state.stats.totalProfit += hand.amount;
      
      // Calculate derived stats
      state.stats.winRate = state.stats.handsPlayed > 0
        ? (state.stats.handsWon / state.stats.handsPlayed) * 100
        : 0;
      
      state.stats.roi = state.stats.handsPlayed > 0
        ? (state.stats.totalProfit / state.stats.handsPlayed) * 100
        : 0;
      
      // Calculate advice followed win rate
      const adviceFollowedHands = state.hands.filter(h => h.followedAdvice);
      const adviceFollowedWins = adviceFollowedHands.filter(h => h.result === 'win').length;
      state.stats.adviceFollowedWinRate = adviceFollowedHands.length > 0
        ? (adviceFollowedWins / adviceFollowedHands.length) * 100
        : 0;
      
      // Calculate advice ignored win rate
      const adviceIgnoredHands = state.hands.filter(h => !h.followedAdvice);
      const adviceIgnoredWins = adviceIgnoredHands.filter(h => h.result === 'win').length;
      state.stats.adviceIgnoredWinRate = adviceIgnoredHands.length > 0
        ? (adviceIgnoredWins / adviceIgnoredHands.length) * 100
        : 0;
    },
    
    // Clear session data
    clearSession: () => initialState,
    
    // Reset stats (keep session active)
    resetStats: (state) => {
      state.hands = [];
      state.stats = { ...initialStats };
    },
  },
});

export const {
  startSession,
  endSession,
  setConnected,
  addHandResult,
  clearSession,
  resetStats,
} = sessionSlice.actions;

export default sessionSlice.reducer;
