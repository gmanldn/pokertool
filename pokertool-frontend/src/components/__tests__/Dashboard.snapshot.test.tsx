/**
 * Dashboard Component Snapshot Tests
 * ====================================
 *
 * Snapshot tests detect unintended changes to component rendering.
 * Run `npm test -- -u` to update snapshots when changes are intentional.
 */

import React from 'react';
import { render } from '@testing-library/react';
import { Dashboard } from '../Dashboard';

describe('Dashboard Snapshot Tests', () => {
  it('renders correctly with no messages', () => {
    const { container } = render(<Dashboard messages={[]} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders correctly with sample messages', () => {
    const sampleMessages = [
      { id: 1, type: 'info', text: 'Welcome to PokerTool', timestamp: new Date() },
      { id: 2, type: 'success', text: 'Connected to server', timestamp: new Date() },
    ];

    const { container } = render(<Dashboard messages={sampleMessages} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders correctly in loading state', () => {
    const { container } = render(<Dashboard messages={[]} isLoading={true} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
