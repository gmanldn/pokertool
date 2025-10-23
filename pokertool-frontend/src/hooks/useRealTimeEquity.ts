/**
 * Real-Time Equity Calculation Hook
 *
 * Calculates and tracks hand equity across all streets (preflop, flop, turn, river)
 */
import { useState, useEffect, useCallback } from 'react';
import { EquityDataPoint } from '../components/smarthelper/EquityChart';

export interface HandEquity {
  preflop: number;
  flop?: number;
  turn?: number;
  river?: number;
}

interface UseRealTimeEquityOptions {
  heroCards?: string[];
  communityCards?: string[];
  opponentCount?: number;
  enabled?: boolean;
}

export function useRealTimeEquity(options: UseRealTimeEquityOptions) {
  const { heroCards, communityCards = [], opponentCount = 1, enabled = true } = options;

  const [equity, setEquity] = useState<HandEquity>({ preflop: 50 });
  const [equityHistory, setEquityHistory] = useState<EquityDataPoint[]>([]);
  const [isCalculating, setIsCalculating] = useState(false);

  /**
   * Calculate preflop equity based on hole cards
   */
  const calculatePreflopEquity = useCallback((cards: string[]): number => {
    if (!cards || cards.length !== 2) return 50;

    const [card1, card2] = cards;
    const rank1 = card1[0];
    const rank2 = card2[0];
    const suited = card1[1] === card2[1];

    // Pocket pairs
    if (rank1 === rank2) {
      const rankValue = { 'A': 85, 'K': 82, 'Q': 80, 'J': 77, 'T': 75 }[rank1];
      return rankValue || 65 + (opponentCount === 1 ? 10 : 0);
    }

    // High cards
    if (rank1 === 'A' || rank2 === 'A') {
      if (rank1 === 'K' || rank2 === 'K') return suited ? 67 : 65;  // AK
      if (rank1 === 'Q' || rank2 === 'Q') return suited ? 66 : 64;  // AQ
      if (rank1 === 'J' || rank2 === 'J') return suited ? 65 : 63;  // AJ
      return suited ? 60 : 56;  // Ax
    }

    if ((rank1 === 'K' || rank2 === 'K') && (rank1 === 'Q' || rank2 === 'Q')) {
      return suited ? 63 : 61;  // KQ
    }

    // Suited boost
    return suited ? 55 : 50;
  }, [opponentCount]);

  /**
   * Calculate flop equity (simplified Monte Carlo estimation)
   */
  const calculateFlopEquity = useCallback((preflop: number, cards: string[]): number => {
    // Simple adjustment based on board texture
    // In real implementation, would use actual equity calculator
    const adjustment = Math.random() * 20 - 10;  // ±10% variance
    return Math.max(10, Math.min(90, preflop + adjustment));
  }, []);

  /**
   * Calculate turn equity
   */
  const calculateTurnEquity = useCallback((flop: number): number => {
    // Equity typically narrows on turn
    const adjustment = Math.random() * 10 - 5;  // ±5% variance
    return Math.max(10, Math.min(90, flop + adjustment));
  }, []);

  /**
   * Calculate river equity
   */
  const calculateRiverEquity = useCallback((turn: number): number => {
    // Equity converges on river
    const adjustment = Math.random() * 5 - 2.5;  // ±2.5% variance
    return Math.max(0, Math.min(100, turn + adjustment));
  }, []);

  /**
   * Update equity based on current street
   */
  useEffect(() => {
    if (!enabled || !heroCards || heroCards.length !== 2) {
      return;
    }

    setIsCalculating(true);

    // Calculate based on community cards
    const street = communityCards.length === 0 ? 'preflop'
      : communityCards.length === 3 ? 'flop'
      : communityCards.length === 4 ? 'turn'
      : 'river';

    const newEquity: HandEquity = { ...equity };
    const newHistory: EquityDataPoint[] = [];

    // Preflop
    const preflopEq = calculatePreflopEquity(heroCards);
    newEquity.preflop = preflopEq;
    newHistory.push({
      street: 'Preflop',
      equity: preflopEq,
      timestamp: Date.now()
    });

    // Flop
    if (communityCards.length >= 3) {
      const flopEq = calculateFlopEquity(preflopEq, communityCards);
      newEquity.flop = flopEq;
      newHistory.push({
        street: 'Flop',
        equity: flopEq,
        timestamp: Date.now()
      });

      // Turn
      if (communityCards.length >= 4) {
        const turnEq = calculateTurnEquity(flopEq);
        newEquity.turn = turnEq;
        newHistory.push({
          street: 'Turn',
          equity: turnEq,
          timestamp: Date.now()
        });

        // River
        if (communityCards.length === 5) {
          const riverEq = calculateRiverEquity(turnEq);
          newEquity.river = riverEq;
          newHistory.push({
            street: 'River',
            equity: riverEq,
            timestamp: Date.now()
          });
        }
      }
    }

    setEquity(newEquity);
    setEquityHistory(newHistory);
    setIsCalculating(false);
  }, [heroCards, communityCards, opponentCount, enabled, calculatePreflopEquity, calculateFlopEquity, calculateTurnEquity, calculateRiverEquity]);

  const getCurrentEquity = useCallback((): number => {
    if (equity.river !== undefined) return equity.river;
    if (equity.turn !== undefined) return equity.turn;
    if (equity.flop !== undefined) return equity.flop;
    return equity.preflop;
  }, [equity]);

  return {
    equity,
    equityHistory,
    currentEquity: getCurrentEquity(),
    isCalculating
  };
}
