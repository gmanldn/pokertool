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
      { type: 'stats_update', data: { handsPlayed: 10, profit: 50 }, timestamp: Date.now() },
      { type: 'info', data: { message: 'Connected to server' }, timestamp: Date.now() },
    ];

    const { container } = render(<Dashboard messages={sampleMessages} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders correctly with no stats', () => {
    const { container } = render(<Dashboard messages={[]} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
