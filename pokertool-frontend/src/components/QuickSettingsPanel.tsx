import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Slider,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Settings,
  Close,
  Brightness6,
  VolumeUp,
  Speed,
  Visibility,
  Timer,
  Psychology,
  Notifications,
  Language,
  Palette,
  Save,
  RestoreOutlined,
  ChevronRight,
  ChevronLeft,
  Dashboard,
  AutorenewOutlined,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { 
  updateSettings,
  ThemeMode,
  AdviceDetailLevel,
  SettingsState 
} from '../store/slices/settingsSlice';
import { AppDispatch, RootState } from '../store';

interface QuickSettingsPanelProps {
  open?: boolean;
  onClose?: () => void;
  position?: 'left' | 'right';
  variant?: 'permanent' | 'persistent' | 'temporary';
}

interface QuickSettings extends Partial<SettingsState> {
  // Additional quick settings
  fontSize: number;
  autoHideDelay: number;
  useHardwareAcceleration: boolean;
  reducedMotion: boolean;
  language: string;
}

const defaultSettings: QuickSettings = {
  theme: 'dark',
  compactMode: false,
  fontSize: 100,
  adviceDetailLevel: 'detailed',
  updateFrequency: 2,
  showConfidenceBreakdown: true,
  showAlternatives: true,
  soundEnabled: true,
  decisionTimerAlert: true,
  soundVolume: 50,
  autoHideInactive: false,
  autoHideDelay: 10,
  useHardwareAcceleration: true,
  reducedMotion: false,
  language: 'en',
  brightness: 100,
  blueLightReduction: false,
};

