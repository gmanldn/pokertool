/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/OpponentFusion.test.tsx
version: v86.3.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created unit tests for OpponentFusion component
---
POKERTOOL-HEADER-END */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { OpponentFusion } from './OpponentFusion';
import { buildApiUrl } from '../config/api';

jest.mock('../config/api', () => ({
  buildApiUrl: jest.fn((path: string) => `http://localhost:5001${path}`),
}));

global.fetch = jest.fn();

const mockStats = {
  tracked_players: 5,
  total_hands_analyzed: 1250,
  active_patterns: 12,
  prediction_accuracy: 0.87,
  temporal_window_size: 10,
  status: 'active',
};

describe('OpponentFusion Component', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
    jest.clearAllTimers();
  });

  it('should render loading state initially', () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<OpponentFusion />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should fetch opponent fusion data on mount', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5001/api/ml/opponent-fusion/stats');
    });
  });

  it('should display opponent fusion data after successful fetch', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(screen.getByText('Sequential Opponent Fusion')).toBeInTheDocument();
      expect(screen.getAllByText('5')[0]).toBeInTheDocument(); // tracked_players
      expect(screen.getByText('1,250')).toBeInTheDocument(); // total_hands_analyzed
      expect(screen.getAllByText('12')[0]).toBeInTheDocument(); // active_patterns
      expect(screen.getByText('87.0%')).toBeInTheDocument(); // prediction_accuracy
    }, { timeout: 3000 });
  });

  it('should display error message when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(screen.getByText('Failed to connect to backend. Is the server running?')).toBeInTheDocument();
    });
  });

  it('should display status chip with correct color', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });

  it('should display message when no players are tracked', async () => {
    const emptyStats = { ...mockStats, tracked_players: 0 };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: emptyStats }),
    });

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(screen.getByText(/No players currently tracked/i)).toBeInTheDocument();
    });
  });

  it('should handle refresh button click', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, data: mockStats }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, data: { ...mockStats, tracked_players: 8 } }),
      });

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(screen.getAllByText('5')[0]).toBeInTheDocument();
    }, { timeout: 3000 });

    const refreshButton = screen.getByRole('button');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 3000 });
  });

  it('should display temporal window size', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(screen.getByText('10 hands')).toBeInTheDocument();
    });
  });

  it('should display prediction accuracy with percentage', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<OpponentFusion />);

    await waitFor(() => {
      expect(screen.getByText('87.0%')).toBeInTheDocument();
    });
  });
});
