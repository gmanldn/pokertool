/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/config/api.ts
version: v86.1.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created portable API configuration system
---
POKERTOOL-HEADER-END */

/**
 * Portable API Configuration
 *
 * This module provides a centralized, portable configuration system that:
 * - Auto-detects API endpoints
 * - Supports environment variable overrides
 * - Falls back to sensible defaults
 * - Supports runtime configuration file
 * - Requires no system-level changes
 *
 * Configuration Priority (highest to lowest):
 * 1. Environment variables (REACT_APP_API_URL, REACT_APP_WS_URL)
 * 2. Runtime config file (public/config.json)
 * 3. Auto-detection (relative paths)
 * 4. Hardcoded defaults (localhost)
 */

interface ApiConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  apiPort: number;
  wsPort: number;
}

interface RuntimeConfig {
  apiUrl?: string;
  wsUrl?: string;
  apiPort?: number;
  wsPort?: number;
}

// Default configuration
const DEFAULT_CONFIG: ApiConfig = {
  apiBaseUrl: 'http://localhost:5001',
  wsBaseUrl: 'http://localhost:8000',
  apiPort: 5001,
  wsPort: 8000,
};

// Cache for runtime config
let runtimeConfigCache: RuntimeConfig | null = null;
let runtimeConfigLoaded = false;

/**
 * Load runtime configuration from public/config.json
 * This allows users to customize API endpoints without rebuilding
 */
async function loadRuntimeConfig(): Promise<RuntimeConfig> {
  if (runtimeConfigLoaded) {
    return runtimeConfigCache || {};
  }

  try {
    const response = await fetch('/config.json', {
      cache: 'no-cache',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      runtimeConfigCache = await response.json();
      console.log('[Config] Loaded runtime configuration:', runtimeConfigCache);
    } else {
      console.log('[Config] No runtime config found, using defaults');
      runtimeConfigCache = {};
    }
  } catch (error) {
    console.log('[Config] Runtime config not available, using defaults');
    runtimeConfigCache = {};
  }

  runtimeConfigLoaded = true;
  return runtimeConfigCache || {};
}

/**
 * Get API base URL with auto-detection and fallbacks
 */
function getApiBaseUrl(runtimeConfig: RuntimeConfig): string {
  // 1. Check environment variable
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  // 2. Check runtime config
  if (runtimeConfig.apiUrl) {
    return runtimeConfig.apiUrl;
  }

  // 3. Try auto-detection based on current window location
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;

    // If we're not on localhost, assume API is on same host
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      const port = runtimeConfig.apiPort || DEFAULT_CONFIG.apiPort;
      return `${protocol}//${hostname}:${port}`;
    }
  }

  // 4. Fall back to default
  return DEFAULT_CONFIG.apiBaseUrl;
}

/**
 * Get WebSocket base URL with auto-detection and fallbacks
 */
function getWsBaseUrl(runtimeConfig: RuntimeConfig): string {
  // 1. Check environment variable
  if (process.env.REACT_APP_WS_URL) {
    return process.env.REACT_APP_WS_URL;
  }

  // 2. Check runtime config
  if (runtimeConfig.wsUrl) {
    return runtimeConfig.wsUrl;
  }

  // 3. Try auto-detection based on current window location
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;

    // If we're not on localhost, assume WS is on same host
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
      const port = runtimeConfig.wsPort || DEFAULT_CONFIG.wsPort;
      return `${wsProtocol}//${hostname}:${port}`;
    }
  }

  // 4. Fall back to default
  return DEFAULT_CONFIG.wsBaseUrl;
}

/**
 * Get full API configuration
 */
async function getConfig(): Promise<ApiConfig> {
  const runtimeConfig = await loadRuntimeConfig();

  return {
    apiBaseUrl: getApiBaseUrl(runtimeConfig),
    wsBaseUrl: getWsBaseUrl(runtimeConfig),
    apiPort: runtimeConfig.apiPort || DEFAULT_CONFIG.apiPort,
    wsPort: runtimeConfig.wsPort || DEFAULT_CONFIG.wsPort,
  };
}

/**
 * Synchronous config access (uses cached values)
 * Should only be used after initial load
 */
function getConfigSync(): ApiConfig {
  const runtimeConfig = runtimeConfigCache || {};

  return {
    apiBaseUrl: getApiBaseUrl(runtimeConfig),
    wsBaseUrl: getWsBaseUrl(runtimeConfig),
    apiPort: runtimeConfig.apiPort || DEFAULT_CONFIG.apiPort,
    wsPort: runtimeConfig.wsPort || DEFAULT_CONFIG.wsPort,
  };
}

/**
 * Build full API endpoint URL
 */
function buildApiUrl(path: string): string {
  const config = getConfigSync();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${config.apiBaseUrl}${cleanPath}`;
}

/**
 * Build full WebSocket URL
 */
function buildWsUrl(path: string = ''): string {
  const config = getConfigSync();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${config.wsBaseUrl}${cleanPath}`;
}

/**
 * Convert HTTP URL to WebSocket URL
 */
function httpToWs(url: string): string {
  return url.replace(/^http/, 'ws');
}

/**
 * Pre-load configuration on module import
 */
const configPromise = loadRuntimeConfig();

// Export configuration functions
export {
  getConfig,
  getConfigSync,
  buildApiUrl,
  buildWsUrl,
  httpToWs,
  configPromise,
};

// Export types
export type { ApiConfig, RuntimeConfig };

// Export default config for reference
export { DEFAULT_CONFIG };