export const QuickSettingsPanel: React.FC<QuickSettingsPanelProps> = ({
  open = false,
  onClose,
  position = 'right',
  variant = 'temporary',
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const savedSettings = useSelector((state: RootState) => state.settings);
  const [settings, setSettings] = useState<QuickSettings>({
    ...defaultSettings,
    ...savedSettings,
    fontSize: defaultSettings.fontSize,
    autoHideDelay: defaultSettings.autoHideDelay,
    useHardwareAcceleration: defaultSettings.useHardwareAcceleration,
    reducedMotion: defaultSettings.reducedMotion,
    language: defaultSettings.language,
  });
  const [hasChanges, setHasChanges] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);

  // Load settings from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('quickSettings');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setSettings({ ...defaultSettings, ...parsed });
      } catch (error) {
        console.error('Failed to parse settings:', error);
      }
    }
  }, []);

  // Save settings to localStorage and Redux
  const saveSettings = () => {
    localStorage.setItem('quickSettings', JSON.stringify(settings));
    // Only update settings that are part of SettingsState
    const settingsForRedux: Partial<SettingsState> = {
      theme: settings.theme,
      brightness: settings.brightness,
      blueLightReduction: settings.blueLightReduction,
      adviceDetailLevel: settings.adviceDetailLevel,
      updateFrequency: settings.updateFrequency,
      showAlternatives: settings.showAlternatives,
      showConfidenceBreakdown: settings.showConfidenceBreakdown,
      soundEnabled: settings.soundEnabled,
      soundVolume: settings.soundVolume,
      decisionTimerAlert: settings.decisionTimerAlert,
      compactMode: settings.compactMode,
      autoHideInactive: settings.autoHideInactive,
    };
    dispatch(updateSettings(settingsForRedux));
    setHasChanges(false);
  };

  // Update setting and mark as changed
  const updateSetting = <K extends keyof QuickSettings>(key: K, value: QuickSettings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  // Reset to defaults
  const resetToDefaults = () => {
    setSettings(defaultSettings);
    setHasChanges(true);
  };

  // Apply settings immediately (for preview)
  useEffect(() => {
    // Apply theme
    if (settings.theme) {
      document.body.setAttribute('data-theme', settings.theme);
    }
    
    // Apply font size
    document.documentElement.style.fontSize = `${settings.fontSize}%`;
    
    // Apply reduced motion
    if (settings.reducedMotion) {
      document.body.classList.add('reduced-motion');
    } else {
      document.body.classList.remove('reduced-motion');
    }
  }, [settings.theme, settings.fontSize, settings.reducedMotion]);

  const drawerWidth = collapsed ? 60 : 320;

  return (
    <Drawer
      anchor={position}
      open={open}
      onClose={onClose}
      variant={variant}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          transition: 'width 0.3s',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        {!collapsed && (
          <>
            <Box display="flex" alignItems="center" gap={1}>
              <Settings />
              <Typography variant="h6">Quick Settings</Typography>
            </Box>
            <Box display="flex" gap={0.5}>
              <IconButton size="small" onClick={() => setCollapsed(true)}>
                {position === 'left' ? <ChevronLeft /> : <ChevronRight />}
              </IconButton>
              {onClose && (
                <IconButton size="small" onClick={onClose}>
                  <Close />
                </IconButton>
              )}
            </Box>
          </>
        )}
        {collapsed && (
          <IconButton onClick={() => setCollapsed(false)}>
            <Settings />
          </IconButton>
        )}
      </Box>

      {!collapsed && (
        <>
          {/* Changes Alert */}
          {hasChanges && (
            <Alert
              severity="info"
              action={
                <Button size="small" onClick={saveSettings}>
                  Save
                </Button>
              }
              sx={{ m: 1 }}
            >
              You have unsaved changes
            </Alert>
          )}

          {/* Settings Sections */}
          <List sx={{ flex: 1, overflow: 'auto' }}>
            {/* Display Settings */}
            <ListItem>
              <ListItemIcon>
                <Brightness6 />
              </ListItemIcon>
              <ListItemText primary="Display" />
            </ListItem>
            <Box px={2}>
              {/* Theme */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Theme</InputLabel>
                <Select
                  value={settings.theme}
                  label="Theme"
                  onChange={(e) => updateSetting('theme', e.target.value as ThemeMode)}
                >
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="poker-green">Poker Green</MenuItem>
                  <MenuItem value="poker-purple">Poker Purple</MenuItem>
                  <MenuItem value="poker-blue">Poker Blue</MenuItem>
                  <MenuItem value="oled-black">OLED Black</MenuItem>
                </Select>
              </FormControl>

              {/* Font Size */}
              <Typography gutterBottom>Font Size: {settings.fontSize}%</Typography>
              <Slider
                value={settings.fontSize}
                onChange={(_, value) => updateSetting('fontSize', value as number)}
                min={80}
                max={120}
                step={5}
                marks
                sx={{ mb: 2 }}
              />

              {/* Compact Mode */}
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.compactMode}
                    onChange={(e) => updateSetting('compactMode', e.target.checked)}
                  />
                }
                label="Compact Mode"
                sx={{ mb: 2 }}
              />
            </Box>

            <Divider />

            {/* Advice Settings */}
            <ListItem>
              <ListItemIcon>
                <Psychology />
              </ListItemIcon>
              <ListItemText primary="Advice" />
            </ListItem>
            <Box px={2}>
              {/* Detail Level */}
              <Typography gutterBottom>Detail Level</Typography>
              <ToggleButtonGroup
                value={settings.adviceDetailLevel}
                exclusive
                onChange={(_, value) => value && updateSetting('adviceDetailLevel', value)}
                size="small"
                fullWidth
                sx={{ mb: 2 }}
              >
                <ToggleButton value="minimal">
                  <Tooltip title="Just the action">
                    <span>Min</span>
                  </Tooltip>
                </ToggleButton>
                <ToggleButton value="compact">
                  <Tooltip title="Action + confidence">
                    <span>Compact</span>
                  </Tooltip>
                </ToggleButton>
                <ToggleButton value="detailed">
                  <Tooltip title="All information">
                    <span>Detailed</span>
                  </Tooltip>
                </ToggleButton>
                <ToggleButton value="expert">
                  <Tooltip title="Maximum detail">
                    <span>Expert</span>
                  </Tooltip>
                </ToggleButton>
              </ToggleButtonGroup>

              {/* Update Frequency */}
              <Typography gutterBottom>
                Update Frequency: {settings.updateFrequency}/sec
              </Typography>
              <Slider
                value={settings.updateFrequency}
                onChange={(_, value) => updateSetting('updateFrequency', value as number)}
                min={1}
                max={5}
                step={1}
                marks
                sx={{ mb: 2 }}
              />

              {/* Show Options */}
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showConfidenceBreakdown}
                    onChange={(e) => updateSetting('showConfidenceBreakdown', e.target.checked)}
                  />
                }
                label="Show Confidence Breakdown"
                sx={{ display: 'block', mb: 1 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showAlternatives}
                    onChange={(e) => updateSetting('showAlternatives', e.target.checked)}
                  />
                }
                label="Show Alternatives"
                sx={{ display: 'block', mb: 2 }}
              />
            </Box>

            <Divider />

            {/* Alert Settings */}
            <ListItem>
              <ListItemIcon>
                <Notifications />
              </ListItemIcon>
              <ListItemText primary="Alerts" />
            </ListItem>
            <Box px={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.soundEnabled}
                    onChange={(e) => updateSetting('soundEnabled', e.target.checked)}
                  />
                }
                label="Sound Enabled"
                sx={{ display: 'block', mb: 1 }}
              />
              
              {settings.soundEnabled && (
                <>
                  <Typography gutterBottom>Volume: {settings.soundVolume}%</Typography>
                  <Slider
                    value={settings.soundVolume}
                    onChange={(_, value) => updateSetting('soundVolume', value as number)}
                    min={0}
                    max={100}
                    step={10}
                    sx={{ mb: 2 }}
                  />
                </>
              )}

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.decisionTimerAlert}
                    onChange={(e) => updateSetting('decisionTimerAlert', e.target.checked)}
                  />
                }
                label="Decision Timer Alerts"
                sx={{ display: 'block', mb: 2 }}
              />
            </Box>

            <Divider />

            {/* Auto-hide Settings */}
            <ListItem>
              <ListItemIcon>
                <Visibility />
              </ListItemIcon>
              <ListItemText primary="Auto-hide" />
            </ListItem>
            <Box px={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoHideInactive}
                    onChange={(e) => updateSetting('autoHideInactive', e.target.checked)}
                  />
                }
                label="Hide Inactive Sections"
                sx={{ display: 'block', mb: 1 }}
              />
              
              {settings.autoHideInactive && (
                <>
                  <Typography gutterBottom>
                    Hide After: {settings.autoHideDelay} seconds
                  </Typography>
                  <Slider
                    value={settings.autoHideDelay}
                    onChange={(_, value) => updateSetting('autoHideDelay', value as number)}
                    min={5}
                    max={30}
                    step={5}
                    marks
                    sx={{ mb: 2 }}
                  />
                </>
              )}
            </Box>

            <Divider />

            {/* Performance Settings */}
            <ListItem>
              <ListItemIcon>
                <Speed />
              </ListItemIcon>
              <ListItemText primary="Performance" />
            </ListItem>
            <Box px={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.useHardwareAcceleration}
                    onChange={(e) => updateSetting('useHardwareAcceleration', e.target.checked)}
                  />
                }
                label="Hardware Acceleration"
                sx={{ display: 'block', mb: 1 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.reducedMotion}
                    onChange={(e) => updateSetting('reducedMotion', e.target.checked)}
                  />
                }
                label="Reduced Motion"
                sx={{ display: 'block', mb: 2 }}
              />
            </Box>

            <Divider />

            {/* Language */}
            <ListItem>
              <ListItemIcon>
                <Language />
              </ListItemIcon>
              <ListItemText primary="Language" />
            </ListItem>
            <Box px={2} mb={2}>
              <FormControl fullWidth size="small">
                <Select
                  value={settings.language}
                  onChange={(e) => updateSetting('language', e.target.value)}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Español</MenuItem>
                  <MenuItem value="fr">Français</MenuItem>
                  <MenuItem value="de">Deutsch</MenuItem>
                  <MenuItem value="zh">中文</MenuItem>
                  <MenuItem value="ja">日本語</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </List>

          {/* Footer Actions */}
          <Box
            sx={{
              p: 2,
              borderTop: 1,
              borderColor: 'divider',
              display: 'flex',
              gap: 1,
            }}
          >
            <Button
              variant="outlined"
              size="small"
              startIcon={<RestoreOutlined />}
              onClick={resetToDefaults}
              fullWidth
            >
              Reset
            </Button>
            <Button
              variant="contained"
              size="small"
              startIcon={<Save />}
              onClick={saveSettings}
              disabled={!hasChanges}
              fullWidth
            >
              Apply
            </Button>
          </Box>
        </>
      )}

      {/* Collapsed View */}
      {collapsed && (
        <List sx={{ flex: 1 }}>
          <Tooltip title="Theme" placement={position === 'left' ? 'right' : 'left'}>
            <ListItem button onClick={() => setActiveSection('theme')}>
              <ListItemIcon>
                <Brightness6 />
              </ListItemIcon>
            </ListItem>
          </Tooltip>
          <Tooltip title="Advice" placement={position === 'left' ? 'right' : 'left'}>
            <ListItem button onClick={() => setActiveSection('advice')}>
              <ListItemIcon>
                <Psychology />
              </ListItemIcon>
            </ListItem>
          </Tooltip>
          <Tooltip title="Alerts" placement={position === 'left' ? 'right' : 'left'}>
            <ListItem button onClick={() => setActiveSection('alerts')}>
              <ListItemIcon>
                <Notifications />
              </ListItemIcon>
            </ListItem>
          </Tooltip>
          <Tooltip title="Performance" placement={position === 'left' ? 'right' : 'left'}>
            <ListItem button onClick={() => setActiveSection('performance')}>
              <ListItemIcon>
                <Speed />
              </ListItemIcon>
            </ListItem>
          </Tooltip>
        </List>
      )}
    </Drawer>
  );
};

// Floating settings button
export const FloatingSettingsButton: React.FC<{
  onClick: () => void;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}> = ({ onClick, position = 'bottom-right' }) => {
  const getPositionStyles = () => {
    const base = { position: 'fixed' as const, margin: '20px', zIndex: 1000 };
    switch (position) {
      case 'top-left':
        return { ...base, top: 0, left: 0 };
      case 'top-right':
        return { ...base, top: 0, right: 0 };
      case 'bottom-left':
        return { ...base, bottom: 0, left: 0 };
      case 'bottom-right':
        return { ...base, bottom: 0, right: 0 };
    }
  };

  return (
    <IconButton
      onClick={onClick}
      sx={{
        ...getPositionStyles(),
        backgroundColor: 'primary.main',
        color: 'primary.contrastText',
        '&:hover': {
          backgroundColor: 'primary.dark',
        },
      }}
    >
      <Settings />
    </IconButton>
  );
};

export default QuickSettingsPanel;
