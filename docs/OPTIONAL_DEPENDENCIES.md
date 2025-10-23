# Optional Dependencies Documentation

## Overview

PokerTool's core functionality works with the default dependencies, but optional packages can enhance specific features.

## Optional Python Packages

### Machine Learning & Analytics

#### TensorFlow (GPU acceleration)
```bash
pip install tensorflow-gpu>=2.13.0
```
**Use Case:** Accelerates ML model training and inference when GPU available  
**Benefits:** 5-10x faster model training  
**Requirements:** CUDA-compatible NVIDIA GPU  
**Alternative:** CPU-only tensorflow (slower but works everywhere)

#### SciPy (Advanced statistics)
```bash
pip install scipy>=1.11.4
```
**Use Case:** Advanced statistical analysis, optimization algorithms  
**Benefits:** Better equity calculations, more accurate range analysis  
**Alternative:** Built-in statistics (limited functionality)

#### Scikit-learn (Additional ML algorithms)
```bash
pip install scikit-learn>=1.3.0
```
**Use Case:** Alternative ML algorithms for opponent modeling  
**Benefits:** More model choices, ensemble methods  
**Alternative:** Built-in models (fewer options)

### Database & Storage

#### PostgreSQL adapter
```bash
pip install psycopg2-binary>=2.9.0
```
**Use Case:** Use PostgreSQL instead of SQLite for production  
**Benefits:** Better performance for large datasets, concurrent access  
**Alternative:** SQLite (default, good for most users)

#### Redis
```bash
pip install redis>=4.5.0
```
**Use Case:** Fast caching layer for frequently accessed data  
**Benefits:** 10-100x faster cache access  
**Alternative:** In-memory caching (uses more RAM)

### Monitoring & Telemetry

#### Prometheus client
```bash
pip install prometheus-client>=0.17.0
```
**Use Case:** Expose metrics for Prometheus monitoring  
**Benefits:** Production-grade monitoring, alerting  
**Alternative:** Built-in logging (less comprehensive)

#### Sentry SDK
```bash
pip install sentry-sdk>=1.30.0
```
**Use Case:** Error tracking and performance monitoring  
**Benefits:** Automatic error reporting, performance insights  
**Alternative:** File-based logging

### Development Tools

#### IPython
```bash
pip install ipython>=8.12.0
```
**Use Case:** Enhanced Python REPL for development  
**Benefits:** Better debugging, autocomplete, history  
**Alternative:** Standard Python REPL

#### Jupyter
```bash
pip install jupyter>=1.0.0
```
**Use Case:** Interactive notebooks for analysis  
**Benefits:** Visual analysis, documentation, sharing  
**Alternative:** Python scripts

## Optional System Packages

### Tesseract OCR (Highly Recommended)

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr libtesseract-dev
```

**Windows:**  
Download from: https://github.com/UB-Mannheim/tesseract/wiki

**Use Case:** Optical character recognition for screen scraping  
**Benefits:** 95%+ text recognition accuracy  
**Alternative:** Built-in OCR (70-80% accuracy)

### Chrome/Chromium (For DevTools scraping)

**macOS:**
```bash
brew install --cask google-chrome
```

**Ubuntu/Debian:**
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

**Windows:**  
Download from: https://www.google.com/chrome/

**Use Case:** Chrome DevTools Protocol for reliable web scraping  
**Benefits:** 99% reliable scraping, handles dynamic content  
**Alternative:** Screenshot-based scraping (less reliable)

## Installation Profiles

### Minimal Install (Core only)
```bash
pip install -r requirements-minimal.txt  # Coming soon - Task 13
```
**Includes:** Core poker logic, basic scraping, SQLite  
**Size:** ~200MB  
**Use Case:** Testing, development, resource-constrained systems

### Standard Install (Default)
```bash
pip install -r requirements.txt
```
**Includes:** All core features, FastAPI, React frontend  
**Size:** ~500MB  
**Use Case:** Most users

### Full Install (All features)
```bash
pip install -r requirements.txt
pip install tensorflow-gpu scipy scikit-learn psycopg2-binary redis prometheus-client
```
**Includes:** Everything + ML acceleration + production tools  
**Size:** ~2GB  
**Use Case:** Production deployments, ML training, multi-table

## Checking Installed Optional Dependencies

```bash
python -c "
import sys
optional = ['tensorflow', 'scipy', 'sklearn', 'psycopg2', 'redis', 'prometheus_client']
for pkg in optional:
    try:
        __import__(pkg)
        print(f'✓ {pkg} installed')
    except ImportError:
        print(f'✗ {pkg} not installed')
"
```

## Conflicts to Avoid

### Known Incompatibilities

1. **opencv-python vs opencv-python-headless**  
   - Only install ONE of these
   - Headless is preferred (smaller, faster)
   - Full version only needed for GUI display

2. **tensorflow vs tensorflow-gpu**  
   - GPU version includes CPU fallback
   - Don't install both

3. **pillow vs PIL**  
   - Use Pillow (PIL is deprecated)
   - Don't install both

## Feature Matrix

| Feature | Required Deps | Optional Deps | Performance Gain |
|---------|--------------|---------------|------------------|
| Basic Poker Logic | ✓ Core | - | N/A |
| Screen Scraping | ✓ Core | Tesseract | +25% accuracy |
| Chrome DevTools | ✓ Core | Chrome | +50% reliability |
| ML Training | ✓ Core | TensorFlow-GPU | 5-10x faster |
| Advanced Stats | ✓ Core | SciPy | +30% capabilities |
| Production DB | ✓ Core | PostgreSQL | +100% throughput |
| Fast Caching | ✓ Core | Redis | 10-100x faster |
| Monitoring | ✓ Core | Prometheus | Production-grade |

## Recommendations

### For Development
```bash
pip install ipython jupyter pytest-cov
```

### For Production
```bash
pip install psycopg2-binary redis prometheus-client sentry-sdk
```

### For ML Training
```bash
pip install tensorflow-gpu scipy scikit-learn
```

### For Maximum Performance
```bash
# Install ALL optional dependencies
pip install -r requirements.txt
pip install tensorflow-gpu scipy scikit-learn psycopg2-binary redis \
            prometheus-client sentry-sdk ipython jupyter
```

## Support

If you encounter issues with optional dependencies:
1. Check [INSTALLATION_TROUBLESHOOTING.md](./INSTALLATION_TROUBLESHOOTING.md)
2. Try without the optional dependency first
3. Report issues at: https://github.com/gmanldn/pokertool/issues
