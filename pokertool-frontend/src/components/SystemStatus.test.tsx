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

  constructor(public url: string) {
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
    (global.fetch as jest.Mock).mockClear();
    jest.clearAllTimers();
  });

  describe('Initial Render and Data Fetching', () => {
    it('should render loading state initially', () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<SystemStatus />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should fetch health data on mount', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });

      render(<SystemStatus />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:5001/api/system/health');
      });
    });

    it('should display health data after successful fetch', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });

      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('System Status Monitor')).toBeInTheDocument();
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });
    });

    it('should display error message when fetch fails', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Failed to connect to backend. Is the server running?')).toBeInTheDocument();
      });
    });
  });

  describe('Overall Status Summary', () => {
    beforeEach(async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });
    });

    it('should display overall status', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
        expect(screen.getByText('Overall Status')).toBeInTheDocument();
      });
    });

    it('should display counts for healthy, degraded, and failing features', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Healthy')).toBeInTheDocument();
        expect(screen.getByText('Degraded')).toBeInTheDocument();
        expect(screen.getByText('Failing')).toBeInTheDocument();
      });
    });

    it('should calculate correct healthy count', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        // Should show 2 healthy features (model_calibration and gto_solver)
        const healthySection = screen.getByText('Healthy').parentElement;
        expect(within(healthySection!).getByText('2')).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    beforeEach(async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });
    });

    it('should filter health checks by search query', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search features...');
      fireEvent.change(searchInput, { target: { value: 'ocr' } });

      await waitFor(() => {
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
        expect(screen.getByText('Ocr Engine')).toBeInTheDocument();
      });
    });

    it('should show no results message when search has no matches', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search features...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByText('No features found matching your criteria')).toBeInTheDocument();
      });
    });

    it('should clear filters when clicking Clear Filters button', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search features...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByText('Clear Filters')).toBeInTheDocument();
      });

      const clearButton = screen.getByText('Clear Filters');
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Functionality', () => {
    beforeEach(async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });
    });

    it('should filter by healthy status', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });

      const healthyChip = screen.getByText('HEALTHY');
      fireEvent.click(healthyChip);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
        expect(screen.getByText('Gto Solver')).toBeInTheDocument();
        expect(screen.queryByText('Ocr Engine')).not.toBeInTheDocument();
      });
    });

    it('should filter by failing status', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });

      const failingChip = screen.getByText('FAILING');
      fireEvent.click(failingChip);

      await waitFor(() => {
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
        expect(screen.getByText('Neural Evaluator')).toBeInTheDocument();
      });
    });

    it('should filter by degraded status', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });

      const degradedChip = screen.getByText('DEGRADED');
      fireEvent.click(degradedChip);

      await waitFor(() => {
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
        expect(screen.getByText('Ocr Engine')).toBeInTheDocument();
      });
    });

    it('should show all features when ALL filter is selected', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
      });

      // First filter to something specific
      const failingChip = screen.getByText('FAILING');
      fireEvent.click(failingChip);

      await waitFor(() => {
        expect(screen.queryByText('Model Calibration')).not.toBeInTheDocument();
      });

      // Then click ALL
      const allChip = screen.getByText('ALL');
      fireEvent.click(allChip);

      await waitFor(() => {
        expect(screen.getByText('Model Calibration')).toBeInTheDocument();
        expect(screen.getByText('Ocr Engine')).toBeInTheDocument();
        expect(screen.getByText('Neural Evaluator')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refetch data when refresh button is clicked', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockHealthData,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockHealthData, overall_status: 'degraded' }),
        });

      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });

      const refreshButton = screen.getByRole('button', { name: /refresh all checks/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });

    it('should show refreshing state while fetching', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockHealthData,
        })
        .mockImplementationOnce(() => new Promise(() => {}));

      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });

      const refreshButton = screen.getByRole('button', { name: /refresh all checks/i });
      fireEvent.click(refreshButton);

      // Should show spinner while refreshing
      await waitFor(() => {
        const buttons = screen.getAllByRole('button', { name: /refresh all checks/i });
        expect(buttons[0]).toBeDisabled();
      });
    });
  });

  describe('Export Functionality', () => {
    beforeEach(async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });

      // Mock URL.createObjectURL and document.createElement
      global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
      global.URL.revokeObjectURL = jest.fn();

      const mockAnchor = document.createElement('a');
      mockAnchor.click = jest.fn();
      jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor);
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    it('should export health data as JSON when export button is clicked', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /export health report/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(global.URL.createObjectURL).toHaveBeenCalled();
        expect(global.URL.revokeObjectURL).toHaveBeenCalled();
      });
    });
  });

  describe('Card Expansion', () => {
    beforeEach(async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });
    });

    it('should expand card to show error details when expand button is clicked', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Ocr Engine')).toBeInTheDocument();
      });

      // Error message should not be visible initially
      expect(screen.queryByText('OCR performance degraded')).not.toBeInTheDocument();

      // Find and click the expand button for the OCR Engine card
      const ocrCard = screen.getByText('Ocr Engine').closest('.MuiCard-root');
      const expandButton = within(ocrCard as HTMLElement).getByRole('button');
      fireEvent.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText('OCR performance degraded')).toBeInTheDocument();
      });
    });

    it('should collapse card when expand button is clicked again', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Ocr Engine')).toBeInTheDocument();
      });

      const ocrCard = screen.getByText('Ocr Engine').closest('.MuiCard-root');
      const expandButton = within(ocrCard as HTMLElement).getByRole('button');

      // Expand
      fireEvent.click(expandButton);
      await waitFor(() => {
        expect(screen.getByText('OCR performance degraded')).toBeInTheDocument();
      });

      // Collapse
      fireEvent.click(expandButton);
      await waitFor(() => {
        expect(screen.queryByText('OCR performance degraded')).not.toBeInTheDocument();
      });
    });
  });

  describe('Category Display', () => {
    beforeEach(async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });
    });

    it('should display correct category names', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText(/Backend Core/i)).toBeInTheDocument();
        expect(screen.getByText(/Screen Scraping/i)).toBeInTheDocument();
        expect(screen.getByText(/ML\/Analytics/i)).toBeInTheDocument();
      });
    });

    it('should show feature count per category', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText(/Backend Core \(2\)/i)).toBeInTheDocument();
        expect(screen.getByText(/Screen Scraping \(1\)/i)).toBeInTheDocument();
        expect(screen.getByText(/ML\/Analytics \(1\)/i)).toBeInTheDocument();
      });
    });
  });

  describe('Status Display', () => {
    beforeEach(async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealthData,
      });
    });

    it('should display latency information when available', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText(/Latency: 10.50ms/i)).toBeInTheDocument();
        expect(screen.getByText(/Latency: 15.20ms/i)).toBeInTheDocument();
      });
    });

    it('should display description for each health check', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        expect(screen.getByText('Model calibration system health check')).toBeInTheDocument();
        expect(screen.getByText('GTO solver engine health check')).toBeInTheDocument();
      });
    });

    it('should display time ago for last check', async () => {
      render(<SystemStatus />);

      await waitFor(() => {
        // Should show some time ago text (implementation will vary based on current time)
        const timeElements = screen.getAllByText(/ago/i);
        expect(timeElements.length).toBeGreaterThan(0);
      });
    });
  });
});
