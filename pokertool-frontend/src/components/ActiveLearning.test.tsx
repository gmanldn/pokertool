/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ActiveLearning.test.tsx
version: v86.3.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created unit tests for ActiveLearning component
---
POKERTOOL-HEADER-END */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ActiveLearning } from './ActiveLearning';
import { buildApiUrl } from '../config/api';

jest.mock('../config/api', () => ({
  buildApiUrl: jest.fn((path: string) => `http://localhost:5001${path}`),
}));

global.fetch = jest.fn();

const mockStats = {
  pending_reviews: 3,
  total_feedback: 145,
  high_uncertainty_events: 8,
  model_accuracy_improvement: 0.042,
  last_retraining: '2025-10-15T14:30:00Z',
  status: 'active',
};

describe('ActiveLearning Component', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
    jest.clearAllTimers();
  });

  it('should render loading state initially', () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<ActiveLearning />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should fetch active learning data on mount', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5001/api/ml/active-learning/stats');
    });
  });

  it('should display active learning data after successful fetch', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText('Active Learning Feedback')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // pending_reviews
      expect(screen.getByText('145')).toBeInTheDocument(); // total_feedback
      expect(screen.getByText('8')).toBeInTheDocument(); // high_uncertainty_events
      expect(screen.getByText('+4.2%')).toBeInTheDocument(); // model_accuracy_improvement
    });
  });

  it('should display error message when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText('Failed to connect to backend. Is the server running?')).toBeInTheDocument();
    });
  });

  it('should show success message when no pending reviews', async () => {
    const noPendingStats = { ...mockStats, pending_reviews: 0 };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: noPendingStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText(/All feedback events have been reviewed/i)).toBeInTheDocument();
    });
  });

  it('should show info alert when there are pending reviews', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText(/3 events awaiting expert review/i)).toBeInTheDocument();
    });
  });

  it('should display warning icon when pending reviews exist', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
      // Warning icon should be present
      const warningIcons = screen.getAllByTestId('WarningIcon');
      expect(warningIcons.length).toBeGreaterThan(0);
    });
  });

  it('should format last retraining date correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      // Should display formatted date (implementation may vary based on locale)
      expect(screen.getByText(/10\/15\/2025|15\/10\/2025/i)).toBeInTheDocument();
    });
  });

  it('should show "Never" when last retraining is null', async () => {
    const noRetrainingStats = { ...mockStats, last_retraining: null };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: noRetrainingStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText('Never')).toBeInTheDocument();
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
        json: async () => ({ success: true, data: { ...mockStats, pending_reviews: 5 } }),
      });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    const refreshButton = screen.getByRole('button');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  it('should display status chip', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ActiveLearning />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });
});
