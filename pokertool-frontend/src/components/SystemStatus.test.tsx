/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/SystemStatus.test.tsx
version: v86.3.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created comprehensive unit tests for SystemStatus component
---
POKERTOOL-HEADER-END */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SystemStatus } from './SystemStatus';
import { buildApiUrl, httpToWs } from '../config/api';

// Mock the config functions
jest.mock('../config/api', () => ({
  buildApiUrl: jest.fn((path: string) => `http://localhost:5001${path}`),
  httpToWs: jest.fn((url: string) => url.replace('http://', 'ws://').replace('https://', 'wss://')),
}));

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((error: Event) => void) | null = null;
  onclose: (() => void) | null = null;

  static instances: MockWebSocket[] = [];

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }

  send(data: string) {}
  close() {
    if (this.onclose) this.onclose();
  }
}

global.WebSocket = MockWebSocket as any;

// Mock fetch
global.fetch = jest.fn();

const mockTrendsResponse = {
  success: true,
  timestamp: '2025-10-16T12:00:00Z',
  trends: {
    period_hours: 24,
    data_points: 4,
    start_time: '2025-10-15T12:00:00Z',
    end_time: '2025-10-16T12:00:00Z',
    summary: 'Analyzed 4 data points over 24 hours',
    feature_trends: {
      ocr_engine: {
        healthy: 1,
        degraded: 2,
        failing: 1,
        unknown: 0,
        healthy_pct: 25,
        degraded_pct: 50,
        failing_pct: 25,
        avg_latency_ms: 45.8,
      },
      neural_evaluator: {
        healthy: 0,
        degraded: 1,
        failing: 3,
        unknown: 0,
        healthy_pct: 0,
        degraded_pct: 25,
        failing_pct: 75,
        avg_latency_ms: null,
      },
    },
  },
};

const mockHistoryResponse = {
  success: true,
  timestamp: '2025-10-16T12:05:00Z',
  period_hours: 24,
  data_points: 2,
  history: [
    {
      timestamp: '2025-10-16T12:00:00Z',
      results: {
        ocr_engine: {
          feature_name: 'ocr_engine',
          category: 'scraping',
          status: 'degraded' as const,
          last_check: '2025-10-16T12:00:00Z',
        },
        neural_evaluator: {
          feature_name: 'neural_evaluator',
          category: 'ml',
          status: 'failing' as const,
          last_check: '2025-10-16T12:00:00Z',
        },
        model_calibration: {
          feature_name: 'model_calibration',
          category: 'backend',
          status: 'healthy' as const,
          last_check: '2025-10-16T12:00:00Z',
        },
      },
    },
    {
      timestamp: '2025-10-16T11:30:00Z',
      results: {
        ocr_engine: {
          feature_name: 'ocr_engine',
          category: 'scraping',
          status: 'healthy' as const,
          last_check: '2025-10-16T11:30:00Z',
        },
        neural_evaluator: {
          feature_name: 'neural_evaluator',
          category: 'ml',
          status: 'degraded' as const,
          last_check: '2025-10-16T11:30:00Z',
        },
      },
    },
  ],
};

const createFetchResponse = (data: unknown) => ({
  ok: true,
  json: async () => data,
});

const mockSuccessfulFetch = (overrides?: {
  health?: typeof mockHealthData;
  trends?: typeof mockTrendsResponse;
  history?: typeof mockHistoryResponse;
}) => {
  const healthPayload = overrides?.health ?? mockHealthData;
  const trendPayload = overrides?.trends ?? mockTrendsResponse;
  const historyPayload = overrides?.history ?? mockHistoryResponse;

  (global.fetch as jest.Mock).mockImplementation((input: RequestInfo) => {
    const url = typeof input === 'string' ? input : input.url;

    if (url.includes('/api/system/health/trends')) {
      return Promise.resolve(createFetchResponse(trendPayload));
    }

    if (url.includes('/api/system/health/history')) {
      return Promise.resolve(createFetchResponse(historyPayload));
    }

    if (url.includes('/api/system/health')) {
      return Promise.resolve(createFetchResponse(healthPayload));
    }

    return Promise.resolve(createFetchResponse({}));
  });
};

