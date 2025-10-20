# Portable Configuration System

The PokerTool frontend uses a flexible, portable configuration system that allows easy customization of API endpoints without requiring system-level changes or rebuilding the application.

## Overview

The configuration system supports multiple methods with a clear priority order:

1. **Environment Variables** (highest priority)
2. **Runtime Config File** (public/config.json)
3. **Auto-Detection** (based on browser location)
4. **Default Values** (localhost)

## Configuration Methods

### Method 1: Environment Variables (Recommended for Development)

Create `.env.local` in the `pokertool-frontend/` directory:

```bash
# Copy from template
cp .env.example .env.local

# Edit with your settings
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=http://localhost:8000
```

**Pros:**
- Takes highest priority
- Git-ignored by default
- Standard React approach

**Cons:**
- Requires restart of dev server
- Need to rebuild for production changes

### Method 2: Runtime Config File (Recommended for Portability)

Create `public/config.json` (copy from template):

```bash
cd pokertool-frontend/public
cp config.json.example config.json
```

Edit `config.json`:

```json
{
  "apiUrl": "http://192.168.1.100:5001",
  "wsUrl": "http://192.168.1.100:8000",
  "apiPort": 5001,
  "wsPort": 8000
}
```

**Pros:**
- No rebuild required
- Can be changed at runtime
- Works in both dev and production
- Git-ignored (won't affect other developers)

**Cons:**
- Lower priority than environment variables

### Method 3: Auto-Detection (Default Behavior)

The system automatically detects API endpoints based on the browser's current location:

- **On localhost**: Uses default ports (5001 for API, 8000 for WS)
- **On other hosts**: Uses same hostname with configured ports

To use auto-detection, simply omit `apiUrl` and `wsUrl` from config:

```json
{
  "apiPort": 5001,
  "wsPort": 8000
}
```

**Pros:**
- Zero configuration for standard setups
- Works across different network environments

**Cons:**
- Requires API server on same host as frontend

### Method 4: Defaults (Fallback)

If no configuration is provided, the system uses:

```
API: http://localhost:5001
WS:  http://localhost:8000
```

## Usage Examples

### Example 1: Local Development (Default)

No configuration needed! Just run:

```bash
# Terminal 1 - Backend
.venv/bin/python scripts/launch_api_simple.py

# Terminal 2 - Frontend
cd pokertool-frontend && npm start
```

Access at: http://localhost:3000

### Example 2: Custom IP Address

Create `pokertool-frontend/public/config.json`:

```json
{
  "apiUrl": "http://192.168.1.50:5001",
  "wsUrl": "http://192.168.1.50:8000"
}
```

The frontend will connect to the API server at 192.168.1.50.

### Example 3: Production Deployment

Create `pokertool-frontend/public/config.json`:

```json
{
  "apiUrl": "https://api.pokertool.app",
  "wsUrl": "wss://ws.pokertool.app"
}
```

### Example 4: Docker/Containerized

Use auto-detection with just ports:

```json
{
  "apiPort": 5001,
  "wsPort": 8000
}
```

The app will automatically use the container's hostname.

## Configuration API

### Available Functions

The config system exposes several helper functions:

```typescript
import {
  buildApiUrl,      // Build full API endpoint URL
  buildWsUrl,       // Build full WebSocket URL
  httpToWs,         // Convert HTTP URL to WS URL
  getConfig,        // Get full configuration (async)
  getConfigSync,    // Get configuration synchronously
} from './config/api';

// Usage
const healthUrl = buildApiUrl('/api/system/health');
// Returns: http://localhost:5001/api/system/health

const wsUrl = buildWsUrl('/ws/system-health');
// Returns: ws://localhost:5001/ws/system-health
```

### In Components

```typescript
import { buildApiUrl } from '../config/api';

// In your component
const response = await fetch(buildApiUrl('/api/endpoint'));
```

```typescript
import { buildWsUrl } from '../config/api';

// For WebSocket
const ws = new WebSocket(buildWsUrl('/ws/updates'));
```

## Portability Features

### No System Modifications Required

The configuration system is fully contained within the app directory:

- ✅ No `/etc/hosts` modifications
- ✅ No system environment variables
- ✅ No DNS configuration
- ✅ No hosts file editing

### Easy to Move

To move PokerTool to a new machine:

1. Copy the entire directory
2. Update `public/config.json` (if needed)
3. Done!

### Network Flexibility

Works in various network scenarios:

- Local development (localhost)
- Same network (LAN IPs)
- Remote access (WAN/VPN)
- Docker containers
- Cloud deployment

## Troubleshooting

### Frontend Can't Connect to Backend

**Check configuration:**
```bash
# View current config
cat pokertool-frontend/public/config.json

# Or check browser console for config logs
```

**Verify backend is running:**
```bash
curl http://localhost:5001/health
```

**Check ports:**
```bash
lsof -i :5001  # API server
lsof -i :8000  # WebSocket server
```

### Configuration Not Taking Effect

1. **Clear browser cache** - Config is cached for performance
2. **Restart dev server** - If using .env variables
3. **Check file location** - Must be `public/config.json`
4. **Verify JSON syntax** - Invalid JSON will be ignored

### Auto-Detection Not Working

Check browser console for config logs:

```
[Config] Loaded runtime configuration: {...}
[Config] No runtime config found, using defaults
```

## Best Practices

### For Development

Use `.env.local`:
```bash
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=http://localhost:8000
```

### For Distribution

Use `config.json.example` as a template:
```bash
cp public/config.json.example public/config.json
# Edit as needed
```

### For Production

1. Build once: `npm run build`
2. Deploy build folder
3. Add `config.json` to build/public/
4. Configure per environment

## Security Notes

- ✅ `config.json` is git-ignored
- ✅ `.env.local` is git-ignored
- ❌ Don't commit sensitive URLs
- ❌ Don't put credentials in config files
- ✅ Use environment-specific configs

## Files

- `src/config/api.ts` - Configuration module
- `public/config.json.example` - Template
- `.env.example` - Environment template
- `.gitignore` - Ignores local configs

## Priority Summary

```
1. REACT_APP_API_URL env variable
2. config.json apiUrl
3. Auto-detected from window.location
4. Default: http://localhost:5001
```

The same priority applies for WebSocket URLs.
