import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Game state types
export interface Card {
  rank: string;
  suit: string;
}

export interface Player {
  id: string;
  name: string;
  stack: number;
  position: number;
  cards?: Card[];
  currentBet: number;
  hasActed: boolean;
  isFolded: boolean;
  isAllIn: boolean;
}

export interface GameState {
  tableId: string | null;
  heroId: string | null;
  players: Player[];
  communityCards: Card[];
  pot: number;
  currentBet: number;
  blinds: {
    small: number;
    big: number;
  };
  street: 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
  buttonPosition: number;
  currentPosition: number;
  isHeroTurn: boolean;
  lastUpdate: number;
}

const initialState: GameState = {
  tableId: null,
  heroId: null,
  players: [],
  communityCards: [],
  pot: 0,
  currentBet: 0,
  blinds: {
    small: 0,
    big: 0,
  },
  street: 'preflop',
  buttonPosition: 0,
  currentPosition: 0,
  isHeroTurn: false,
  lastUpdate: 0,
};

const gameSlice = createSlice({
  name: 'game',
  initialState,
  reducers: {
    // Update entire table state
    updateTable: (state, action: PayloadAction<Partial<GameState>>) => {
      return {
        ...state,
        ...action.payload,
        lastUpdate: Date.now(),
      };
    },
    
    // Update specific player
    updatePlayer: (state, action: PayloadAction<{ id: string; updates: Partial<Player> }>) => {
      const playerIndex = state.players.findIndex(p => p.id === action.payload.id);
      if (playerIndex !== -1) {
        state.players[playerIndex] = {
          ...state.players[playerIndex],
          ...action.payload.updates,
        };
      }
    },
    
    // Add community card
    addCommunityCard: (state, action: PayloadAction<Card>) => {
      state.communityCards.push(action.payload);
      state.lastUpdate = Date.now();
    },
    
    // Update pot
    updatePot: (state, action: PayloadAction<number>) => {
      state.pot = action.payload;
      state.lastUpdate = Date.now();
    },
    
    // Advance street
    advanceStreet: (state) => {
      const streetOrder: GameState['street'][] = ['preflop', 'flop', 'turn', 'river', 'showdown'];
      const currentIndex = streetOrder.indexOf(state.street);
      if (currentIndex < streetOrder.length - 1) {
        state.street = streetOrder[currentIndex + 1];
        state.lastUpdate = Date.now();
      }
    },
    
    // Reset hand
    resetHand: (state) => {
      state.communityCards = [];
      state.pot = 0;
      state.currentBet = 0;
      state.street = 'preflop';
      state.players = state.players.map(p => ({
        ...p,
        cards: undefined,
        currentBet: 0,
        hasActed: false,
        isFolded: false,
        isAllIn: false,
      }));
      state.lastUpdate = Date.now();
    },
    
    // Clear table (disconnect)
    clearTable: () => initialState,
  },
});

export const {
  updateTable,
  updatePlayer,
  addCommunityCard,
  updatePot,
  advanceStreet,
  resetHand,
  clearTable,
} = gameSlice.actions;

export default gameSlice.reducer;
