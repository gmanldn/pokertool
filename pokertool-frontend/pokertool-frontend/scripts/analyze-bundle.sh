#!/bin/bash
# Bundle size analysis script  

echo "🔍 Analyzing React bundle size..."
echo "================================"

# Build with source maps
GENERATE_SOURCEMAP=true npm run build

echo ""
echo "📊 Bundle Statistics:"
du -h build/static/js/*.js | sort -hr | head -20

echo ""
echo "💡 Check for large chunks >200KB"
find build/static/js -name "*.js" -size +200k

echo ""
echo "Run: npx source-map-explorer build/static/js/*.js"