const findChipButton = (label: RegExp | string): HTMLButtonElement => {
  const pattern = typeof label === 'string' ? new RegExp(`^${label}$`, 'i') : label;
  const buttons = screen.getAllByRole('button');
  for (const button of buttons) {
    const text = button.textContent?.trim() ?? '';
    if (pattern.test(text)) {
      return button as HTMLButtonElement;
    }
  }
  throw new Error(`Chip with label ${label} not found`);
};

const mockHealthData = {
  timestamp: '2025-10-16T12:00:00Z',
  overall_status: 'healthy',
  failing_count: 0,
  degraded_count: 0,
  categories: {
    backend: {
      status: 'healthy',
      checks: [
        {
          feature_name: 'model_calibration',
          category: 'backend',
          status: 'healthy' as const,
          last_check: '2025-10-16T12:00:00Z',
          latency_ms: 10.5,
          description: 'Model calibration system health check',
        },
        {
          feature_name: 'gto_solver',
          category: 'backend',
          status: 'healthy' as const,
          last_check: '2025-10-16T12:00:00Z',
          latency_ms: 15.2,
          description: 'GTO solver engine health check',
        },
      ],
    },
    scraping: {
      status: 'degraded',
      checks: [
        {
          feature_name: 'ocr_engine',
          category: 'scraping',
          status: 'degraded' as const,
          last_check: '2025-10-16T12:00:00Z',
          latency_ms: 45.8,
          error_message: 'OCR performance degraded',
          description: 'OCR engine health check',
        },
      ],
    },
    ml: {
      status: 'failing',
      checks: [
        {
          feature_name: 'neural_evaluator',
          category: 'ml',
          status: 'failing' as const,
          last_check: '2025-10-16T12:00:00Z',
          error_message: 'Model initialization failed',
          description: 'Neural network evaluator health check',
        },
      ],
    },
  },
};

