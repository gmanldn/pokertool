/**
 * Session Persistence Utility
 * Saves and restores application state to/from localStorage
 */

interface SessionData {
  timestamp: number;
  tableState?: any;
  detectionStats?: any;
  userPreferences?: any;
}

const SESSION_KEY = 'pokertool_session';
const MAX_SESSION_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

export const sessionPersistence = {
  /**
   * Save current session data to localStorage
   */
  saveSession(data: Partial<SessionData>): void {
    try {
      const existing = this.loadSession();
      const updated: SessionData = {
        ...existing,
        ...data,
        timestamp: Date.now(),
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  },

  /**
   * Load session data from localStorage
   */
  loadSession(): SessionData | null {
    try {
      const stored = localStorage.getItem(SESSION_KEY);
      if (!stored) return null;

      const data: SessionData = JSON.parse(stored);
      
      // Check if session is too old
      if (Date.now() - data.timestamp > MAX_SESSION_AGE_MS) {
        this.clearSession();
        return null;
      }

      return data;
    } catch (error) {
      console.error('Failed to load session:', error);
      return null;
    }
  },

  /**
   * Clear stored session
   */
  clearSession(): void {
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (error) {
      console.error('Failed to clear session:', error);
    }
  },

  /**
   * Check if there's a valid stored session
   */
  hasValidSession(): boolean {
    const session = this.loadSession();
    return session !== null;
  },
};
