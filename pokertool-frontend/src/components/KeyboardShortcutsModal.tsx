import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Paper,
  Chip,
  IconButton,
  TextField,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Close,
  Search,
  Settings,
  Keyboard,
  RestartAlt,
  FileDownload,
  FileUpload,
  Help,
} from '@mui/icons-material';
import {
  KeyboardShortcut,
  ShortcutCategory,
  KeyboardShortcutDisplay,
  useKeyboardShortcuts,
} from '../hooks/useKeyboardShortcuts';

interface KeyboardShortcutsModalProps {
  open: boolean;
  onClose: () => void;
}

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({
  open,
  onClose,
}) => {
  const {
    shortcuts,
    getShortcutsByCategory,
    toggleShortcut,
    resetToDefaults,
    exportShortcuts,
    importShortcuts,
    formatShortcut,
  } = useKeyboardShortcuts();

  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDisabled, setShowDisabled] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });
  const [editingShortcut, setEditingShortcut] = useState<KeyboardShortcut | null>(null);

  const categories = getShortcutsByCategory();

  // Filter shortcuts based on search query
  const filterShortcuts = (shortcuts: KeyboardShortcut[]) => {
    if (!searchQuery) return shortcuts;
    const query = searchQuery.toLowerCase();
    return shortcuts.filter(
      (s) =>
        s.description.toLowerCase().includes(query) ||
        formatShortcut(s).toLowerCase().includes(query)
    );
  };

  // Filter categories based on active tab
  const getActiveCategory = (): ShortcutCategory | null => {
    if (activeTab === 0) {
      // All shortcuts
      return {
        name: 'All',
        shortcuts: shortcuts.filter((s) => showDisabled || s.enabled !== false),
      };
    }
    const category = categories[activeTab - 1];
    if (!category) return null;
    return {
      ...category,
      shortcuts: category.shortcuts.filter((s) => showDisabled || s.enabled !== false),
    };
  };

  const activeCategory = getActiveCategory();
  const filteredShortcuts = activeCategory ? filterShortcuts(activeCategory.shortcuts) : [];

  // Handle export
  const handleExport = () => {
    const json = exportShortcuts();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pokertool-shortcuts.json';
    a.click();
    URL.revokeObjectURL(url);
    setSnackbar({ open: true, message: 'Shortcuts exported successfully' });
  };

  // Handle import
  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      if (importShortcuts(content)) {
        setSnackbar({ open: true, message: 'Shortcuts imported successfully' });
      } else {
        setSnackbar({ open: true, message: 'Failed to import shortcuts' });
      }
    };
    reader.readAsText(file);
  };

  // Handle reset
  const handleReset = () => {
    resetToDefaults();
    setSnackbar({ open: true, message: 'Shortcuts reset to defaults' });
  };

  // Category icons
  const getCategoryIcon = (name: string) => {
    switch (name) {
      case 'Actions':
        return '🎮';
      case 'Bet Sizing':
        return '💰';
      case 'Views':
        return '👁️';
      case 'Navigation':
        return '🧭';
      case 'Help':
        return '❓';
      default:
        return '📌';
    }
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            height: '80vh',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <Keyboard />
              <Typography variant="h6">Keyboard Shortcuts</Typography>
            </Box>
            <IconButton onClick={onClose} size="small">
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent sx={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Search and Controls */}
          <Box mb={2}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search shortcuts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Box display="flex" gap={1} justifyContent="flex-end">
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showDisabled}
                        onChange={(e) => setShowDisabled(e.target.checked)}
                        size="small"
                      />
                    }
                    label="Show disabled"
                  />
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<RestartAlt />}
                    onClick={handleReset}
                  >
                    Reset
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<FileDownload />}
                    onClick={handleExport}
                  >
                    Export
                  </Button>
                  <Button
                    component="label"
                    variant="outlined"
                    size="small"
                    startIcon={<FileUpload />}
                  >
                    Import
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleImport}
                      style={{ display: 'none' }}
                    />
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>

          {/* Tabs */}
          <Tabs
            value={activeTab}
            onChange={(_, value) => setActiveTab(value)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
          >
            <Tab label="All" />
            {categories.map((category) => (
              <Tab
                key={category.name}
                label={
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <span>{getCategoryIcon(category.name)}</span>
                    <span>{category.name}</span>
                  </Box>
                }
              />
            ))}
          </Tabs>

          {/* Shortcuts List */}
          <Box flex={1} overflow="auto">
            {filteredShortcuts.length === 0 ? (
              <Alert severity="info">
                No shortcuts found. {searchQuery && 'Try adjusting your search.'}
              </Alert>
            ) : (
              <List>
                {filteredShortcuts.map((shortcut, index) => (
                  <React.Fragment key={index}>
                    <ListItem
                      sx={{
                        opacity: shortcut.enabled === false ? 0.5 : 1,
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }}
                    >
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={2}>
                            <KeyboardShortcutDisplay shortcut={shortcut} />
                            <Typography variant="body1">
                              {shortcut.description}
                            </Typography>
                            {shortcut.enabled === false && (
                              <Chip label="Disabled" size="small" />
                            )}
                          </Box>
                        }
                        secondary={shortcut.category}
                      />
                      <ListItemSecondaryAction>
                        <Switch
                          edge="end"
                          checked={shortcut.enabled !== false}
                          onChange={() =>
                            toggleShortcut(shortcut.key, {
                              ctrl: shortcut.ctrl,
                              alt: shortcut.alt,
                              shift: shortcut.shift,
                              meta: shortcut.meta,
                            })
                          }
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                    {index < filteredShortcuts.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </Box>

          {/* Help Section */}
          <Paper sx={{ p: 2, mt: 2, backgroundColor: 'background.default' }}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Help fontSize="small" />
              <Typography variant="subtitle2">Tips</Typography>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Typography variant="caption" color="textSecondary">
                  • Press <kbd>?</kbd> anytime to show this help
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="caption" color="textSecondary">
                  • Shortcuts work in all views
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="caption" color="textSecondary">
                  • Disabled in input fields
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </DialogContent>

        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </>
  );
};

// Floating shortcut hint component
export const ShortcutHint: React.FC<{
  action: string;
  shortcut: KeyboardShortcut;
  visible?: boolean;
  position?: 'top' | 'bottom';
}> = ({ action, shortcut, visible = false, position = 'bottom' }) => {
  if (!visible) return null;

  const positionStyles = position === 'top' 
    ? { top: 20 } 
    : { bottom: 20 };

  return (
    <Paper
      elevation={4}
      sx={{
        position: 'fixed',
        left: '50%',
        transform: 'translateX(-50%)',
        ...positionStyles,
        padding: '8px 16px',
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        animation: 'fadeIn 0.3s',
        '@keyframes fadeIn': {
          from: { opacity: 0, transform: 'translateX(-50%) translateY(10px)' },
          to: { opacity: 1, transform: 'translateX(-50%) translateY(0)' },
        },
      }}
    >
      <Typography variant="body2">{action}:</Typography>
      <KeyboardShortcutDisplay shortcut={shortcut} compact />
    </Paper>
  );
};

// Shortcut overlay for onboarding
export const ShortcutOverlay: React.FC<{
  visible?: boolean;
  onDismiss?: () => void;
}> = ({ visible = false, onDismiss }) => {
  if (!visible) return null;

  const commonShortcuts = [
    { key: 'F', description: 'Fold' },
    { key: 'C', description: 'Call' },
    { key: 'R', description: 'Raise' },
    { key: '1-5', description: 'Bet Sizes' },
    { key: '?', description: 'Help' },
  ];

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onDismiss}
    >
      <Paper sx={{ p: 3, maxWidth: 400 }}>
        <Typography variant="h6" gutterBottom>
          Quick Keyboard Shortcuts
        </Typography>
        <List dense>
          {commonShortcuts.map((shortcut) => (
            <ListItem key={shortcut.key}>
              <ListItemText
                primary={
                  <Box display="flex" justifyContent="space-between">
                    <kbd style={{
                      padding: '2px 6px',
                      backgroundColor: '#f0f0f0',
                      border: '1px solid #ccc',
                      borderRadius: '3px',
                      fontFamily: 'monospace',
                    }}>
                      {shortcut.key}
                    </kbd>
                    <Typography>{shortcut.description}</Typography>
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
        <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
          Press anywhere to dismiss
        </Typography>
      </Paper>
    </Box>
  );
};

export default KeyboardShortcutsModal;