describe('SystemStatus Component', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockReset();
    (buildApiUrl as jest.Mock).mockImplementation((path: string) => `http://localhost:5001${path}`);
    jest.clearAllTimers();
    localStorage.clear();
    MockWebSocket.instances = [];
  });

  describe('Initial Render and Data Fetching', () => {
    it('should render loading state initially', async () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<SystemStatus />);

      expect(await screen.findByTestId('system-status-skeleton-heading')).toBeInTheDocument();
    });

    it('should fetch health data on mount', async () => {
      mockSuccessfulFetch();

      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      const calledUrls = (global.fetch as jest.Mock).mock.calls.map(([url]) =>
        typeof url === 'string' ? url : (url as Request).url
      );
      expect(calledUrls).toEqual(expect.arrayContaining([
        'http://localhost:5001/api/system/health',
        'http://localhost:5001/api/system/health/trends?hours=24',
        'http://localhost:5001/api/system/health/history?hours=24',
      ]));
      expect(global.fetch).toHaveBeenCalled();
    });

    it('should display health data after successful fetch', async () => {
      mockSuccessfulFetch();

      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      expect(screen.getByLabelText('Overall system status: healthy')).toBeInTheDocument();
    });

    it('should display error message when fetch fails', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Failed to connect to backend. Is the server running?')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Overall Status Summary', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should display overall status', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      expect(screen.getByLabelText('Overall system status: healthy')).toBeInTheDocument();
      const summary = screen.getByLabelText('System health summary');
      expect(within(summary).getByText('Overall Status')).toBeInTheDocument();
    });

    it('should display counts for healthy, degraded, and failing features', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      const summary = screen.getByLabelText('System health summary');
      expect(within(summary).getAllByText('Healthy')[0]).toBeInTheDocument();
      expect(within(summary).getAllByText('Degraded')[0]).toBeInTheDocument();
      expect(within(summary).getAllByText('Failing')[0]).toBeInTheDocument();
    });

    it('should calculate correct healthy count', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      const summary = screen.getByLabelText('System health summary');
      const healthySection = within(summary).getAllByText('Healthy')[0].parentElement;
      expect(within(healthySection!).getAllByText('2')[0]).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should filter health checks by search query', async () => {
      render(<SystemStatus />);

      await screen.findByText('Model Calibration');

      const searchInput = screen.getByPlaceholderText('Search features...');
      fireEvent.change(searchInput, { target: { value: 'ocr' } });

      await waitFor(() => {
        const ocrEngines = screen.queryAllByText('Ocr Engine');
        expect(ocrEngines.length).toBeGreaterThan(0);
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
      });
    });

    it('should show no results message when search has no matches', async () => {
      render(<SystemStatus />);

      await screen.findByText('Model Calibration');

      const searchInput = screen.getByPlaceholderText('Search features...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await screen.findByText('No features found matching your criteria');
    });

    it('should clear filters when clicking Clear Filters button', async () => {
      render(<SystemStatus />);

      await screen.findByText('Model Calibration');

      const searchInput = screen.getByPlaceholderText('Search features...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await screen.findByText('Clear Filters');

      const clearButton = screen.getByText('Clear Filters');
      fireEvent.click(clearButton);

      await screen.findByText('Model Calibration');
    });
  });

  describe('Filter Functionality', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should filter by healthy status', async () => {
      render(<SystemStatus />);

      await screen.findByText('Model Calibration');

      const healthyChip = findChipButton(/HEALTHY/i);
      fireEvent.click(healthyChip);

      await waitFor(() => {
        expect(screen.getAllByText('Model Calibration')[0]).toBeInTheDocument();
        expect(screen.getAllByText('Gto Solver')[0]).toBeInTheDocument();
        // Check in cards section specifically - Ocr Engine might still be in trends
        const cards = screen.queryAllByRole('article');
        const ocrCard = cards.find(card => card.textContent?.includes('Ocr Engine'));
        expect(ocrCard).toBeUndefined();
      });
    });

    it('should filter by failing status', async () => {
      render(<SystemStatus />);

      await screen.findByText('Model Calibration');

      const failingChip = findChipButton(/FAILING/i);
      fireEvent.click(failingChip);

      await waitFor(() => {
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
        const neuralEvaluators = screen.getAllByText('Neural Evaluator');
        expect(neuralEvaluators.length).toBeGreaterThan(0);
      });
    });

    it('should filter by degraded status', async () => {
      render(<SystemStatus />);

      await screen.findByText('Model Calibration');

      const degradedChip = findChipButton(/DEGRADED/i);
      fireEvent.click(degradedChip);

      await waitFor(() => {
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
        const ocrEngines = screen.getAllByText('Ocr Engine');
        expect(ocrEngines.length).toBeGreaterThan(0);
      });
    });

    it('should show all features when ALL filter is selected', async () => {
      render(<SystemStatus />);

      await screen.findByText('Model Calibration');

      // First filter to something specific
      const appliedFailingChip = findChipButton(/FAILING/i);
      fireEvent.click(appliedFailingChip);

      await waitFor(() => {
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
      });

      // Then click ALL
      const allChip = findChipButton(/ALL/i);
      fireEvent.click(allChip);

      await waitFor(() => {
        expect(screen.getAllByText('Model Calibration')[0]).toBeInTheDocument();
        expect(screen.getAllByText('Ocr Engine').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Neural Evaluator').length).toBeGreaterThan(0);
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refetch data when refresh button is clicked', async () => {
      const responses = [
        createFetchResponse(mockHealthData),
        createFetchResponse(mockTrendsResponse),
        createFetchResponse(mockHistoryResponse),
        createFetchResponse({ ...mockHealthData, overall_status: 'degraded' }),
        createFetchResponse(mockTrendsResponse),
        createFetchResponse(mockHistoryResponse),
      ];

      (global.fetch as jest.Mock).mockImplementation(() => {
        const next = responses.shift();
        if (!next) {
          return Promise.resolve(createFetchResponse({}));
        }
        return Promise.resolve(next);
      });

      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');

      const refreshButton = screen.getByRole('button', { name: /refresh all health checks/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(6);
        expect(screen.getAllByText('DEGRADED')[0]).toBeInTheDocument();
      });
    });

    it('should show refreshing state while fetching', async () => {
      const pending = new Promise(() => {});
      const responses: Array<any> = [
        createFetchResponse(mockHealthData),
        createFetchResponse(mockTrendsResponse),
        createFetchResponse(mockHistoryResponse),
        pending,
        createFetchResponse(mockTrendsResponse),
        createFetchResponse(mockHistoryResponse),
      ];

      (global.fetch as jest.Mock).mockImplementation(() => {
        const next = responses.shift();
        if (!next) {
          return Promise.resolve(createFetchResponse({}));
        }
        if (typeof (next as any).then === 'function') {
          return next as Promise<any>;
        }
        return Promise.resolve(next);
      });

      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');

      const refreshButton = screen.getByRole('button', { name: /refresh all health checks/i });
      fireEvent.click(refreshButton);

      // Should show spinner while refreshing
      await waitFor(() => {
        const buttons = screen.getAllByRole('button', { name: /refresh all health checks/i });
        expect(buttons[0]).toBeDisabled();
      });
    });
  });

  describe('Trend Analytics', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should display watchlist and recent samples', async () => {
      render(<SystemStatus />);

      await screen.findByText('Health Trends');
      expect(screen.getAllByText(/Watchlist \(Top 6 by failure rate\)/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/Healthy uptime: 25\.0%/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/Recent samples/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/Healthy:/i)[0]).toHaveTextContent(/Healthy: 1/i);
    });

    it('should refetch trends when changing window', async () => {
      render(<SystemStatus />);

      await screen.findByText('Health Trends');

      const windowSelect = screen.getByLabelText(/select health trend window/i);
      fireEvent.change(windowSelect, { target: { value: '48' } });

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls.map(([url]) =>
          typeof url === 'string' ? url : (url as Request).url
        );
        expect(calls).toContain('http://localhost:5001/api/system/health/trends?hours=48');
        expect(calls).toContain('http://localhost:5001/api/system/health/history?hours=48');
      });
    });
  });

  describe('Real-time updates', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should update status when websocket pushes new data', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      const socket = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      expect(socket).toBeDefined();

      const failingUpdate = {
        ...mockHealthData,
        timestamp: '2025-10-16T12:05:00Z',
        overall_status: 'failing' as const,
        failing_count: 2,
        degraded_count: 1,
      };

      socket?.onmessage?.({ data: JSON.stringify(failingUpdate) } as MessageEvent);

      await waitFor(() => {
        expect(screen.getAllByText('FAILING')[0]).toBeInTheDocument();
        expect(screen.getByLabelText('Overall system status: failing')).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    let createdAnchors: HTMLAnchorElement[] = [];

    beforeEach(() => {
      mockSuccessfulFetch();

      createdAnchors = [];

      global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
      global.URL.revokeObjectURL = jest.fn();

      const originalCreateElement = Document.prototype.createElement;
      jest.spyOn(document, 'createElement').mockImplementation(((tagName: string, options?: ElementCreationOptions) => {
        const element = originalCreateElement.call(document, tagName, options);
        if (tagName.toLowerCase() === 'a') {
          const anchor = element as HTMLAnchorElement;
          anchor.click = jest.fn();
          createdAnchors.push(anchor);
        }
        return element;
      }) as typeof document.createElement);
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    it('should export health data as JSON when export option is selected', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');

      const exportButton = screen.getByRole('button', { name: /open export menu/i });
      fireEvent.click(exportButton);

      const jsonOption = await screen.findByRole('menuitem', { name: /export as json/i });
      fireEvent.click(jsonOption);

      await waitFor(() => {
        expect(global.URL.createObjectURL).toHaveBeenCalled();
        expect(global.URL.revokeObjectURL).toHaveBeenCalled();
      });

      expect(createdAnchors).toHaveLength(1);
      expect(createdAnchors[0].download).toMatch(/\.json$/);
      expect(createdAnchors[0].click).toHaveBeenCalled();
    });

    it('should export health data as CSV when export option is selected', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');

      const exportButton = screen.getByRole('button', { name: /open export menu/i });
      fireEvent.click(exportButton);

      const csvOption = await screen.findByRole('menuitem', { name: /export as csv/i });
      fireEvent.click(csvOption);

      await waitFor(() => {
        expect(global.URL.createObjectURL).toHaveBeenCalled();
        expect(global.URL.revokeObjectURL).toHaveBeenCalled();
      });

      const csvAnchor = createdAnchors[createdAnchors.length - 1];
      expect(csvAnchor.download).toMatch(/\.csv$/);
      expect(csvAnchor.click).toHaveBeenCalled();
    });
  });

  describe('Card Expansion', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should expand card to show error details when expand button is clicked', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');

      // Error message should not be visible initially
      expect(screen.queryByText('OCR performance degraded')).not.toBeInTheDocument();

      // Find all cards and locate the one with OCR Engine
      const cards = screen.getAllByRole('article');
      const ocrCard = cards.find(card => card.textContent?.includes('Ocr Engine'));
      expect(ocrCard).toBeDefined();
      
      const expandButton = within(ocrCard as HTMLElement).getByRole('button');
      fireEvent.click(expandButton);

      await waitFor(() => {
        expect(screen.getAllByText('OCR performance degraded')[0]).toBeInTheDocument();
      });
    });

    it('should collapse card when expand button is clicked again', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');

      const cards = screen.getAllByRole('article');
      const ocrCard = cards.find(card => card.textContent?.includes('Ocr Engine'));
      expect(ocrCard).toBeDefined();
      
      const expandButton = within(ocrCard as HTMLElement).getByRole('button');

      // Expand
      fireEvent.click(expandButton);
      await waitFor(() => {
        expect(screen.getAllByText('OCR performance degraded')[0]).toBeInTheDocument();
      });

      // Collapse
      fireEvent.click(expandButton);
      await waitFor(() => {
        expect(screen.queryByText('OCR performance degraded')).not.toBeInTheDocument();
      });
    });
  });

  describe('Category Display', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should display correct category names', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      expect(screen.getByText(/Backend Core/i)).toBeInTheDocument();
      expect(screen.getByText(/Screen Scraping/i)).toBeInTheDocument();
      expect(screen.getByText(/ML\/Analytics/i)).toBeInTheDocument();
    });

    it('should show feature count per category', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      expect(screen.getByText(/Backend Core \(2\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Screen Scraping \(1\)/i)).toBeInTheDocument();
      expect(screen.getByText(/ML\/Analytics \(1\)/i)).toBeInTheDocument();
    });
  });

  describe('Status Display', () => {
    beforeEach(() => {
      mockSuccessfulFetch();
    });

    it('should display latency information when available', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      expect(screen.getAllByText(/Latency: 10.50ms/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/Latency: 15.20ms/i)[0]).toBeInTheDocument();
    });

    it('should display description for each health check', async () => {
      render(<SystemStatus />);

      await screen.findByText('System Status Monitor');
      expect(screen.getByText('Model calibration system health check')).toBeInTheDocument();
      expect(screen.getByText('GTO solver engine health check')).toBeInTheDocument();
    });

    it('should display time ago for last check', async () => {
      render(<SystemStatus />);

      const timeElements = await screen.findAllByText(/ago/i);
      expect(timeElements.length).toBeGreaterThan(0);
    });
  });
});
