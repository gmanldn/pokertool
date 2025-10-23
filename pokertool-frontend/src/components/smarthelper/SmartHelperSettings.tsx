/**
 * SmartHelper Settings Panel
 *
 * Centralized configuration for all SmartHelper features including:
 * - GTO/Exploitative strategy preference
 * - Confidence threshold settings
 * - Chart display preferences
 * - Notification preferences
 */
import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Switch,
  Slider,
  FormControlLabel,
  Divider,
  Chip,
  ToggleButtonGroup,
  ToggleButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Menu,
  MenuItem,
  Snackbar,
  Alert
} from '@mui/material';
import {
  Settings,
  ExpandMore,
  Psychology,
  BarChart,
  Notifications,
  Visibility,
  Download,
  Upload,
  MoreVert
} from '@mui/icons-material';
import {
  exportSettings,
  importSettings,
  copySettingsToClipboard,
  importSettingsFromClipboard,
  exportSettingsAsURL
} from '../../utils/settingsExporter';

export interface SmartHelperConfig {
  // Strategy Settings
  strategyMode: 'gto' | 'exploitative' | 'balanced';
  exploitativeWeight: number; // 0-100%, how much to deviate from GTO

  // Confidence Thresholds
  minConfidenceToShow: number; // 0-100%, minimum confidence to display recommendations
  minConfidenceToHighlight: number; // 0-100%, minimum confidence for visual emphasis

  // Chart Display Preferences
  showEquityChart: boolean;
  showRangeAnalyzer: boolean;
  showOpponentProfiles: boolean;
  showDecisionFactors: boolean;
  showPotOdds: boolean;
  showImpliedOdds: boolean;

  // Notification Preferences
  enableSoundAlerts: boolean;
  enableVisualAlerts: boolean;
  alertOnHighConfidence: boolean; // Alert when confidence > 90%
  alertOnExploitOpportunity: boolean; // Alert when EV gain > 0.3

  // Performance Settings
  autoCollapsePanels: boolean;
  enableAnimations: boolean;
  refreshRate: number; // milliseconds, how often to recalculate
}

interface SmartHelperSettingsProps {
  initialConfig?: Partial<SmartHelperConfig>;
  onConfigChange?: (config: SmartHelperConfig) => void;
}

const defaultConfig: SmartHelperConfig = {
  strategyMode: 'balanced',
  exploitativeWeight: 50,
  minConfidenceToShow: 30,
  minConfidenceToHighlight: 70,
  showEquityChart: true,
  showRangeAnalyzer: true,
  showOpponentProfiles: true,
  showDecisionFactors: true,
  showPotOdds: true,
  showImpliedOdds: true,
  enableSoundAlerts: false,
  enableVisualAlerts: true,
  alertOnHighConfidence: true,
  alertOnExploitOpportunity: true,
  autoCollapsePanels: false,
  enableAnimations: true,
  refreshRate: 1000
};

