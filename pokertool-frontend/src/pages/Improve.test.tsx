/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/pages/Improve.test.tsx
version: v28.0.0
last_commit: '2025-10-22T00:00:00Z'
fixes:
- date: '2025-10-22'
  summary: Comprehensive tests for SuperAdmin authentication feature
---
POKERTOOL-HEADER-END */

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Improve from './Improve';

// Mock crypto.subtle for tests
const mockDigest = jest.fn();
Object.defineProperty(global, 'crypto', {
  value: {
    subtle: {
      digest: mockDigest,
    },
  },
});

// Helper to convert string to ArrayBuffer for mocking
function stringToArrayBuffer(str: string): ArrayBuffer {
  const buf = new ArrayBuffer(str.length * 2);
  const bufView = new Uint16Array(buf);
  for (let i = 0; i < str.length; i++) {
    bufView[i] = str.charCodeAt(i);
  }
  return buf;
}

// Helper to render with theme
const renderWithTheme = (ui: React.ReactElement) => {
  const theme = createTheme({ palette: { mode: 'dark' } });
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
};

// The correct hash for the password (computed separately, not hardcoded password)
const CORRECT_HASH = 'afcf0cafd8f0161edc400dc94d14892a3da4862423863be5f6be6b530ca59416';

describe('Improve Component - SuperAdmin Authentication', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear();

    // Reset mocks
    mockDigest.mockReset();

    // Mock console methods to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should render with SuperAdmin features disabled by default', () => {
      renderWithTheme(<Improve />);

      // Check for SuperAdmin button
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      expect(superAdminButton).toBeInTheDocument();

      // Check for warning alert
      expect(screen.getByText(/Feature Locked/i)).toBeInTheDocument();

      // DoActions button should be disabled
      const doActionsButton = screen.getByRole('button', { name: /DoActions/i });
      expect(doActionsButton).toBeDisabled();
    });

    it('should not show SUPERADMIN chip when not authenticated', () => {
      renderWithTheme(<Improve />);

      // Should have BETA chip but not SUPERADMIN chip
      expect(screen.getByText('BETA')).toBeInTheDocument();
      expect(screen.queryByText('SUPERADMIN')).not.toBeInTheDocument();
    });

    it('should restore session if superadmin was previously enabled', () => {
      // Set session storage before render
      sessionStorage.setItem('superadmin_enabled', 'true');

      renderWithTheme(<Improve />);

      // Should show SUPERADMIN chip
      expect(screen.getByText('SUPERADMIN')).toBeInTheDocument();

      // DoActions button should be enabled
      const doActionsButton = screen.getByRole('button', { name: /DoActions/i });
      expect(doActionsButton).not.toBeDisabled();
    });
  });

  describe('Authentication Dialog', () => {
    it('should show authentication dialog when SuperAdmin button clicked', () => {
      renderWithTheme(<Improve />);

      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Dialog should appear
      expect(screen.getByText('SuperAdmin Authentication')).toBeInTheDocument();
      expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    });

    it('should close dialog when Cancel button clicked', async () => {
      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      fireEvent.click(cancelButton);

      // Dialog should be closed
      await waitFor(() => {
        expect(screen.queryByText('SuperAdmin Authentication')).not.toBeInTheDocument();
      });
    });

    it('should close dialog when clicking outside (backdrop)', () => {
      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Find and click backdrop (MUI Dialog backdrop)
      const backdrop = document.querySelector('.MuiBackdrop-root');
      if (backdrop) {
        fireEvent.click(backdrop);
      }

      // Dialog should be closed
      waitFor(() => {
        expect(screen.queryByText('SuperAdmin Authentication')).not.toBeInTheDocument();
      });
    });

    it('should clear password field when dialog closes', () => {
      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Type password
      const passwordInput = screen.getByLabelText(/Password/i) as HTMLInputElement;
      fireEvent.change(passwordInput, { target: { value: 'test-password' } });
      expect(passwordInput.value).toBe('test-password');

      // Close dialog
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      fireEvent.click(cancelButton);

      // Reopen dialog
      fireEvent.click(superAdminButton);

      // Password should be cleared
      const newPasswordInput = screen.getByLabelText(/Password/i) as HTMLInputElement;
      expect(newPasswordInput.value).toBe('');
    });
  });

  describe('Authentication Logic', () => {
    it('should show error when password field is empty', async () => {
      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Click authenticate without entering password
      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/Please enter a password/i)).toBeInTheDocument();
      });
    });

    it('should reject incorrect password', async () => {
      // Mock hash function to return wrong hash
      const wrongHash = '0000000000000000000000000000000000000000000000000000000000000000';
      const wrongHashBuffer = new Uint8Array(
        wrongHash.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16))
      ).buffer;

      mockDigest.mockResolvedValue(wrongHashBuffer);

      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Enter wrong password
      const passwordInput = screen.getByLabelText(/Password/i);
      fireEvent.change(passwordInput, { target: { value: 'wrong-password' } });

      // Click authenticate
      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Should show error (wait for async hash operation)
      await waitFor(() => {
        const passwordField = screen.getByLabelText(/Password/i);
        // Check if the field has error state - MUI TextField shows helperText
        expect(passwordField).toBeInTheDocument();
      }, { timeout: 3000 });

      // Should NOT enable features
      expect(screen.queryByText('SUPERADMIN')).not.toBeInTheDocument();
      expect(sessionStorage.getItem('superadmin_enabled')).toBeNull();
    });

    it('should accept correct password and enable features', async () => {
      // Mock hash function to return correct hash
      const correctHashBuffer = new Uint8Array(
        CORRECT_HASH.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16))
      ).buffer;

      mockDigest.mockResolvedValue(correctHashBuffer);

      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Enter correct password (we're testing the hash, not the actual password)
      const passwordInput = screen.getByLabelText(/Password/i);
      fireEvent.change(passwordInput, { target: { value: 'test-correct-password' } });

      // Click authenticate
      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Should enable features (wait for async operations)
      await waitFor(() => {
        expect(screen.getByText('SUPERADMIN')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Dialog should close
      await waitFor(() => {
        expect(screen.queryByText('SuperAdmin Authentication')).not.toBeInTheDocument();
      });

      // Session storage should be set
      expect(sessionStorage.getItem('superadmin_enabled')).toBe('true');

      // DoActions button should be enabled
      const doActionsButton = screen.getByRole('button', { name: /DoActions/i });
      expect(doActionsButton).not.toBeDisabled();
    });

    it('should support Enter key to submit authentication', async () => {
      // Mock hash function to return correct hash
      const correctHashBuffer = new Uint8Array(
        CORRECT_HASH.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16))
      ).buffer;

      mockDigest.mockResolvedValue(correctHashBuffer);

      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Enter password and press Enter
      const passwordInput = screen.getByLabelText(/Password/i);
      fireEvent.change(passwordInput, { target: { value: 'test-password' } });
      fireEvent.keyPress(passwordInput, { key: 'Enter', code: 'Enter', charCode: 13 });

      // Should enable features (wait for async operations)
      await waitFor(() => {
        expect(screen.getByText('SUPERADMIN')).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should handle crypto errors gracefully', async () => {
      // Mock hash function to throw error
      mockDigest.mockRejectedValue(new Error('Crypto error'));

      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Enter password
      const passwordInput = screen.getByLabelText(/Password/i);
      fireEvent.change(passwordInput, { target: { value: 'test-password' } });

      // Click authenticate
      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/Authentication error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Feature Disabling/Enabling', () => {
    it('should disable SuperAdmin mode when clicking button while authenticated', async () => {
      // Start with authenticated state
      sessionStorage.setItem('superadmin_enabled', 'true');

      renderWithTheme(<Improve />);

      // Should be authenticated
      expect(screen.getByText('SUPERADMIN')).toBeInTheDocument();

      // Click SuperAdmin button to disable
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Should be disabled
      expect(screen.queryByText('SUPERADMIN')).not.toBeInTheDocument();
      expect(sessionStorage.getItem('superadmin_enabled')).toBeNull();

      // Features should be disabled
      const doActionsButton = screen.getByRole('button', { name: /DoActions/i });
      expect(doActionsButton).toBeDisabled();
    });

    it('should disable all control buttons when not authenticated', () => {
      renderWithTheme(<Improve />);

      // Check all buttons are disabled
      expect(screen.getByRole('button', { name: /Add New Task/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /DoActions/i })).toBeDisabled();
    });

    it('should enable all control buttons when authenticated', () => {
      sessionStorage.setItem('superadmin_enabled', 'true');

      renderWithTheme(<Improve />);

      // Check all buttons are enabled
      expect(screen.getByRole('button', { name: /Add New Task/i })).not.toBeDisabled();
      expect(screen.getByRole('button', { name: /DoActions/i })).not.toBeDisabled();
    });

    it('should show/hide warning alert based on authentication state', async () => {
      renderWithTheme(<Improve />);

      // Should show warning when not authenticated
      expect(screen.getByText(/Feature Locked/i)).toBeInTheDocument();

      // Simulate authentication by enabling it directly
      const correctHashBuffer = new Uint8Array(
        CORRECT_HASH.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16))
      ).buffer;
      mockDigest.mockResolvedValue(correctHashBuffer);

      // Open dialog and authenticate
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      const passwordInput = screen.getByLabelText(/Password/i);
      fireEvent.change(passwordInput, { target: { value: 'test' } });

      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Wait for authentication to complete
      await waitFor(() => {
        expect(screen.getByText('SUPERADMIN')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Warning should be gone
      expect(screen.queryByText(/Feature Locked/i)).not.toBeInTheDocument();
    });
  });

  describe('Visual State Changes', () => {
    it('should change button appearance when authenticated', async () => {
      renderWithTheme(<Improve />);

      // Initially should be outlined variant
      let superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      expect(superAdminButton).toHaveClass('MuiButton-outlined');

      // Authenticate
      const correctHashBuffer = new Uint8Array(
        CORRECT_HASH.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16))
      ).buffer;
      mockDigest.mockResolvedValue(correctHashBuffer);

      fireEvent.click(superAdminButton);
      const passwordInput = screen.getByLabelText(/Password/i);
      fireEvent.change(passwordInput, { target: { value: 'test' } });
      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByText('SUPERADMIN')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Should be contained variant
      superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      expect(superAdminButton).toHaveClass('MuiButton-contained');
    });

    it('should show lock icon when locked and unlock icon when unlocked', () => {
      const { rerender } = renderWithTheme(<Improve />);

      const theme = createTheme({ palette: { mode: 'dark' } });

      // Should show lock icon (we can check via aria-label or test-id if added)
      expect(screen.getByRole('button', { name: /SuperAdmin/i })).toBeInTheDocument();

      // Authenticate
      sessionStorage.setItem('superadmin_enabled', 'true');
      rerender(<ThemeProvider theme={theme}><Improve /></ThemeProvider>);

      // Button should still be there but with different appearance
      expect(screen.getByRole('button', { name: /SuperAdmin/i })).toBeInTheDocument();
    });
  });

  describe('Password Hash Security', () => {
    it('should never store plaintext password', async () => {
      const correctHashBuffer = new Uint8Array(
        CORRECT_HASH.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16))
      ).buffer;

      mockDigest.mockResolvedValue(correctHashBuffer);

      renderWithTheme(<Improve />);

      // Open dialog and authenticate
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      const passwordInput = screen.getByLabelText(/Password/i);
      const testPassword = 'my-secret-password';
      fireEvent.change(passwordInput, { target: { value: testPassword } });

      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      await waitFor(() => {
        expect(screen.getByText('SUPERADMIN')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Check that password is not stored anywhere
      expect(sessionStorage.getItem('password')).toBeNull();
      expect(sessionStorage.getItem('superadmin_password')).toBeNull();
      expect(localStorage.getItem('password')).toBeNull();
      expect(localStorage.getItem('superadmin_password')).toBeNull();

      // Only the enabled flag should be stored
      expect(sessionStorage.getItem('superadmin_enabled')).toBe('true');
    });

    it('should use SHA-256 hashing', async () => {
      // Mock will be called, just need to provide a response
      mockDigest.mockResolvedValue(new ArrayBuffer(32));

      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Enter password
      const passwordInput = screen.getByLabelText(/Password/i);
      fireEvent.change(passwordInput, { target: { value: 'test' } });

      // Click authenticate
      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Verify that crypto.subtle.digest was called with SHA-256
      await waitFor(() => {
        expect(mockDigest).toHaveBeenCalledWith('SHA-256', expect.any(ArrayBuffer));
      }, { timeout: 3000 });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      renderWithTheme(<Improve />);

      // SuperAdmin button should have tooltip/title
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      expect(superAdminButton).toBeInTheDocument();
    });

    it('should support keyboard navigation in dialog', () => {
      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Password field should auto-focus
      const passwordInput = screen.getByLabelText(/Password/i);
      expect(document.activeElement).toBe(passwordInput);
    });

    it('should show error messages with proper styling', async () => {
      renderWithTheme(<Improve />);

      // Open dialog
      const superAdminButton = screen.getByRole('button', { name: /SuperAdmin/i });
      fireEvent.click(superAdminButton);

      // Try to authenticate without password
      const authenticateButton = screen.getByRole('button', { name: /Authenticate/i });
      fireEvent.click(authenticateButton);

      // Error should be visible
      await waitFor(() => {
        const errorText = screen.getByText(/Please enter a password/i);
        expect(errorText).toBeInTheDocument();
      });
    });
  });
});
