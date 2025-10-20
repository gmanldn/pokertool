import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Transaction types
export interface Transaction {
  id: string;
  timestamp: number;
  type: 'deposit' | 'withdrawal' | 'win' | 'loss' | 'buyin' | 'cashout';
  amount: number;
  description: string;
  balance: number;
}

// Bankroll limits for risk management
export interface BankrollLimits {
  stopLossAmount: number | null;
  stopLossPercentage: number | null;
  dailyLossLimit: number | null;
  sessionLossLimit: number | null;
}

// Stake recommendations based on bankroll
export interface StakeRecommendation {
  conservative: { min: number; max: number };
  moderate: { min: number; max: number };
  aggressive: { min: number; max: number };
}

export interface BankrollState {
  currentBalance: number;
  startingBalance: number;
  peakBalance: number;
  lowestBalance: number;
  totalDeposits: number;
  totalWithdrawals: number;
  transactions: Transaction[];
  limits: BankrollLimits;
  currency: string;
  lastUpdated: number;
}

const initialState: BankrollState = {
  currentBalance: 0,
  startingBalance: 0,
  peakBalance: 0,
  lowestBalance: 0,
  totalDeposits: 0,
  totalWithdrawals: 0,
  transactions: [],
  limits: {
    stopLossAmount: null,
    stopLossPercentage: null,
    dailyLossLimit: null,
    sessionLossLimit: null,
  },
  currency: 'USD',
  lastUpdated: Date.now(),
};

const bankrollSlice = createSlice({
  name: 'bankroll',
  initialState,
  reducers: {
    // Initialize bankroll with starting balance
    initializeBankroll: (state, action: PayloadAction<{ amount: number; currency?: string }>) => {
      state.currentBalance = action.payload.amount;
      state.startingBalance = action.payload.amount;
      state.peakBalance = action.payload.amount;
      state.lowestBalance = action.payload.amount;
      state.totalDeposits = action.payload.amount;
      if (action.payload.currency) {
        state.currency = action.payload.currency;
      }
      
      // Add initial deposit transaction
      const transaction: Transaction = {
        id: `txn-${Date.now()}`,
        timestamp: Date.now(),
        type: 'deposit',
        amount: action.payload.amount,
        description: 'Initial deposit',
        balance: action.payload.amount,
      };
      state.transactions.push(transaction);
      state.lastUpdated = Date.now();
    },

    // Add a deposit
    addDeposit: (state, action: PayloadAction<{ amount: number; description?: string }>) => {
      state.currentBalance += action.payload.amount;
      state.totalDeposits += action.payload.amount;
      
      if (state.currentBalance > state.peakBalance) {
        state.peakBalance = state.currentBalance;
      }
      
      const transaction: Transaction = {
        id: `txn-${Date.now()}`,
        timestamp: Date.now(),
        type: 'deposit',
        amount: action.payload.amount,
        description: action.payload.description || 'Deposit',
        balance: state.currentBalance,
      };
      state.transactions.push(transaction);
      state.lastUpdated = Date.now();
    },

    // Add a withdrawal
    addWithdrawal: (state, action: PayloadAction<{ amount: number; description?: string }>) => {
      state.currentBalance -= action.payload.amount;
      state.totalWithdrawals += action.payload.amount;
      
      if (state.currentBalance < state.lowestBalance) {
        state.lowestBalance = state.currentBalance;
      }
      
      const transaction: Transaction = {
        id: `txn-${Date.now()}`,
        timestamp: Date.now(),
        type: 'withdrawal',
        amount: action.payload.amount,
        description: action.payload.description || 'Withdrawal',
        balance: state.currentBalance,
      };
      state.transactions.push(transaction);
      state.lastUpdated = Date.now();
    },

    // Record a win
    recordWin: (state, action: PayloadAction<{ amount: number; description?: string }>) => {
      state.currentBalance += action.payload.amount;
      
      if (state.currentBalance > state.peakBalance) {
        state.peakBalance = state.currentBalance;
      }
      
      const transaction: Transaction = {
        id: `txn-${Date.now()}`,
        timestamp: Date.now(),
        type: 'win',
        amount: action.payload.amount,
        description: action.payload.description || 'Win',
        balance: state.currentBalance,
      };
      state.transactions.push(transaction);
      state.lastUpdated = Date.now();
    },

    // Record a loss
    recordLoss: (state, action: PayloadAction<{ amount: number; description?: string }>) => {
      state.currentBalance -= action.payload.amount;
      
      if (state.currentBalance < state.lowestBalance) {
        state.lowestBalance = state.currentBalance;
      }
      
      const transaction: Transaction = {
        id: `txn-${Date.now()}`,
        timestamp: Date.now(),
        type: 'loss',
        amount: action.payload.amount,
        description: action.payload.description || 'Loss',
        balance: state.currentBalance,
      };
      state.transactions.push(transaction);
      state.lastUpdated = Date.now();
    },

    // Record a buy-in
    recordBuyin: (state, action: PayloadAction<{ amount: number; description?: string }>) => {
      state.currentBalance -= action.payload.amount;
      
      if (state.currentBalance < state.lowestBalance) {
        state.lowestBalance = state.currentBalance;
      }
      
      const transaction: Transaction = {
        id: `txn-${Date.now()}`,
        timestamp: Date.now(),
        type: 'buyin',
        amount: action.payload.amount,
        description: action.payload.description || 'Table buy-in',
        balance: state.currentBalance,
      };
      state.transactions.push(transaction);
      state.lastUpdated = Date.now();
    },

    // Record a cashout
    recordCashout: (state, action: PayloadAction<{ amount: number; description?: string }>) => {
      state.currentBalance += action.payload.amount;
      
      if (state.currentBalance > state.peakBalance) {
        state.peakBalance = state.currentBalance;
      }
      
      const transaction: Transaction = {
        id: `txn-${Date.now()}`,
        timestamp: Date.now(),
        type: 'cashout',
        amount: action.payload.amount,
        description: action.payload.description || 'Table cashout',
        balance: state.currentBalance,
      };
      state.transactions.push(transaction);
      state.lastUpdated = Date.now();
    },

    // Update bankroll limits
    updateLimits: (state, action: PayloadAction<Partial<BankrollLimits>>) => {
      state.limits = { ...state.limits, ...action.payload };
      state.lastUpdated = Date.now();
    },

    // Set currency
    setCurrency: (state, action: PayloadAction<string>) => {
      state.currency = action.payload;
      state.lastUpdated = Date.now();
    },

    // Delete a transaction
    deleteTransaction: (state, action: PayloadAction<string>) => {
      const transactionIndex = state.transactions.findIndex(t => t.id === action.payload);
      if (transactionIndex !== -1) {
        state.transactions.splice(transactionIndex, 1);
        
        // Recalculate balance from transactions
        state.currentBalance = state.startingBalance;
        state.totalDeposits = state.startingBalance;
        state.totalWithdrawals = 0;
        state.peakBalance = state.startingBalance;
        state.lowestBalance = state.startingBalance;
        
        state.transactions.forEach(txn => {
          if (txn.type === 'deposit' || txn.type === 'win' || txn.type === 'cashout') {
            state.currentBalance += txn.amount;
            if (txn.type === 'deposit') {
              state.totalDeposits += txn.amount;
            }
          } else if (txn.type === 'withdrawal' || txn.type === 'loss' || txn.type === 'buyin') {
            state.currentBalance -= txn.amount;
            if (txn.type === 'withdrawal') {
              state.totalWithdrawals += txn.amount;
            }
          }
          
          if (state.currentBalance > state.peakBalance) {
            state.peakBalance = state.currentBalance;
          }
          if (state.currentBalance < state.lowestBalance) {
            state.lowestBalance = state.currentBalance;
          }
          
          txn.balance = state.currentBalance;
        });
        
        state.lastUpdated = Date.now();
      }
    },

    // Clear all transactions and reset
    resetBankroll: () => initialState,
  },
});

