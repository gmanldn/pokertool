/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/App.tsx
version: v28.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
---
POKERTOOL-HEADER-END */

import React, { useState, useEffect, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, useMediaQuery } from '@mui/material';
import { Provider } from 'react-redux';
import { Dashboard } from './components/Dashboard';
import { Navigation } from './components/Navigation';
import { TableView } from './components/TableView';
import { DetectionLog } from './components/DetectionLog';
import { Statistics } from './components/Statistics';
import { BankrollManager } from './components/BankrollManager';
import { TournamentView } from './components/TournamentView';
import { Settings } from './components/Settings';
import { HUDOverlay } from './components/HUDOverlay';
import { GTOTrainer } from './components/GTOTrainer';
import { HandHistory } from './components/HandHistory';
import { SystemStatus } from './components/SystemStatus';
import { useWebSocket } from './hooks/useWebSocket';
import { ThemeContext } from './contexts/ThemeContext';
import { store, useAppSelector, RootState } from './store';
import { setMobileLayout, SettingsState } from './store/slices/settingsSlice';
import { MobileBottomNav } from './components/MobileBottomNav';
import './styles/App.css';
import './styles/mobile.css';

// Separate component to use Redux hooks
function AppContent() {
  const isMobile = useMediaQuery('(max-width:768px)');
  const isTablet = useMediaQuery('(max-width:1024px)');
  const settings = useAppSelector((state: RootState) => state.settings) as SettingsState;
  const mobileLayout = settings.mobileLayout;
  
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const savedMode = localStorage.getItem('darkMode');
    return savedMode ? JSON.parse(savedMode) : true;
  });

  // Detect mobile and update Redux state
  useEffect(() => {
    const shouldUseMobileLayout = isMobile || isTablet;
    if (shouldUseMobileLayout !== mobileLayout) {
      store.dispatch(setMobileLayout(shouldUseMobileLayout));
    }
  }, [isMobile, isTablet, mobileLayout]);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? 'dark' : 'light',
          primary: {
            main: darkMode ? '#4caf50' : '#2e7d32',
          },
          secondary: {
            main: darkMode ? '#ff9800' : '#ed6c02',
          },
          background: {
            default: darkMode ? '#121212' : '#fafafa',
            paper: darkMode ? '#1e1e1e' : '#ffffff',
          },
        },
        typography: {
          fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        },
        components: {
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: 'none',
                borderRadius: 8,
                color: '#000000',
              },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                borderRadius: 12,
              },
            },
          },
        },
      }),
    [darkMode]
  );

  // WebSocket connection for real-time updates
  const { connected, messages, sendMessage } = useWebSocket('http://localhost:8000');

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeContext.Provider value={{ darkMode, toggleDarkMode }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <div className={`app ${mobileLayout ? 'mobile-layout' : ''}`}>
            <Navigation connected={connected} />
            <main className="app-main">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard messages={messages} />} />
                <Route path="/tables" element={<TableView sendMessage={sendMessage} />} />
                <Route path="/detection-log" element={<DetectionLog messages={messages} />} />
                <Route path="/statistics" element={<Statistics />} />
                <Route path="/bankroll" element={<BankrollManager />} />
                <Route path="/tournament" element={<TournamentView />} />
                <Route path="/hud" element={<HUDOverlay />} />
                <Route path="/gto" element={<GTOTrainer />} />
                <Route path="/history" element={<HandHistory />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/system-status" element={<SystemStatus />} />
              </Routes>
            </main>
            <MobileBottomNav />
          </div>
        </Router>
      </ThemeProvider>
    </ThemeContext.Provider>
  );
}

// Main App component with Redux Provider
function App() {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
}

export default App;
