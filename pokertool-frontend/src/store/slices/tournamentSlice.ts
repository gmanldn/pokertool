import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Tournament status types
export type TournamentStatus = 'registered' | 'active' | 'completed' | 'cancelled';

// Tournament structure types
export type TournamentStructure = 'freezeout' | 'rebuy' | 'knockout' | 'turbo' | 'hyper-turbo' | 'satellite';

// Individual tournament entry
export interface Tournament {
  id: string;
  name: string;
  buyin: number;
  rebuy: number;
  addon: number;
  totalInvestment: number;
  prize: number;
  position: number | null;
  totalEntrants: number;
  structure: TournamentStructure;
  status: TournamentStatus;
  startTime: number;
  endTime: number | null;
  notes: string;
}

// Tournament statistics
export interface TournamentStats {
  totalTournaments: number;
  activeTournaments: number;
  completedTournaments: number;
  totalBuyins: number;
  totalPrizes: number;
  totalProfit: number;
  roi: number;
  averageBuyin: number;
  averagePrize: number;
  itm: number; // In The Money percentage
  averagePosition: number;
  bestFinish: number | null;
  biggestCash: number;
}

export interface TournamentState {
  tournaments: Tournament[];
  stats: TournamentStats;
  filters: {
    status: TournamentStatus | 'all';
    structure: TournamentStructure | 'all';
  };
}

const initialStats: TournamentStats = {
  totalTournaments: 0,
  activeTournaments: 0,
  completedTournaments: 0,
  totalBuyins: 0,
  totalPrizes: 0,
  totalProfit: 0,
  roi: 0,
  averageBuyin: 0,
  averagePrize: 0,
  itm: 0,
  averagePosition: 0,
  bestFinish: null,
  biggestCash: 0,
};

const initialState: TournamentState = {
  tournaments: [],
  stats: initialStats,
  filters: {
    status: 'all',
    structure: 'all',
  },
};

// Helper function to calculate stats
const calculateStats = (tournaments: Tournament[]): TournamentStats => {
  const completed = tournaments.filter(t => t.status === 'completed');
  const active = tournaments.filter(t => t.status === 'active');
  
  const totalBuyins = tournaments.reduce((sum, t) => sum + t.totalInvestment, 0);
  const totalPrizes = tournaments.reduce((sum, t) => sum + t.prize, 0);
  const totalProfit = totalPrizes - totalBuyins;
  const roi = totalBuyins > 0 ? (totalProfit / totalBuyins) * 100 : 0;
  
  const itmTournaments = completed.filter(t => t.prize > 0);
  const itm = completed.length > 0 ? (itmTournaments.length / completed.length) * 100 : 0;
  
  const averageBuyin = tournaments.length > 0 ? totalBuyins / tournaments.length : 0;
  const averagePrize = completed.length > 0 ? totalPrizes / completed.length : 0;
  
  const positionsWithData = completed.filter(t => t.position !== null);
  const averagePosition = positionsWithData.length > 0
    ? positionsWithData.reduce((sum, t) => sum + (t.position || 0), 0) / positionsWithData.length
    : 0;
  
  const bestFinish = positionsWithData.length > 0
    ? Math.min(...positionsWithData.map(t => t.position || Infinity))
    : null;
  
  const biggestCash = Math.max(...tournaments.map(t => t.prize), 0);
  
  return {
    totalTournaments: tournaments.length,
    activeTournaments: active.length,
    completedTournaments: completed.length,
    totalBuyins,
    totalPrizes,
    totalProfit,
    roi,
    averageBuyin,
    averagePrize,
    itm,
    averagePosition,
    bestFinish,
    biggestCash,
  };
};

const tournamentSlice = createSlice({
  name: 'tournament',
  initialState,
  reducers: {
    // Register a new tournament
    registerTournament: (state, action: PayloadAction<Omit<Tournament, 'id' | 'totalInvestment' | 'prize' | 'status' | 'endTime'>>) => {
      const tournament: Tournament = {
        id: `tournament-${Date.now()}`,
        ...action.payload,
        totalInvestment: action.payload.buyin + action.payload.rebuy + action.payload.addon,
        prize: 0,
        status: 'registered',
        endTime: null,
      };
      
      state.tournaments.push(tournament);
      state.stats = calculateStats(state.tournaments);
    },

    // Start a tournament (move to active)
    startTournament: (state, action: PayloadAction<string>) => {
      const tournament = state.tournaments.find(t => t.id === action.payload);
      if (tournament) {
        tournament.status = 'active';
        state.stats = calculateStats(state.tournaments);
      }
    },

    // Complete a tournament with results
    completeTournament: (state, action: PayloadAction<{ 
      id: string; 
      position: number; 
      prize: number;
      totalEntrants?: number;
    }>) => {
      const tournament = state.tournaments.find(t => t.id === action.payload.id);
      if (tournament) {
        tournament.status = 'completed';
        tournament.position = action.payload.position;
        tournament.prize = action.payload.prize;
        tournament.endTime = Date.now();
        if (action.payload.totalEntrants) {
          tournament.totalEntrants = action.payload.totalEntrants;
        }
        state.stats = calculateStats(state.tournaments);
      }
    },

    // Cancel a tournament
    cancelTournament: (state, action: PayloadAction<string>) => {
      const tournament = state.tournaments.find(t => t.id === action.payload);
      if (tournament) {
        tournament.status = 'cancelled';
        state.stats = calculateStats(state.tournaments);
      }
    },

    // Update tournament investment (add rebuy/addon)
    updateTournamentInvestment: (state, action: PayloadAction<{ id: string; rebuy?: number; addon?: number }>) => {
      const tournament = state.tournaments.find(t => t.id === action.payload.id);
      if (tournament) {
        if (action.payload.rebuy !== undefined) {
          tournament.rebuy = action.payload.rebuy;
        }
        if (action.payload.addon !== undefined) {
          tournament.addon = action.payload.addon;
        }
        tournament.totalInvestment = tournament.buyin + tournament.rebuy + tournament.addon;
        state.stats = calculateStats(state.tournaments);
      }
    },

    // Update tournament notes
    updateTournamentNotes: (state, action: PayloadAction<{ id: string; notes: string }>) => {
      const tournament = state.tournaments.find(t => t.id === action.payload.id);
      if (tournament) {
        tournament.notes = action.payload.notes;
      }
    },

    // Delete a tournament
    deleteTournament: (state, action: PayloadAction<string>) => {
      state.tournaments = state.tournaments.filter(t => t.id !== action.payload);
      state.stats = calculateStats(state.tournaments);
    },

    // Set filters
    setStatusFilter: (state, action: PayloadAction<TournamentStatus | 'all'>) => {
      state.filters.status = action.payload;
    },

    setStructureFilter: (state, action: PayloadAction<TournamentStructure | 'all'>) => {
      state.filters.structure = action.payload;
    },

    // Reset all tournaments
    resetTournaments: () => initialState,
  },
});

export const {
  registerTournament,
  startTournament,
  completeTournament,
  cancelTournament,
  updateTournamentInvestment,
  updateTournamentNotes,
  deleteTournament,
  setStatusFilter,
  setStructureFilter,
  resetTournaments,
} = tournamentSlice.actions;

export default tournamentSlice.reducer;

// Selectors
export const selectFilteredTournaments = (state: { tournament: TournamentState }) => {
  const { tournaments, filters } = state.tournament;
  
  return tournaments.filter(t => {
    if (filters.status !== 'all' && t.status !== filters.status) {
      return false;
    }
    if (filters.structure !== 'all' && t.structure !== filters.structure) {
      return false;
    }
    return true;
  });
};
