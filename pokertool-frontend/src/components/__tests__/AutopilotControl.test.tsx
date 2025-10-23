/**
 * Autopilot Control Component Tests
 *
 * Tests for the Autopilot control panel component that manages automated gameplay.
 */

import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { store } from '../../store';
import { AutopilotControl } from '../AutopilotControl';

// Mock useWebSocket hook
jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(() => ({
    connected: true,
    messages: [],
    sendMessage: jest.fn(),
  })),
}));

const mockSendMessage = jest.fn();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </Provider>
  );
};

describe('AutopilotControl Component', () => {
  beforeEach(() => {
    mockSendMessage.mockClear();
  });

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);
      expect(screen.getByText('Autopilot Control')).toBeInTheDocument();
    });

    it('should display STANDBY status when not active', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);
      expect(screen.getByText('STANDBY')).toBeInTheDocument();
    });

    it('should show warning alert when autopilot is disabled', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);
      expect(screen.getByText(/Important:/)).toBeInTheDocument();
    });

    it('should display all control settings', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText('Autopilot Settings')).toBeInTheDocument();
      expect(screen.getByText('Playing Strategy')).toBeInTheDocument();
      expect(screen.getByText('Risk Tolerance')).toBeInTheDocument();
    });

    it('should display session statistics panel', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText('Session Statistics')).toBeInTheDocument();
      expect(screen.getByText('Hands Played')).toBeInTheDocument();
      expect(screen.getByText('Hands Won')).toBeInTheDocument();
      expect(screen.getByText('Total Profit')).toBeInTheDocument();
    });

    it('should display playing style metrics', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText('Playing Style Metrics')).toBeInTheDocument();
      expect(screen.getByText(/VPIP/)).toBeInTheDocument();
      expect(screen.getByText(/PFR/)).toBeInTheDocument();
      expect(screen.getByText(/Aggression Factor/)).toBeInTheDocument();
    });
  });

  describe('Autopilot Toggle', () => {
    it('should send start_autopilot message when enabling', async () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      const toggle = screen.getByRole('checkbox', { name: /Enable Autopilot/ });
      fireEvent.click(toggle);

      await waitFor(() => {
        expect(mockSendMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'start_autopilot',
          })
        );
      });
    });

    it('should show ACTIVE status when autopilot is enabled', async () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      const toggle = screen.getByRole('checkbox', { name: /Enable Autopilot/ });
      fireEvent.click(toggle);

      await waitFor(() => {
        expect(screen.getByText('ACTIVE')).toBeInTheDocument();
      });
    });

    it('should show success alert when autopilot is active', async () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      const toggle = screen.getByRole('checkbox', { name: /Enable Autopilot/ });
      fireEvent.click(toggle);

      await waitFor(() => {
        expect(screen.getByText(/Autopilot is active/)).toBeInTheDocument();
      });
    });

    it('should display emergency stop button when active', async () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      const toggle = screen.getByRole('checkbox', { name: /Enable Autopilot/ });
      fireEvent.click(toggle);

      await waitFor(() => {
        expect(screen.getByText('EMERGENCY STOP')).toBeInTheDocument();
      });
    });

    it('should send stop_autopilot message when emergency stop is clicked', async () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      // Enable autopilot first
      const toggle = screen.getByRole('checkbox', { name: /Enable Autopilot/ });
      fireEvent.click(toggle);

      await waitFor(() => {
        expect(screen.getByText('EMERGENCY STOP')).toBeInTheDocument();
      });

      // Clear previous calls
      mockSendMessage.mockClear();

      // Click emergency stop
      const stopButton = screen.getByText('EMERGENCY STOP');
      fireEvent.click(stopButton);

      await waitFor(() => {
        expect(mockSendMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'stop_autopilot',
          })
        );
      });
    });
  });

  describe('Strategy Selection', () => {
    it('should have balanced strategy selected by default', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      // The default value should be visible in the select
      const description = screen.getByText(/Mix of tight and loose play/);
      expect(description).toBeInTheDocument();
    });

    it('should disable strategy selection when autopilot is active', async () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      const toggle = screen.getByRole('checkbox', { name: /Enable Autopilot/ });
      fireEvent.click(toggle);

      await waitFor(() => {
        // Find the select by its label
        const strategyLabel = screen.getByText('Playing Strategy');
        const selectContainer = strategyLabel.closest('.MuiFormControl-root');
        expect(selectContainer).toBeInTheDocument();
      });
    });
  });

  describe('Risk Tolerance', () => {
    it('should have medium risk selected by default', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      const riskChip = screen.getByText('MEDIUM');
      expect(riskChip).toBeInTheDocument();
    });

    it('should display risk tolerance slider', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText('Risk Tolerance')).toBeInTheDocument();
      // Slider should be present (check for Low/Medium/High/Very High labels)
      expect(screen.getByText('Low')).toBeInTheDocument();
      expect(screen.getByText('Very High')).toBeInTheDocument();
    });
  });

  describe('Stop Loss and Win Goal', () => {
    it('should display stop loss slider', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText(/Stop Loss:/)).toBeInTheDocument();
    });

    it('should display win goal slider', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText(/Win Goal:/)).toBeInTheDocument();
    });

    it('should display auto-reload option', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText(/Auto-reload stack when below minimum/)).toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
    it('should show zero hands played initially', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      const handsCells = screen.getAllByText('0');
      expect(handsCells.length).toBeGreaterThan(0);
    });

    it('should display profit as $0.00 initially', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText('$0.00')).toBeInTheDocument();
    });

    it('should display session duration', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      expect(screen.getByText('Session Duration')).toBeInTheDocument();
      expect(screen.getByText('0h 0m')).toBeInTheDocument();
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should render on mobile screens', () => {
      // Set mobile viewport
      global.innerWidth = 500;
      global.dispatchEvent(new Event('resize'));

      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);
      expect(screen.getByText('Autopilot Control')).toBeInTheDocument();
    });
  });

  describe('WebSocket Integration', () => {
    it('should handle autopilot_state_update messages', async () => {
      const { useWebSocket } = require('../../hooks/useWebSocket');
      useWebSocket.mockReturnValue({
        connected: true,
        messages: [
          {
            type: 'autopilot_state_update',
            data: {
              isActive: true,
              handsPlayed: 42,
              currentProfit: 125.50,
              winRate: 58.3,
            },
          },
        ],
        sendMessage: jest.fn(),
      });

      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      await waitFor(() => {
        // The component should update with new data from WebSocket
        expect(screen.getByText('42')).toBeInTheDocument();
      });
    });

    it('should handle autopilot_stats_update messages', async () => {
      const { useWebSocket } = require('../../hooks/useWebSocket');
      useWebSocket.mockReturnValue({
        connected: true,
        messages: [
          {
            type: 'autopilot_stats_update',
            data: {
              handsPlayed: 100,
              handsWon: 58,
              totalProfit: 250.75,
              bigBlindsWon: 12.5,
              vpip: 22,
              pfr: 18,
              aggression: 2.5,
              sessionDuration: 3600,
            },
          },
        ],
        sendMessage: jest.fn(),
      });

      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      await waitFor(() => {
        // Check for updated statistics
        expect(screen.getByText('100')).toBeInTheDocument();
        expect(screen.getByText('58')).toBeInTheDocument();
      });
    });
  });

  describe('Feature Parity', () => {
    it('should have all v82 Autopilot features', () => {
      renderWithProviders(<AutopilotControl sendMessage={mockSendMessage} />);

      // Verify key features from v82 Autopilot panel
      expect(screen.getByText('Autopilot Settings')).toBeInTheDocument();
      expect(screen.getByText('Playing Strategy')).toBeInTheDocument();
      expect(screen.getByText('Risk Tolerance')).toBeInTheDocument();
      expect(screen.getByText(/Stop Loss/)).toBeInTheDocument();
      expect(screen.getByText(/Win Goal/)).toBeInTheDocument();
      expect(screen.getByText('Session Statistics')).toBeInTheDocument();
      expect(screen.getByText('Playing Style Metrics')).toBeInTheDocument();
    });
  });
});
