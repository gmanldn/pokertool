/**
 * Settings Import/Export Utility
 *
 * Allows users to export their SmartHelper settings to a JSON file
 * and import settings from a previously exported file.
 * This enables sharing settings between devices or backing up preferences.
 */

import { SmartHelperConfig } from '../components/smarthelper/SmartHelperSettings';

export interface ExportedSettings {
  version: string;
  exportDate: string;
  settings: SmartHelperConfig;
  metadata?: {
    deviceName?: string;
    username?: string;
    notes?: string;
  };
}

/**
 * Export settings to a downloadable JSON file
 */
export const exportSettings = (
  settings: SmartHelperConfig,
  metadata?: ExportedSettings['metadata']
): void => {
  const exportData: ExportedSettings = {
    version: '1.0.0',
    exportDate: new Date().toISOString(),
    settings,
    metadata
  };

  const jsonString = JSON.stringify(exportData, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `smarthelper-settings-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Import settings from a JSON file
 */
export const importSettings = (file: File): Promise<SmartHelperConfig> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const parsed: ExportedSettings = JSON.parse(content);

        // Validate the structure
        if (!parsed.settings || !parsed.version) {
          throw new Error('Invalid settings file format');
        }

        // Validate required fields
        validateSettings(parsed.settings);

        resolve(parsed.settings);
      } catch (error) {
        reject(new Error(`Failed to import settings: ${error instanceof Error ? error.message : 'Unknown error'}`));
      }
    };

    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };

    reader.readAsText(file);
  });
};

/**
 * Validate settings structure
 */
const validateSettings = (settings: Partial<SmartHelperConfig>): void => {
  const requiredFields: (keyof SmartHelperConfig)[] = [
    'strategyMode',
    'exploitativeWeight',
    'minConfidenceToShow',
    'minConfidenceToHighlight'
  ];

  for (const field of requiredFields) {
    if (!(field in settings)) {
      throw new Error(`Missing required field: ${field}`);
    }
  }

  // Validate strategy mode
  if (!['gto', 'exploitative', 'balanced'].includes(settings.strategyMode as string)) {
    throw new Error('Invalid strategy mode');
  }

  // Validate ranges
  if (typeof settings.exploitativeWeight === 'number' &&
      (settings.exploitativeWeight < 0 || settings.exploitativeWeight > 100)) {
    throw new Error('Exploitative weight must be between 0 and 100');
  }

  if (typeof settings.minConfidenceToShow === 'number' &&
      (settings.minConfidenceToShow < 0 || settings.minConfidenceToShow > 100)) {
    throw new Error('Min confidence to show must be between 0 and 100');
  }

  if (typeof settings.minConfidenceToHighlight === 'number' &&
      (settings.minConfidenceToHighlight < 0 || settings.minConfidenceToHighlight > 100)) {
    throw new Error('Min confidence to highlight must be between 0 and 100');
  }
};

/**
 * Copy settings to clipboard as JSON
 */
export const copySettingsToClipboard = async (settings: SmartHelperConfig): Promise<void> => {
  const exportData: ExportedSettings = {
    version: '1.0.0',
    exportDate: new Date().toISOString(),
    settings
  };

  const jsonString = JSON.stringify(exportData, null, 2);
  await navigator.clipboard.writeText(jsonString);
};

/**
 * Import settings from clipboard
 */
export const importSettingsFromClipboard = async (): Promise<SmartHelperConfig> => {
  const clipboardText = await navigator.clipboard.readText();
  const parsed: ExportedSettings = JSON.parse(clipboardText);

  if (!parsed.settings || !parsed.version) {
    throw new Error('Invalid settings format in clipboard');
  }

  validateSettings(parsed.settings);
  return parsed.settings;
};

/**
 * Export settings as a shareable URL (base64 encoded)
 */
export const exportSettingsAsURL = (settings: SmartHelperConfig): string => {
  const exportData: ExportedSettings = {
    version: '1.0.0',
    exportDate: new Date().toISOString(),
    settings
  };

  const jsonString = JSON.stringify(exportData);
  const base64 = btoa(jsonString);
  const currentURL = new URL(window.location.href);
  currentURL.searchParams.set('importSettings', base64);
  return currentURL.toString();
};

/**
 * Import settings from URL parameter
 */
export const importSettingsFromURL = (): SmartHelperConfig | null => {
  const params = new URLSearchParams(window.location.search);
  const settingsParam = params.get('importSettings');

  if (!settingsParam) {
    return null;
  }

  try {
    const jsonString = atob(settingsParam);
    const parsed: ExportedSettings = JSON.parse(jsonString);

    if (!parsed.settings || !parsed.version) {
      throw new Error('Invalid settings format in URL');
    }

    validateSettings(parsed.settings);
    return parsed.settings;
  } catch (error) {
    console.error('Failed to import settings from URL:', error);
    return null;
  }
};

/**
 * Save settings to localStorage with a custom name
 */
export const saveSettingsProfile = (name: string, settings: SmartHelperConfig): void => {
  const profiles = getSettingsProfiles();
  profiles[name] = {
    settings,
    savedAt: new Date().toISOString()
  };
  localStorage.setItem('smarthelper-profiles', JSON.stringify(profiles));
};

/**
 * Load settings from a named profile
 */
export const loadSettingsProfile = (name: string): SmartHelperConfig | null => {
  const profiles = getSettingsProfiles();
  return profiles[name]?.settings || null;
};

/**
 * Get all saved settings profiles
 */
export const getSettingsProfiles = (): Record<string, { settings: SmartHelperConfig; savedAt: string }> => {
  const stored = localStorage.getItem('smarthelper-profiles');
  return stored ? JSON.parse(stored) : {};
};

/**
 * Delete a settings profile
 */
export const deleteSettingsProfile = (name: string): void => {
  const profiles = getSettingsProfiles();
  delete profiles[name];
  localStorage.setItem('smarthelper-profiles', JSON.stringify(profiles));
};

/**
 * Merge imported settings with current settings
 * Allows selective import of only certain settings categories
 */
export const mergeSettings = (
  current: SmartHelperConfig,
  imported: Partial<SmartHelperConfig>,
  categories?: {
    strategy?: boolean;
    confidence?: boolean;
    charts?: boolean;
    notifications?: boolean;
    performance?: boolean;
  }
): SmartHelperConfig => {
  if (!categories) {
    // Import all settings
    return { ...current, ...imported };
  }

  const merged = { ...current };

  if (categories.strategy) {
    merged.strategyMode = imported.strategyMode ?? merged.strategyMode;
    merged.exploitativeWeight = imported.exploitativeWeight ?? merged.exploitativeWeight;
  }

  if (categories.confidence) {
    merged.minConfidenceToShow = imported.minConfidenceToShow ?? merged.minConfidenceToShow;
    merged.minConfidenceToHighlight = imported.minConfidenceToHighlight ?? merged.minConfidenceToHighlight;
  }

  if (categories.charts) {
    merged.showEquityChart = imported.showEquityChart ?? merged.showEquityChart;
    merged.showRangeAnalyzer = imported.showRangeAnalyzer ?? merged.showRangeAnalyzer;
    merged.showOpponentProfiles = imported.showOpponentProfiles ?? merged.showOpponentProfiles;
    merged.showDecisionFactors = imported.showDecisionFactors ?? merged.showDecisionFactors;
    merged.showPotOdds = imported.showPotOdds ?? merged.showPotOdds;
    merged.showImpliedOdds = imported.showImpliedOdds ?? merged.showImpliedOdds;
  }

  if (categories.notifications) {
    merged.enableSoundAlerts = imported.enableSoundAlerts ?? merged.enableSoundAlerts;
    merged.enableVisualAlerts = imported.enableVisualAlerts ?? merged.enableVisualAlerts;
    merged.alertOnHighConfidence = imported.alertOnHighConfidence ?? merged.alertOnHighConfidence;
    merged.alertOnExploitOpportunity = imported.alertOnExploitOpportunity ?? merged.alertOnExploitOpportunity;
  }

  if (categories.performance) {
    merged.autoCollapsePanels = imported.autoCollapsePanels ?? merged.autoCollapsePanels;
    merged.enableAnimations = imported.enableAnimations ?? merged.enableAnimations;
    merged.refreshRate = imported.refreshRate ?? merged.refreshRate;
  }

  return merged;
};
