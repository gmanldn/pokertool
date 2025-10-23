/**
 * EmptyState Component Snapshot Tests
 * ====================================
 *
 * Snapshot tests for EmptyState component variations.
 */

import React from 'react';
import { render } from '@testing-library/react';
import { EmptyState } from '../EmptyState';

describe('EmptyState Snapshot Tests', () => {
  it('renders no-data state correctly', () => {
    const { container } = render(
      <EmptyState
        variant="no-data"
        title="No hands recorded yet"
        message="Start playing to see your stats here"
      />
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders error state correctly', () => {
    const { container } = render(
      <EmptyState
        variant="error"
        title="Connection Error"
        message="Could not connect to server"
      />
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders loading state correctly', () => {
    const { container } = render(
      <EmptyState
        variant="loading"
        title="Loading..."
        message="Fetching your data"
      />
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders with action button', () => {
    const mockAction = jest.fn();
    const { container } = render(
      <EmptyState
        variant="no-data"
        title="Get Started"
        message="Begin your poker journey"
        actionLabel="Start Session"
        onAction={mockAction}
      />
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
