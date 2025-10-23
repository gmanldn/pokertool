/**
 * SmartHelper Recommendation Hook
 *
 * Real-time hook for fetching and managing SmartHelper action recommendations
 * with automatic updates based on game state changes
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { PokerAction } from '../components/smarthelper/ActionRecommendationCard';
import { DecisionFactor } from '../components/smarthelper/ReasoningPanel';

export interface GTOFrequencies {
  fold?: number;
  check?: number;
  call?: number;
  bet?: number;
  raise?: number;
  all_in?: number;
}

export interface SmartHelperRecommendation {
  action: PokerAction;
  amount?: number;
  gtoFrequencies: GTOFrequencies;
  strategicReasoning: string;
  confidence: number;
  factors: DecisionFactor[];
  netConfidence: number;
  timestamp: number;
}

export interface GameState {
  // Player state
  heroCards?: string[];
  heroPosition?: string;
  heroStack?: number;

  // Table state
  communityCards?: string[];
  potSize?: number;
  betToCall?: number;
  street?: 'preflop' | 'flop' | 'turn' | 'river';

  // Opponents
  opponents?: Array<{
    name: string;
    position: string;
    stack: number;
    stats?: any;
  }>;

  // Action history
  actionHistory?: Array<{
    player: string;
    action: string;
    amount?: number;
  }>;
}

export interface UseSmartHelperRecommendationOptions {
  enabled?: boolean;
  debounceMs?: number;
  autoUpdate?: boolean;
}

export interface UseSmartHelperRecommendationResult {
  recommendation: SmartHelperRecommendation | null;
  isLoading: boolean;
  error: string | null;
  isUpdating: boolean;
  refresh: () => Promise<void>;
}

/**
 * Hook for fetching SmartHelper recommendations with real-time updates
 */
export function useSmartHelperRecommendation(
  gameState: GameState,
  options: UseSmartHelperRecommendationOptions = {}
): UseSmartHelperRecommendationResult {
  const {
    enabled = true,
    debounceMs = 300,
    autoUpdate = true
  } = options;

  const [recommendation, setRecommendation] = useState<SmartHelperRecommendation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastGameStateRef = useRef<string>('');

  /**
   * Fetch recommendation from API
   */
  const fetchRecommendation = useCallback(async (showLoading = true) => {
    if (!enabled) return;

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      if (showLoading) {
        setIsLoading(true);
      } else {
        setIsUpdating(true);
      }
      setError(null);

      const response = await fetch('/api/smarthelper/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_state: gameState,
          timestamp: Date.now()
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch recommendation: ${response.statusText}`);
      }

      const data = await response.json();
      setRecommendation(data);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('SmartHelper recommendation error:', err);
        setError(err.message || 'Failed to fetch recommendation');
      }
    } finally {
      setIsLoading(false);
      setIsUpdating(false);
    }
  }, [enabled, gameState]);

  /**
   * Debounced refresh function
   */
  const refresh = useCallback(async () => {
    await fetchRecommendation(true);
  }, [fetchRecommendation]);

  /**
   * Auto-update effect with debouncing
   */
  useEffect(() => {
    if (!enabled || !autoUpdate) return;

    // Serialize game state to detect changes
    const currentGameStateStr = JSON.stringify(gameState);

    // Skip if game state hasn't changed
    if (currentGameStateStr === lastGameStateRef.current) {
      return;
    }

    lastGameStateRef.current = currentGameStateStr;

    // Clear existing debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new debounce timer
    debounceTimerRef.current = setTimeout(() => {
      fetchRecommendation(false);
    }, debounceMs);

    // Cleanup
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [enabled, autoUpdate, gameState, debounceMs, fetchRecommendation]);

  /**
   * Initial fetch
   */
  useEffect(() => {
    if (enabled && !recommendation) {
      fetchRecommendation(true);
    }
  }, [enabled]); // Only run on mount and enabled change

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    recommendation,
    isLoading,
    error,
    isUpdating,
    refresh
  };
}

/**
 * Helper function to create mock game state for testing
 */
export function createMockGameState(): GameState {
  return {
    heroCards: ['As', 'Ks'],
    heroPosition: 'BTN',
    heroStack: 1000,
    communityCards: ['Qh', 'Jd', '9c'],
    potSize: 150,
    betToCall: 50,
    street: 'flop',
    opponents: [
      {
        name: 'Player 1',
        position: 'BB',
        stack: 800
      }
    ],
    actionHistory: [
      { player: 'BB', action: 'BET', amount: 50 }
    ]
  };
}
