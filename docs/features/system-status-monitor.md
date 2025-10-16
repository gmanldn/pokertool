# System Status Monitor - User Guide

## Overview

The System Status Monitor is a comprehensive real-time health monitoring dashboard that provides instant visibility into the operational status of all PokerTool components. Access it via the **System Status** menu item (gear icon) in the navigation bar.

## Features

### Real-Time Health Monitoring
- **Live Updates**: WebSocket-powered real-time status updates every 30 seconds
- **Instant Feedback**: See component health changes immediately
- **Color-Coded Status**: Quick visual identification of system health

### Status Indicators

| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 Green | Healthy | Component functioning normally |
| 🟡 Yellow | Degraded | Component partially functional, may have reduced performance |
| 🔴 Red | Failing | Component not working, action required |
| ⚪ Gray | Unknown | Status not yet determined or component initializing |

### Monitored Components

#### Backend Core
- **API Server**: RESTful API endpoints and request handling
- **WebSocket Server**: Real-time communication channel
- **Database**: SQLite database connectivity and operations

#### Screen Scraping
- **OCR Engine**: Tesseract text extraction functionality
- **Screen Capture**: Desktop screenshot capabilities (mss library)
- **Poker Table Detection**: ML model for identifying poker tables
- **Region Extraction**: ROI (Region of Interest) detection and cropping

#### ML/Analytics
- **Model Calibration**: Drift detection and model accuracy tracking
- **GTO Solver**: Game Theory Optimal strategy calculations
- **Opponent Modeling**: Player behavior analysis and prediction
- **Sequential Opponent Fusion**: Temporal opponent behavior analysis
- **Active Learning**: Feedback loop for model improvement
- **Neural Evaluator**: Deep learning hand evaluation
- **Hand Range Analyzer**: Probability calculations for hand ranges

#### GUI Components
- **Frontend Server**: React development server availability
- **Static Assets**: Critical frontend resources loading correctly

#### Advanced Features
- **Scraping Accuracy**: Validation and correction tracking
- **ROI Tracking**: Bankroll and return on investment calculations
- **Tournament Support**: ICM calculations and tournament tracking
- **Multi-Table Support**: Multiple table detection and management
- **Hand History Database**: Game record storage and retrieval

## How to Use

### Accessing the Dashboard

1. Navigate to **System Status** in the main menu
2. Or visit http://localhost:3000/system-status directly

### Viewing System Health

**Overall Status Summary**
- Displayed at the top of the page
- Shows total counts of Healthy, Degraded, and Failing features
- Overall system status indicator (green = all healthy, red = some failing)

**Feature Cards**
Each component displays:
- **Feature Name**: Human-readable component name
- **Status Badge**: Current health status with color coding
- **Last Checked**: Time elapsed since last health check
- **Latency**: Response time in milliseconds (if applicable)
- **Description**: What the component does (hover for tooltip)

### Filtering and Search

**Filter by Status**
Click on status chips to filter:
- **ALL**: Show all components
- **HEALTHY**: Show only working components
- **FAILING**: Show only broken components
- **DEGRADED**: Show partially functional components
- **UNKNOWN**: Show uninitialized components

**Search**
- Type in the search bar to filter by feature name, category, or description
- Search is case-insensitive and matches partial text

### Viewing Error Details

1. For failing components, click the **expand arrow** (▼) on the feature card
2. View detailed error messages
3. Use error information for troubleshooting

### Manual Refresh

- Click the **circular arrow icon** (↻) in the top-right corner
- Forces immediate health check execution
- Useful when testing fixes or debugging

### Exporting Health Reports

1. Click the **Download icon** (⬇) in the top-right corner
2. Downloads a JSON file containing:
   - Complete health status for all components
   - Timestamp of export
   - Detailed error messages
   - Metadata for each component
3. File name format: `system-health-[timestamp].json`

## Interpreting Results

### All Systems Healthy 🟢
- **Overall Status**: Healthy
- **Action**: No action needed
- **Meaning**: All critical components operational

### Some Components Failing 🔴
- **Overall Status**: Failing
- **Action Required**: Investigate failing components
- **Common Causes**:
  - Missing dependencies (Python packages not installed)
  - Optional features not configured
  - Services not running (database, Chrome DevTools Protocol)

### Expected Failures

Some components may show as **failing** if optional features aren't enabled:

**Optional ML Components**:
- `gto_solver` - Requires GTO solver library installation
- `neural_evaluator` - Requires TensorFlow/PyTorch
- `model_calibration` - Requires calibration data

**Optional External Services**:
- `frontend_server` - Only when React dev server is running
- `websocket_server` - Only when WebSocket clients connected

**Development vs. Production**:
- Development mode may show more failing checks for unimplemented features
- Production should have all critical components healthy

## Troubleshooting

### "Failed to connect to backend" Error

**Problem**: Frontend can't reach the API server

**Solutions**:
1. Verify API server is running on port 5001
2. Start the backend: `python scripts/launch_api_simple.py`
3. Check firewall settings

### OCR Engine Failing

**Problem**: `ocr_engine` shows as failing

**Solutions**:
1. Install Tesseract: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
2. Verify installation: `tesseract --version`
3. Restart the API server

### Database Failing

**Problem**: `database` shows as failing

**Solutions**:
1. Check database file exists: `poker_decisions.db`
2. Verify file permissions (read/write access)
3. Check disk space availability

### Screen Capture Failing

**Problem**: `screen_capture` shows as failing

**Solutions**:
1. Grant screen recording permissions (macOS System Preferences > Security & Privacy > Screen Recording)
2. Install mss library: `pip install mss`
3. Restart the application

### WebSocket Connection Issues

**Problem**: Real-time updates not working

**Solutions**:
1. Check browser console for WebSocket errors
2. Verify WebSocket server is running (Backend Core > WebSocket Server should be healthy)
3. Refresh the page to reconnect

## FAQ

**Q: How often are health checks performed?**
A: Automatically every 30 seconds. You can manually trigger checks anytime using the refresh button.

**Q: Do health checks impact performance?**
A: No. Health checks run asynchronously in the background with timeout protections (2-5 seconds per check).

**Q: What should I do if a critical component is failing?**
A:
1. Expand the error details to see the specific error
2. Follow troubleshooting steps for that component
3. Check the developer documentation for advanced debugging
4. Contact support if the issue persists

**Q: Can I disable health checks for specific components?**
A: Health checks are hardcoded for reliability. If a component isn't critical for your use case, you can safely ignore its failing status.

**Q: Why are some ML features failing?**
A: Many ML features are optional and require additional Python packages. Install missing dependencies:
```bash
pip install tensorflow scikit-learn pandas numpy
```

**Q: Is the System Status Monitor available offline?**
A: The dashboard requires connection to the backend API. However, health check data is cached and will show the last known status if temporarily disconnected.

## Best Practices

1. **Check Before Starting Sessions**: Review system health before poker sessions
2. **Monitor During Play**: Keep an eye on the status if experiencing issues
3. **Export Reports for Support**: Download health reports before reporting bugs
4. **Regular Maintenance**: Address degraded components before they fail completely
5. **Validate After Updates**: Check system health after software updates

## Support

If you encounter persistent issues not covered in this guide:

1. Export a health report (JSON file)
2. Check application logs: `pokertool.log`
3. Visit the GitHub issues page: https://github.com/your-repo/pokertool/issues
4. Include the health report and relevant log excerpts

---

**Last Updated**: October 2025
**Version**: v86.0.0
**Feature**: System Status Monitor
