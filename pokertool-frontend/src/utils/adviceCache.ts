/**
 * LRU Cache for poker advice with game state similarity matching
 * Reduces backend load by caching similar game states
 */

interface GameState {
  potSize: number;
  heroCards: string;
  boardCards: string;
  position: string;
  street: 'PREFLOP' | 'FLOP' | 'TURN' | 'RIVER';
  stackSize: number;
  numPlayers: number;
  toCall: number;
}

interface CachedAdvice {
  action: 'FOLD' | 'CALL' | 'RAISE' | 'CHECK' | 'ALL-IN';
  amount?: number;
  confidence: number;
  ev: number;
  reasoning: string;
  timestamp: number;
  gameStateHash: string;
}

interface CacheEntry {
  gameState: GameState;
  advice: CachedAdvice;
  accessCount: number;
  lastAccessed: number;
}

interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  hitRate: number;
  avgLookupTime: number;
}

export class AdviceCache {
  private cache: Map<string, CacheEntry>;
  private maxSize: number;
  private stats: CacheStats;
  private lookupTimes: number[];
  private readonly SIMILARITY_THRESHOLD = 0.85;
  private readonly CACHE_TTL = 300000; // 5 minutes

  constructor(maxSize: number = 100) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.stats = {
      hits: 0,
      misses: 0,
      size: 0,
      hitRate: 0,
      avgLookupTime: 0
    };
    this.lookupTimes = [];
  }

  /**
   * Generate a hash for a game state
   */
  private hashGameState(state: GameState): string {
    const normalized = {
      pot: Math.round(state.potSize / 5) * 5, // Round to nearest $5
      cards: this.normalizeCards(state.heroCards),
      board: this.normalizeCards(state.boardCards),
      position: state.position,
      street: state.street,
      stack: Math.round(state.stackSize / 10) * 10, // Round to nearest $10
      players: state.numPlayers,
      call: Math.round(state.toCall / 5) * 5
    };

    return JSON.stringify(normalized);
  }

  /**
   * Normalize card representation (e.g., AhKs -> AK)
   */
  private normalizeCards(cards: string): string {
    if (!cards) return '';
    // Extract just ranks and suits, normalize order
    return cards
      .replace(/[♠♣♥♦]/g, '')
      .split('')
      .sort()
      .join('');
  }

  /**
   * Calculate similarity between two game states (0-1)
   */
  private calculateSimilarity(state1: GameState, state2: GameState): number {
    let score = 0;
    let weights = 0;

    // Exact matches
    if (state1.street === state2.street) {
      score += 0.2;
    }
    weights += 0.2;

    if (state1.position === state2.position) {
      score += 0.15;
    }
    weights += 0.15;

    if (state1.numPlayers === state2.numPlayers) {
      score += 0.1;
    }
    weights += 0.1;

    // Normalize cards for comparison
    if (this.normalizeCards(state1.heroCards) === this.normalizeCards(state2.heroCards)) {
      score += 0.25;
    }
    weights += 0.25;

    if (this.normalizeCards(state1.boardCards) === this.normalizeCards(state2.boardCards)) {
      score += 0.15;
    }
    weights += 0.15;

    // Numeric similarity (within 20% tolerance)
    const potSimilarity = 1 - Math.abs(state1.potSize - state2.potSize) / Math.max(state1.potSize, state2.potSize);
    if (potSimilarity > 0.8) {
      score += 0.08 * potSimilarity;
    }
    weights += 0.08;

    const stackSimilarity = 1 - Math.abs(state1.stackSize - state2.stackSize) / Math.max(state1.stackSize, state2.stackSize);
    if (stackSimilarity > 0.8) {
      score += 0.05 * stackSimilarity;
    }
    weights += 0.05;

    const callSimilarity = state1.toCall === 0 && state2.toCall === 0 ? 1 : 
      1 - Math.abs(state1.toCall - state2.toCall) / Math.max(state1.toCall, state2.toCall, 1);
    if (callSimilarity > 0.8) {
      score += 0.02 * callSimilarity;
    }
    weights += 0.02;

    return score / weights;
  }

  /**
   * Find cached advice for similar game state
   */
  get(state: GameState): CachedAdvice | null {
    const startTime = performance.now();
    const hash = this.hashGameState(state);

    // Try exact match first
    if (this.cache.has(hash)) {
      const entry = this.cache.get(hash)!;
      
      // Check if entry is still fresh
      if (Date.now() - entry.advice.timestamp < this.CACHE_TTL) {
        entry.accessCount++;
        entry.lastAccessed = Date.now();
        this.stats.hits++;
        this.recordLookupTime(performance.now() - startTime);
        return { ...entry.advice, cached: true, exact: true } as any;
      } else {
        // Expired entry
        this.cache.delete(hash);
      }
    }

    // Try similarity match
    for (const [cachedHash, entry] of Array.from(this.cache.entries())) {
      const similarity = this.calculateSimilarity(state, entry.gameState);
      
      if (similarity >= this.SIMILARITY_THRESHOLD) {
        // Check freshness
        if (Date.now() - entry.advice.timestamp < this.CACHE_TTL) {
          entry.accessCount++;
          entry.lastAccessed = Date.now();
          this.stats.hits++;
          this.recordLookupTime(performance.now() - startTime);
          return { 
            ...entry.advice, 
            cached: true, 
            exact: false, 
            similarity 
          } as any;
        }
      }
    }

    this.stats.misses++;
    this.recordLookupTime(performance.now() - startTime);
    return null;
  }

  /**
   * Store advice in cache
   */
  set(state: GameState, advice: Omit<CachedAdvice, 'timestamp' | 'gameStateHash'>): void {
    const hash = this.hashGameState(state);
    
    // Evict if at capacity
    if (this.cache.size >= this.maxSize && !this.cache.has(hash)) {
      this.evictLRU();
    }

    const cachedAdvice: CachedAdvice = {
      ...advice,
      timestamp: Date.now(),
      gameStateHash: hash
    };

    this.cache.set(hash, {
      gameState: state,
      advice: cachedAdvice,
      accessCount: 0,
      lastAccessed: Date.now()
    });

    this.updateStats();
  }

  /**
   * Evict least recently used entry
   */
  private evictLRU(): void {
    let oldestTime = Infinity;
    let oldestKey = '';

    for (const [key, entry] of Array.from(this.cache.entries())) {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  /**
   * Invalidate entries matching criteria
   */
  invalidate(criteria: Partial<GameState>): number {
    let count = 0;

    for (const [hash, entry] of Array.from(this.cache.entries())) {
      let shouldInvalidate = false;

      if (criteria.street && entry.gameState.street !== criteria.street) {
        shouldInvalidate = true;
      }
      if (criteria.position && entry.gameState.position !== criteria.position) {
        shouldInvalidate = true;
      }
      if (criteria.numPlayers && entry.gameState.numPlayers !== criteria.numPlayers) {
        shouldInvalidate = true;
      }

      if (shouldInvalidate) {
        this.cache.delete(hash);
        count++;
      }
    }

    this.updateStats();
    return count;
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.stats = {
      hits: 0,
      misses: 0,
      size: 0,
      hitRate: 0,
      avgLookupTime: 0
    };
    this.lookupTimes = [];
  }

  /**
   * Remove expired entries
   */
  cleanupExpired(): number {
    const now = Date.now();
    let count = 0;

    for (const [hash, entry] of Array.from(this.cache.entries())) {
      if (now - entry.advice.timestamp > this.CACHE_TTL) {
        this.cache.delete(hash);
        count++;
      }
    }

    this.updateStats();
    return count;
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Update statistics
   */
  private updateStats(): void {
    this.stats.size = this.cache.size;
    const total = this.stats.hits + this.stats.misses;
    this.stats.hitRate = total > 0 ? (this.stats.hits / total) * 100 : 0;
    this.stats.avgLookupTime = this.lookupTimes.length > 0
      ? this.lookupTimes.reduce((a, b) => a + b, 0) / this.lookupTimes.length
      : 0;
  }

  /**
   * Record lookup time for performance tracking
   */
  private recordLookupTime(time: number): void {
    this.lookupTimes.push(time);
    // Keep only last 100 measurements
    if (this.lookupTimes.length > 100) {
      this.lookupTimes.shift();
    }
    this.updateStats();
  }

  /**
   * Get cache entries sorted by access count
   */
  getMostAccessed(limit: number = 10): Array<{ hash: string; count: number; advice: CachedAdvice }> {
    return Array.from(this.cache.entries())
      .sort((a, b) => b[1].accessCount - a[1].accessCount)
      .slice(0, limit)
      .map(([hash, entry]) => ({
        hash,
        count: entry.accessCount,
        advice: entry.advice
      }));
  }
}

// Global singleton instance
let globalCache: AdviceCache | null = null;

export function getAdviceCache(): AdviceCache {
  if (!globalCache) {
    globalCache = new AdviceCache(100);
    
    // Setup periodic cleanup
    setInterval(() => {
      const removed = globalCache!.cleanupExpired();
      if (removed > 0) {
        console.log(`[AdviceCache] Cleaned up ${removed} expired entries`);
      }
    }, 60000); // Every minute
  }
  return globalCache;
}

/**
 * Smooth interpolation between cached and fresh advice
 */
export function interpolateAdvice(
  cached: CachedAdvice,
  fresh: CachedAdvice,
  factor: number = 0.3
): CachedAdvice {
  // Interpolate numeric values
  const interpolated: CachedAdvice = {
    action: fresh.action, // Use fresh action
    amount: cached.amount && fresh.amount 
      ? Math.round(cached.amount * (1 - factor) + fresh.amount * factor)
      : fresh.amount,
    confidence: Math.round(cached.confidence * (1 - factor) + fresh.confidence * factor),
    ev: cached.ev * (1 - factor) + fresh.ev * factor,
    reasoning: fresh.reasoning, // Use fresh reasoning
    timestamp: fresh.timestamp,
    gameStateHash: fresh.gameStateHash
  };

  return interpolated;
}

export default AdviceCache;
