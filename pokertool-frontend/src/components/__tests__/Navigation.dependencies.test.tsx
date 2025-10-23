/**
 * Navigation Component - Dependencies Test
 * 
 * This test file ensures that all required dependencies for the Navigation
 * component are properly installed and can be imported without errors.
 * 
 * This prevents the "Cannot read properties of null (reading 'useContext')"
 * error that occurs when react-i18next is missing or has version conflicts.
 */

import { describe, it, expect } from '@jest/globals';

describe('Navigation Dependencies', () => {
  it('should have react-i18next installed', () => {
    expect(() => {
      require('react-i18next');
    }).not.toThrow();
  });

  it('should have i18next installed', () => {
    expect(() => {
      require('i18next');
    }).not.toThrow();
  });

  it('should have i18next-browser-languagedetector installed', () => {
    expect(() => {
      require('i18next-browser-languagedetector');
    }).not.toThrow();
  });

  it('should be able to import useTranslation hook', () => {
    const { useTranslation } = require('react-i18next');
    expect(useTranslation).toBeDefined();
    expect(typeof useTranslation).toBe('function');
  });

  it('should be able to import initReactI18next', () => {
    const { initReactI18next } = require('react-i18next');
    expect(initReactI18next).toBeDefined();
  });

  it('should have i18n properly initialized', () => {
    const i18n = require('../../i18n/i18n').default;
    expect(i18n).toBeDefined();
    expect(i18n.t).toBeDefined();
    expect(typeof i18n.t).toBe('function');
  });

  it('should have React and ReactDOM at compatible versions', () => {
    const React = require('react');
    const ReactDOM = require('react-dom');
    
    expect(React.version).toBeDefined();
    expect(ReactDOM.version).toBeDefined();
    
    // React 18.x requires matching ReactDOM 18.x
    const reactMajor = parseInt(React.version.split('.')[0]);
    const reactDOMMajor = parseInt(ReactDOM.version.split('.')[0]);
    
    expect(reactMajor).toBe(reactDOMMajor);
  });

  it('should have @mui/material installed and compatible with React', () => {
    expect(() => {
      require('@mui/material');
    }).not.toThrow();
  });

  it('should have react-router-dom installed', () => {
    expect(() => {
      const { useNavigate, useLocation } = require('react-router-dom');
      expect(useNavigate).toBeDefined();
      expect(useLocation).toBeDefined();
    }).not.toThrow();
  });
});
