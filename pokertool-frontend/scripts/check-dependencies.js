#!/usr/bin/env node

/**
 * Dependency Checker Script
 * 
 * This script validates that all required dependencies are present in package.json
 * and can prevent build failures due to missing dependencies.
 * 
 * Run this script:
 * - Before committing changes
 * - In CI/CD pipelines
 * - After pulling new changes
 */

const fs = require('fs');
const path = require('path');

// Define critical dependencies that must be present
const REQUIRED_DEPENDENCIES = {
  'react': 'React core library',
  'react-dom': 'React DOM renderer',
  'react-i18next': 'React i18n internationalization',
  'i18next': 'i18n core library',
  'i18next-browser-languagedetector': 'i18n browser language detection',
  '@mui/material': 'Material-UI components',
  '@mui/icons-material': 'Material-UI icons',
  'react-router-dom': 'React routing',
  'react-redux': 'React Redux bindings',
  '@reduxjs/toolkit': 'Redux Toolkit',
};

// Version compatibility checks
const VERSION_CHECKS = [
  {
    name: 'React and ReactDOM version sync',
    check: (deps) => {
      const reactVersion = deps['react'];
      const reactDomVersion = deps['react-dom'];
      if (!reactVersion || !reactDomVersion) return false;
      
      const reactMajor = reactVersion.match(/\d+/)?.[0];
      const reactDomMajor = reactDomVersion.match(/\d+/)?.[0];
      
      return reactMajor === reactDomMajor;
    },
    errorMessage: 'React and ReactDOM must have the same major version'
  }
];

function checkDependencies() {
  console.log('🔍 Checking dependencies...\n');
  
  const packageJsonPath = path.join(__dirname, '..', 'package.json');
  
  if (!fs.existsSync(packageJsonPath)) {
    console.error('❌ package.json not found!');
    process.exit(1);
  }
  
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
  
  let hasErrors = false;
  
  // Check for required dependencies
  console.log('📦 Checking required dependencies...');
  for (const [dep, description] of Object.entries(REQUIRED_DEPENDENCIES)) {
    if (!dependencies[dep]) {
      console.error(`❌ Missing required dependency: ${dep}`);
      console.error(`   Description: ${description}`);
      hasErrors = true;
    } else {
      console.log(`✅ ${dep} (${dependencies[dep]})`);
    }
  }
  
  console.log('\n🔄 Checking version compatibility...');
  for (const check of VERSION_CHECKS) {
    if (!check.check(dependencies)) {
      console.error(`❌ ${check.name}: ${check.errorMessage}`);
      hasErrors = true;
    } else {
      console.log(`✅ ${check.name}`);
    }
  }
  
  if (hasErrors) {
    console.error('\n❌ Dependency check failed!');
    console.error('   Run: npm install to fix missing dependencies');
    process.exit(1);
  }
  
  console.log('\n✅ All dependency checks passed!');
}

// Run the check
checkDependencies();
