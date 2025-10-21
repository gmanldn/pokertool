/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/index.tsx
version: v28.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
---
POKERTOOL-HEADER-END */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import './i18n/i18n'; // Initialize i18n early
import App from './App';
import errorTracking from './services/errorTracking';
import { initializeRUM } from './services/rum';

// Initialize frontend error tracking (Sentry) early
errorTracking.initialize();
initializeRUM();

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