export const SmartHelperSettings: React.FC<SmartHelperSettingsProps> = React.memo(({
  initialConfig = {},
  onConfigChange
}) => {
  const [config, setConfig] = useState<SmartHelperConfig>({
    ...defaultConfig,
    ...initialConfig
  });
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateConfig = (updates: Partial<SmartHelperConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    if (onConfigChange) {
      onConfigChange(newConfig);
    }
  };

  const handleExport = () => {
    exportSettings(config);
    setSnackbar({ open: true, message: 'Settings exported successfully!', severity: 'success' });
    setAnchorEl(null);
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const importedSettings = await importSettings(file);
      updateConfig(importedSettings);
      setSnackbar({ open: true, message: 'Settings imported successfully!', severity: 'success' });
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to import settings',
        severity: 'error'
      });
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCopyToClipboard = async () => {
    try {
      await copySettingsToClipboard(config);
      setSnackbar({ open: true, message: 'Settings copied to clipboard!', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to copy settings', severity: 'error' });
    }
    setAnchorEl(null);
  };

  const handleImportFromClipboard = async () => {
    try {
      const importedSettings = await importSettingsFromClipboard();
      updateConfig(importedSettings);
      setSnackbar({ open: true, message: 'Settings imported from clipboard!', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to import from clipboard', severity: 'error' });
    }
    setAnchorEl(null);
  };

  const handleCopyShareableURL = () => {
    const url = exportSettingsAsURL(config);
    navigator.clipboard.writeText(url);
    setSnackbar({ open: true, message: 'Shareable URL copied to clipboard!', severity: 'success' });
    setAnchorEl(null);
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        backgroundColor: 'rgba(33, 33, 33, 0.9)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 2
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Settings sx={{ color: 'primary.main', fontSize: 24 }} />
        <Typography variant="subtitle1" fontWeight="bold" color="white">
          SmartHelper Settings
        </Typography>
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            style={{ display: 'none' }}
            onChange={handleImport}
          />
          <Button
            size="small"
            startIcon={<Upload />}
            onClick={() => fileInputRef.current?.click()}
            sx={{ minWidth: 'auto', px: 1 }}
          >
            Import
          </Button>
          <Button
            size="small"
            startIcon={<Download />}
            onClick={handleExport}
            sx={{ minWidth: 'auto', px: 1 }}
          >
            Export
          </Button>
          <Button
            size="small"
            onClick={(e) => setAnchorEl(e.currentTarget)}
            sx={{ minWidth: 'auto', px: 0.5 }}
          >
            <MoreVert />
          </Button>
        </Box>
      </Box>

      {/* Import/Export Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={handleCopyToClipboard}>Copy to Clipboard</MenuItem>
        <MenuItem onClick={handleImportFromClipboard}>Paste from Clipboard</MenuItem>
        <Divider />
        <MenuItem onClick={handleCopyShareableURL}>Copy Shareable URL</MenuItem>
      </Menu>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Strategy Settings */}
      <Accordion
        defaultExpanded
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          mb: 1,
          '&:before': { display: 'none' }
        }}
      >
        <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Psychology sx={{ fontSize: 20, color: 'primary.main' }} />
            <Typography variant="body2" fontWeight="bold" color="white">
              Strategy Mode
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Strategy Mode Toggle */}
            <Box>
              <Typography variant="caption" color="textSecondary" sx={{ mb: 1, display: 'block' }}>
                Select your preferred strategy approach
              </Typography>
              <ToggleButtonGroup
                value={config.strategyMode}
                exclusive
                onChange={(_, mode) => mode && updateConfig({ strategyMode: mode })}
                fullWidth
                size="small"
              >
                <ToggleButton value="gto">
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="caption" fontWeight="bold">GTO</Typography>
                    <Typography variant="caption" sx={{ display: 'block', fontSize: '9px' }}>
                      Game Theory Optimal
                    </Typography>
                  </Box>
                </ToggleButton>
                <ToggleButton value="balanced">
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="caption" fontWeight="bold">Balanced</Typography>
                    <Typography variant="caption" sx={{ display: 'block', fontSize: '9px' }}>
                      GTO + Exploitative
                    </Typography>
                  </Box>
                </ToggleButton>
                <ToggleButton value="exploitative">
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="caption" fontWeight="bold">Exploitative</Typography>
                    <Typography variant="caption" sx={{ display: 'block', fontSize: '9px' }}>
                      Maximum Deviation
                    </Typography>
                  </Box>
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>

            {/* Exploitative Weight Slider */}
            {config.strategyMode !== 'gto' && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="caption" color="textSecondary">
                    Exploitative Weight
                  </Typography>
                  <Chip
                    label={`${config.exploitativeWeight}%`}
                    size="small"
                    sx={{ height: 18, fontSize: '10px' }}
                  />
                </Box>
                <Slider
                  value={config.exploitativeWeight}
                  onChange={(_, value) => updateConfig({ exploitativeWeight: value as number })}
                  min={0}
                  max={100}
                  step={5}
                  marks={[
                    { value: 0, label: 'GTO' },
                    { value: 50, label: '50%' },
                    { value: 100, label: 'Max' }
                  ]}
                  sx={{ color: 'primary.main' }}
                />
                <Typography variant="caption" color="textSecondary" sx={{ fontSize: '9px' }}>
                  Higher values = more aggressive exploitation of opponent weaknesses
                </Typography>
              </Box>
            )}
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Confidence Thresholds */}
      <Accordion
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          mb: 1,
          '&:before': { display: 'none' }
        }}
      >
        <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BarChart sx={{ fontSize: 20, color: 'primary.main' }} />
            <Typography variant="body2" fontWeight="bold" color="white">
              Confidence Thresholds
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Min Confidence to Show */}
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  Minimum Confidence to Show
                </Typography>
                <Chip
                  label={`${config.minConfidenceToShow}%`}
                  size="small"
                  sx={{ height: 18, fontSize: '10px' }}
                />
              </Box>
              <Slider
                value={config.minConfidenceToShow}
                onChange={(_, value) => updateConfig({ minConfidenceToShow: value as number })}
                min={0}
                max={100}
                step={5}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 50, label: '50%' },
                  { value: 100, label: '100%' }
                ]}
                sx={{ color: 'primary.main' }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ fontSize: '9px' }}>
                Hide recommendations below this confidence level
              </Typography>
            </Box>

            {/* Min Confidence to Highlight */}
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  Minimum Confidence to Highlight
                </Typography>
                <Chip
                  label={`${config.minConfidenceToHighlight}%`}
                  size="small"
                  sx={{ height: 18, fontSize: '10px', backgroundColor: '#4caf50', color: 'white' }}
                />
              </Box>
              <Slider
                value={config.minConfidenceToHighlight}
                onChange={(_, value) => updateConfig({ minConfidenceToHighlight: value as number })}
                min={0}
                max={100}
                step={5}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 70, label: '70%' },
                  { value: 100, label: '100%' }
                ]}
                sx={{ color: '#4caf50' }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ fontSize: '9px' }}>
                Add visual emphasis to high-confidence recommendations
              </Typography>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Chart Display Preferences */}
      <Accordion
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          mb: 1,
          '&:before': { display: 'none' }
        }}
      >
        <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Visibility sx={{ fontSize: 20, color: 'primary.main' }} />
            <Typography variant="body2" fontWeight="bold" color="white">
              Chart Display
            </Typography>
            <Chip
              label={`${Object.values(config).filter((v, i) => i >= 6 && i < 12 && v === true).length}/6 visible`}
              size="small"
              sx={{ height: 16, fontSize: '9px', ml: 'auto' }}
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.showEquityChart}
                  onChange={(e) => updateConfig({ showEquityChart: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Equity Chart</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.showRangeAnalyzer}
                  onChange={(e) => updateConfig({ showRangeAnalyzer: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Range Analyzer</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.showOpponentProfiles}
                  onChange={(e) => updateConfig({ showOpponentProfiles: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Opponent Profiles</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.showDecisionFactors}
                  onChange={(e) => updateConfig({ showDecisionFactors: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Decision Factors</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.showPotOdds}
                  onChange={(e) => updateConfig({ showPotOdds: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Pot Odds</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.showImpliedOdds}
                  onChange={(e) => updateConfig({ showImpliedOdds: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Implied Odds</Typography>}
            />
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Notification Preferences */}
      <Accordion
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          mb: 1,
          '&:before': { display: 'none' }
        }}
      >
        <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Notifications sx={{ fontSize: 20, color: 'primary.main' }} />
            <Typography variant="body2" fontWeight="bold" color="white">
              Notifications
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.enableSoundAlerts}
                  onChange={(e) => updateConfig({ enableSoundAlerts: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Sound Alerts</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.enableVisualAlerts}
                  onChange={(e) => updateConfig({ enableVisualAlerts: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Visual Alerts</Typography>}
            />
            <Divider sx={{ my: 0.5, backgroundColor: 'rgba(255, 255, 255, 0.1)' }} />
            <FormControlLabel
              control={
                <Switch
                  checked={config.alertOnHighConfidence}
                  onChange={(e) => updateConfig({ alertOnHighConfidence: e.target.checked })}
                  size="small"
                  disabled={!config.enableVisualAlerts && !config.enableSoundAlerts}
                />
              }
              label={
                <Typography variant="caption" color={(!config.enableVisualAlerts && !config.enableSoundAlerts) ? 'textSecondary' : 'inherit'}>
                  Alert on High Confidence (&gt;90%)
                </Typography>
              }
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.alertOnExploitOpportunity}
                  onChange={(e) => updateConfig({ alertOnExploitOpportunity: e.target.checked })}
                  size="small"
                  disabled={!config.enableVisualAlerts && !config.enableSoundAlerts}
                />
              }
              label={
                <Typography variant="caption" color={(!config.enableVisualAlerts && !config.enableSoundAlerts) ? 'textSecondary' : 'inherit'}>
                  Alert on Exploit Opportunity (EV &gt;0.3)
                </Typography>
              }
            />
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Performance Settings */}
      <Accordion
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          '&:before': { display: 'none' }
        }}
      >
        <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Settings sx={{ fontSize: 20, color: 'primary.main' }} />
            <Typography variant="body2" fontWeight="bold" color="white">
              Performance
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.autoCollapsePanels}
                  onChange={(e) => updateConfig({ autoCollapsePanels: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Auto-collapse Panels</Typography>}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={config.enableAnimations}
                  onChange={(e) => updateConfig({ enableAnimations: e.target.checked })}
                  size="small"
                />
              }
              label={<Typography variant="caption">Enable Animations</Typography>}
            />

            {/* Refresh Rate */}
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  Refresh Rate
                </Typography>
                <Chip
                  label={`${config.refreshRate}ms`}
                  size="small"
                  sx={{ height: 18, fontSize: '10px' }}
                />
              </Box>
              <Slider
                value={config.refreshRate}
                onChange={(_, value) => updateConfig({ refreshRate: value as number })}
                min={250}
                max={5000}
                step={250}
                marks={[
                  { value: 250, label: '0.25s' },
                  { value: 1000, label: '1s' },
                  { value: 5000, label: '5s' }
                ]}
                sx={{ color: 'primary.main' }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ fontSize: '9px' }}>
                How often to recalculate recommendations (lower = more CPU usage)
              </Typography>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
});

SmartHelperSettings.displayName = 'SmartHelperSettings';
