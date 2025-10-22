# PokerTool Quick Start Guide

Get up and running with PokerTool in **less than 5 minutes**.

## Prerequisites

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **8GB+ RAM** recommended
- **5GB+ disk space**

## Quick Install

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/pokertool.git
cd pokertool
```

### 2. Install Dependencies

**Backend:**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

**Frontend:**
```bash
cd pokertool-frontend
npm install
cd ..
```

### 3. Start PokerTool

**Option A: Using start script (Recommended)**
```bash
python scripts/start.py
```

**Option B: Manual start**

Terminal 1 (Backend):
```bash
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python -m uvicorn pokertool.api:app --reload --port 5001
```

Terminal 2 (Frontend):
```bash
cd pokertool-frontend
npm start
```

### 4. Open Your Browser

Navigate to: **http://localhost:3000**

You should see the PokerTool dashboard! 🎉

## First Session

### 1. Start a Poker Client

Open your poker client (PokerStars, GGPoker, 888poker, etc.)

### 2. Join a Table

- PokerTool automatically detects tables
- Card detection starts immediately
- Real-time hand analysis appears in the dashboard

### 3. View Your Stats

- Navigate to the **Stats** tab
- See hand history
- Analyze your performance
- Review AI recommendations

## Quick Features Tour

### 📊 Dashboard
- Real-time table detection
- Active hands display
- System status monitoring

### 🎯 SmartHelper (AI Assistant)
- GTO-based recommendations
- Pot odds calculations
- Equity analysis
- Opponent modeling

### 📈 Statistics
- Win rate tracking
- VPIP/PFR statistics
- Hand range analysis
- Session summaries

### 🎮 Hand Replay
- Review past hands
- Analyze decision points
- Compare with GTO strategy

## Troubleshooting

### Port Already in Use

If port 5001 or 3000 is in use:

```bash
# Find and kill process on macOS/Linux
lsof -ti:5001 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# On Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

### Table Not Detected

1. Ensure poker client is running
2. Check that table window is visible
3. Verify screen permissions (macOS)
4. Try manually refreshing detection

### Dependencies Missing

```bash
# Reinstall backend dependencies
pip install -r requirements.txt --force-reinstall

# Reinstall frontend dependencies
cd pokertool-frontend
rm -rf node_modules package-lock.json
npm install
```

### Database Errors

```bash
# Reset database (WARNING: deletes all data)
rm -rf data/poker.db
python scripts/init_db.py
```

## Configuration

### Optional: Environment Variables

Create `.env` file in project root:

```env
# Database
DATABASE_URL=sqlite:///data/poker.db

# API
JWT_SECRET_KEY=your-secret-key-here

# Logging
LOG_LEVEL=INFO

# Features
ENABLE_AI_FEATURES=true
ENABLE_VECTOR_DB=true
```

### Optional: Configure Poker Sites

Edit `config/poker_sites.json` to add your preferred sites:

```json
{
  "sites": [
    {
      "name": "PokerStars",
      "enabled": true,
      "window_pattern": ".*PokerStars.*"
    }
  ]
}
```

## Next Steps

### 📚 Full Documentation
- [Complete Installation Guide](./INSTALL.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [API Documentation](./api/README.md)
- [Contributing Guide](../CONTRIBUTING.md)

### 🧪 Running Tests
```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd pokertool-frontend
npm test

# E2E tests
npm run test:e2e
```

### 🔧 Development
```bash
# Run with hot reload
python scripts/start.py --dev

# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/start.py
```

### 🚀 Production Deployment
See [Deployment Guide](./DEPLOYMENT.md) for:
- Docker deployment
- Cloud hosting (AWS, GCP, Azure)
- Nginx configuration
- SSL/HTTPS setup

## Common Commands

```bash
# Start PokerTool
python scripts/start.py

# Run tests
pytest tests/

# Update dependencies
pip install -r requirements.txt --upgrade
npm update

# Build frontend for production
cd pokertool-frontend
npm run build

# Check code quality
black src/ --check
flake8 src/
npm run lint
```

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/pokertool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/pokertool/discussions)
- **Email**: support@pokertool.com

## Tips for Best Experience

1. **Keep software updated**: Run `git pull` regularly
2. **Use latest Python/Node**: Older versions may have issues
3. **Close other screen capture apps**: Prevents detection conflicts
4. **Grant screen permissions**: Required for table detection (macOS)
5. **Run on SSD**: Faster database and better performance

## What's Next?

Now that you're up and running:

1. ✅ Play a few hands to test detection
2. ✅ Review the SmartHelper recommendations
3. ✅ Explore the statistics dashboard
4. ✅ Customize settings to your preferences
5. ✅ Join the community and share feedback!

---

**Happy Grinding! 🎰**

*For detailed setup instructions, see [INSTALL.md](./INSTALL.md)*