export const {
  initializeBankroll,
  addDeposit,
  addWithdrawal,
  recordWin,
  recordLoss,
  recordBuyin,
  recordCashout,
  updateLimits,
  setCurrency,
  deleteTransaction,
  resetBankroll,
} = bankrollSlice.actions;

export default bankrollSlice.reducer;

// Selectors
export const selectCurrentBalance = (state: { bankroll: BankrollState }) => state.bankroll.currentBalance;
export const selectProfitLoss = (state: { bankroll: BankrollState }) => 
  state.bankroll.currentBalance - state.bankroll.startingBalance;
export const selectProfitLossPercentage = (state: { bankroll: BankrollState }) => 
  state.bankroll.startingBalance > 0
    ? ((state.bankroll.currentBalance - state.bankroll.startingBalance) / state.bankroll.startingBalance) * 100
    : 0;
export const selectNetDeposits = (state: { bankroll: BankrollState }) =>
  state.bankroll.totalDeposits - state.bankroll.totalWithdrawals;

// Calculate stake recommendations based on bankroll
export const selectStakeRecommendations = (state: { bankroll: BankrollState }): StakeRecommendation => {
  const balance = state.bankroll.currentBalance;
  return {
    conservative: {
      min: balance * 0.01, // 1% of bankroll
      max: balance * 0.02, // 2% of bankroll
    },
    moderate: {
      min: balance * 0.02, // 2% of bankroll
      max: balance * 0.05, // 5% of bankroll
    },
    aggressive: {
      min: balance * 0.05, // 5% of bankroll
      max: balance * 0.10, // 10% of bankroll
    },
  };
};
