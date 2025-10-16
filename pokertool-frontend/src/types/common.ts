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
export interface WebSocketMessageData extends JsonObject {
  type?: string;
  timestamp?: number;
  [key: string]: JsonValue;
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
export interface DetectionLogData extends JsonObject {
  version?: string;
  player_id?: string;
  card?: string;
  amount?: number;
  action?: string;
  [key: string]: JsonValue;
}

/**
 * Detection log messages array
 */
export interface DetectionMessage {
  type: string;
  data: DetectionLogData;
  timestamp: string;
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
