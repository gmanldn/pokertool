/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/ScrapingAccuracy.test.tsx
version: v86.3.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created unit tests for ScrapingAccuracy component
---
POKERTOOL-HEADER-END */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ScrapingAccuracy } from './ScrapingAccuracy';
import { buildApiUrl } from '../config/api';

jest.mock('../config/api', () => ({
  buildApiUrl: jest.fn((path: string) => `http://localhost:5001${path}`),
}));

global.fetch = jest.fn();

const mockStats = {
  overall_accuracy: 0.96,
  pot_corrections: 42,
  card_recognition_accuracy: 0.98,
  ocr_corrections: 27,
  temporal_consensus_improvements: 18,
  total_frames_processed: 15420,
  status: 'active',
};

describe('ScrapingAccuracy Component', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
    jest.clearAllTimers();
  });

  it('should render loading state initially', () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<ScrapingAccuracy />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should fetch scraping accuracy data on mount', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5001/api/scraping/accuracy/stats');
    });
  });

  it('should display scraping accuracy data after successful fetch', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('Scraping Accuracy System')).toBeInTheDocument();
      expect(screen.getByText('96.0%')).toBeInTheDocument(); // overall_accuracy
      expect(screen.getByText('98.0%')).toBeInTheDocument(); // card_recognition_accuracy
      expect(screen.getByText('42')).toBeInTheDocument(); // pot_corrections
      expect(screen.getByText('27')).toBeInTheDocument(); // ocr_corrections
      expect(screen.getByText('18')).toBeInTheDocument(); // temporal_consensus_improvements
    });
  });

  it('should display error message when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('Failed to connect to backend. Is the server running?')).toBeInTheDocument();
    });
  });

  it('should display status chip with correct color', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });

  it('should display total frames processed with formatting', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('15,420')).toBeInTheDocument();
    });
  });

  it('should calculate and display total corrections', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      // pot_corrections (42) + ocr_corrections (27) = 69
      expect(screen.getByText('69')).toBeInTheDocument();
    });
  });

  it('should show "Excellent" label for high accuracy', async () => {
    const highAccuracyStats = { ...mockStats, overall_accuracy: 0.97 };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: highAccuracyStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('Excellent')).toBeInTheDocument();
    });
  });

  it('should show "Good" label for moderate accuracy', async () => {
    const moderateAccuracyStats = { ...mockStats, overall_accuracy: 0.92 };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: moderateAccuracyStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('Good')).toBeInTheDocument();
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
        json: async () => ({ success: true, data: { ...mockStats, overall_accuracy: 0.97 } }),
      });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('96.0%')).toBeInTheDocument();
    });

    const refreshButton = screen.getByRole('button');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  it('should display recognition metrics section', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('Recognition Metrics')).toBeInTheDocument();
      expect(screen.getByText('Card Recognition')).toBeInTheDocument();
      expect(screen.getByText('Pot Corrections')).toBeInTheDocument();
      expect(screen.getByText('OCR Corrections')).toBeInTheDocument();
    });
  });

  it('should display accuracy improvements section', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('Accuracy Improvements')).toBeInTheDocument();
      expect(screen.getByText('Temporal Consensus')).toBeInTheDocument();
    });
  });

  it('should display success alert for active system', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText(/System is actively improving accuracy/i)).toBeInTheDocument();
    });
  });

  it('should display descriptive captions for metrics', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, data: mockStats }),
    });

    render(<ScrapingAccuracy />);

    await waitFor(() => {
      expect(screen.getByText('Context-aware validation')).toBeInTheDocument();
      expect(screen.getByText('Post-processing rules')).toBeInTheDocument();
      expect(screen.getByText('Multi-frame smoothing corrections')).toBeInTheDocument();
    });
  });
});
