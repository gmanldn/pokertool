/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/types/common.ts
version: v86.5.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created common type definitions to eliminate 'any' types
---
POKERTOOL-HEADER-END */

/**
 * Common TypeScript types for the PokerTool frontend
 * Eliminates usage of 'any' types throughout the application
 */

// ============================================================================
// Generic JSON Types
// ============================================================================

/**
 * Type-safe representation of JSON values
 */
export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonObject
  | JsonArray;

export interface JsonObject {
  [key: string]: JsonValue;
}

export interface JsonArray extends Array<JsonValue> {}

// ============================================================================
// WebSocket Message Types
// ============================================================================

/**
 * Generic WebSocket message structure
 */
export interface WebSocketMessageData {
  type?: string;
  timestamp?: number;
  [key: string]: JsonValue | undefined;
}

/**
 * Chart.js context types for tooltip/label callbacks
 */
export interface ChartTooltipContext {
  chart: unknown;
  label?: string;
  parsed: {
    x: number;
    y: number;
  };
  raw: number;
  formattedValue: string;
  dataset: {
    label?: string;
    data: number[];
  };
  dataIndex: number;
  datasetIndex: number;
}

export interface ChartScaleContext {
  chart: unknown;
  scale: {
    id: string;
    type: string;
  };
  index: number;
  tick: {
    value: number;
    label?: string;
  };
}

// ============================================================================
// Detection Log Types
// ============================================================================

/**
 * Detection log entry data
 */
export interface DetectionLogData {
  version?: string;
  player_id?: string;
  card?: string;
  amount?: number;
  action?: string;
  [key: string]: JsonValue | undefined;
}

/**
 * Detection log messages array
 */
export interface DetectionMessage {
  type: string;
  data: DetectionLogData;
  timestamp: number;  // Changed from string to match WebSocketMessage
  severity?: 'info' | 'success' | 'warning' | 'error';
  message?: string;
}

// ============================================================================
// React Component Prop Types
// ============================================================================

/**
 * Generic card component props
 */
export interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: string;
}

/**
 * Table view send message function type
 */
export type SendMessageFunction = (message: WebSocketMessageData | string) => void;

// ============================================================================
// Specific Message Data Types
// ============================================================================

/**
 * Advice data from backend
 */
export interface Advice extends WebSocketMessageData {
  action: string;
  confidence: string;
  confidenceScore: number;
  ev: number;
  reasoning: string;
  situation: string;
  alternatives?: Array<{ action: string; ev: number }>;
}

/**
 * Alternative actions data
 */
export interface AlternativeActionsData extends WebSocketMessageData {
  primaryEV: number;
  alternatives: Array<{
    action: string;
    ev: number;
    confidence?: number;
    viable?: boolean;
  }>;
}

/**
 * Table data for table view
 * Note: Does not extend WebSocketMessageData due to Player[] array incompatibility with JsonValue
 */
export interface TableData {
  type?: string;
  timestamp?: number;
  tableId: string;
  tableName: string;
  players: Player[];
  pot: number;
  communityCards: string[];
  currentAction?: string;
  dealer?: number;
  smallBlind?: number;
  bigBlind?: number;
}

/**
 * Player data
 */
export interface Player {
  seat: number;
  name: string;
  chips: number;
  cards?: string[];
  isActive: boolean;
  isFolded: boolean;
  currentBet?: number;
  isDealer?: boolean;
}

// Type guards for narrowing WebSocketMessageData
export function isAdvice(data: WebSocketMessageData): data is Advice {
  return (
    typeof data === 'object' &&
    'action' in data &&
    'confidence' in data &&
    'confidenceScore' in data
  );
}

export function isAlternativeActionsData(
  data: WebSocketMessageData
): data is AlternativeActionsData {
  return (
    typeof data === 'object' &&
    'primaryEV' in data &&
    'alternatives' in data &&
    Array.isArray((data as AlternativeActionsData).alternatives)
  );
}

export function isTableData(data: unknown): data is TableData {
  return (
    typeof data === 'object' &&
    data !== null &&
    'tableId' in data &&
    'tableName' in data &&
    'players' in data
  );
}
