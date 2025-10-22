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

import React, { useState, useEffect, useMemo, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, useMediaQuery, CircularProgress, Box } from '@mui/material';
import { Provider } from 'react-redux';
import { useWebSocket } from './hooks/useWebSocket';
import { useBackendLifecycle } from './hooks/useBackendLifecycle';
import { ThemeContext } from './contexts/ThemeContext';
import { store, useAppSelector, RootState } from './store';
import { setMobileLayout, SettingsState } from './store/slices/settingsSlice';
import { buildWsUrl } from './config/api';
import './styles/App.css';
import './styles/mobile.css';

// Eagerly load critical components needed for initial render
import { Navigation } from './components/Navigation';
import { MobileBottomNav } from './components/MobileBottomNav';
import ErrorBoundary from './components/ErrorBoundary';
import { GlobalErrorBoundary } from './components/GlobalErrorBoundary';

// Lazy load route components for code splitting
const Dashboard = lazy(() => import('./components/Dashboard').then(module => ({ default: module.Dashboard })));
const TableView = lazy(() => import('./components/TableView').then(module => ({ default: module.TableView })));
const DetectionLog = lazy(() => import('./components/DetectionLog').then(module => ({ default: module.DetectionLog })));
const Statistics = lazy(() => import('./components/Statistics').then(module => ({ default: module.Statistics })));
const BankrollManager = lazy(() => import('./components/BankrollManager').then(module => ({ default: module.BankrollManager })));
const TournamentView = lazy(() => import('./components/TournamentView').then(module => ({ default: module.TournamentView })));
const Settings = lazy(() => import('./components/Settings').then(module => ({ default: module.Settings })));
const HUDOverlay = lazy(() => import('./components/HUDOverlay').then(module => ({ default: module.HUDOverlay })));
const GTOTrainer = lazy(() => import('./components/GTOTrainer').then(module => ({ default: module.GTOTrainer })));
const HandHistory = lazy(() => import('./components/HandHistory').then(module => ({ default: module.HandHistory })));
const SystemStatus = lazy(() => import('./components/SystemStatus').then(module => ({ default: module.SystemStatus })));
const ModelCalibration = lazy(() => import('./components/ModelCalibration').then(module => ({ default: module.ModelCalibration })));
const OpponentFusion = lazy(() => import('./components/OpponentFusion').then(module => ({ default: module.OpponentFusion })));
const ActiveLearning = lazy(() => import('./components/ActiveLearning').then(module => ({ default: module.ActiveLearning })));
const ScrapingAccuracy = lazy(() => import('./components/ScrapingAccuracy').then(module => ({ default: module.ScrapingAccuracy })));
const BackendStatus = lazy(() => import('./pages/BackendStatus'));
const TodoList = lazy(() => import('./components/TodoList').then(module => ({ default: module.TodoList })));
const SmartHelper = lazy(() => import('./pages/SmartHelper'));

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="80vh"
  >
    <CircularProgress size={60} />
  </Box>
);

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
  const { connected, messages, sendMessage } = useWebSocket(buildWsUrl());
  const { status: backendStatus } = useBackendLifecycle();

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
            <Navigation connected={connected} backendStatus={backendStatus} />
            <main className="app-main">
              <Suspense fallback={<LoadingFallback />}>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<ErrorBoundary fallbackType="general"><Dashboard messages={messages} /></ErrorBoundary>} />
                  <Route path="/backend" element={<ErrorBoundary fallbackType="general"><BackendStatus /></ErrorBoundary>} />
                  <Route path="/todo" element={<ErrorBoundary fallbackType="general"><TodoList /></ErrorBoundary>} />
                  <Route path="/tables" element={<ErrorBoundary fallbackType="table"><TableView sendMessage={sendMessage} /></ErrorBoundary>} />
                  <Route path="/detection-log" element={<ErrorBoundary fallbackType="general"><DetectionLog messages={messages} /></ErrorBoundary>} />
                  <Route path="/statistics" element={<ErrorBoundary fallbackType="stats"><Statistics /></ErrorBoundary>} />
                  <Route path="/bankroll" element={<ErrorBoundary fallbackType="general"><BankrollManager /></ErrorBoundary>} />
                  <Route path="/tournament" element={<ErrorBoundary fallbackType="general"><TournamentView /></ErrorBoundary>} />
                  <Route path="/hud" element={<ErrorBoundary fallbackType="general"><HUDOverlay /></ErrorBoundary>} />
                  <Route path="/gto" element={<ErrorBoundary fallbackType="advice"><GTOTrainer /></ErrorBoundary>} />
                  <Route path="/history" element={<ErrorBoundary fallbackType="general"><HandHistory /></ErrorBoundary>} />
                  <Route path="/settings" element={<ErrorBoundary fallbackType="general"><Settings /></ErrorBoundary>} />
                  <Route path="/model-calibration" element={<ErrorBoundary fallbackType="general"><ModelCalibration /></ErrorBoundary>} />
                  <Route path="/system-status" element={<ErrorBoundary fallbackType="general"><SystemStatus /></ErrorBoundary>} />
                  <Route path="/opponent-fusion" element={<ErrorBoundary fallbackType="general"><OpponentFusion /></ErrorBoundary>} />
                  <Route path="/active-learning" element={<ErrorBoundary fallbackType="general"><ActiveLearning /></ErrorBoundary>} />
                  <Route path="/scraping-accuracy" element={<ErrorBoundary fallbackType="general"><ScrapingAccuracy /></ErrorBoundary>} />
                  <Route path="/smarthelper" element={<ErrorBoundary fallbackType="general"><SmartHelper /></ErrorBoundary>} />
                </Routes>
              </Suspense>
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
    <GlobalErrorBoundary>
      <Provider store={store}>
        <AppContent />
      </Provider>
    </GlobalErrorBoundary>
  );
}

export default App;
