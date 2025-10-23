/**Key Management Modal - View, edit, and delete saved API keys*/
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Box,
  Typography,
  Alert,
  Chip,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as ShowIcon,
  VisibilityOff as HideIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { secureKeyStorage } from '../../utils/secureKeyStorage';
import { apiKeyValidator, ProviderType, ValidationResult } from '../../utils/apiKeyValidation';

interface KeyEntry {
  provider: string;
  masked: string;
  isEditing?: boolean;
  newValue?: string;
  validationResult?: ValidationResult;
  isValidating?: boolean;
}

export interface KeyManagementModalProps {
  open: boolean;
  onClose: () => void;
  onKeysChanged?: () => void;
}

export const KeyManagementModal: React.FC<KeyManagementModalProps> = ({
  open,
  onClose,
  onKeysChanged
}) => {
  const [keys, setKeys] = useState<KeyEntry[]>([]);
  const [showKey, setShowKey] = useState<{ [provider: string]: boolean }>({});
  const [addingNew, setAddingNew] = useState(false);
  const [newProvider, setNewProvider] = useState<ProviderType>('anthropic');
  const [newKey, setNewKey] = useState('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const providers: ProviderType[] = ['claude-code', 'anthropic', 'openrouter', 'openai'];

  useEffect(() => {
    if (open) {
      loadKeys();
    }
  }, [open]);

  const loadKeys = async () => {
    const storedProviders = secureKeyStorage.getStoredProviders();
    const loadedKeys: KeyEntry[] = [];

    for (const provider of storedProviders) {
      const key = await secureKeyStorage.getKey(provider);
      if (key) {
        loadedKeys.push({
          provider,
          masked: maskKey(key)
        });
      }
    }

    setKeys(loadedKeys);
  };

  const maskKey = (key: string): string => {
    if (key.length <= 8) {
      return '*'.repeat(key.length);
    }
    return key.substring(0, 4) + '*'.repeat(key.length - 8) + key.substring(key.length - 4);
  };

  const handleDelete = async (provider: string) => {
    if (window.confirm(`Delete API key for ${provider}?`)) {
      secureKeyStorage.removeKey(provider);
      setKeys(keys.filter(k => k.provider !== provider));
      if (onKeysChanged) {
        onKeysChanged();
      }
    }
  };

  const handleEdit = (provider: string) => {
    setKeys(keys.map(k =>
      k.provider === provider
        ? { ...k, isEditing: true, newValue: '' }
        : k
    ));
  };

  const handleSaveEdit = async (provider: string) => {
    const keyEntry = keys.find(k => k.provider === provider);
    if (!keyEntry || !keyEntry.newValue) return;

    // Validate first
    setKeys(keys.map(k =>
      k.provider === provider
        ? { ...k, isValidating: true }
        : k
    ));

    const result = await apiKeyValidator.validateKey(provider as ProviderType, keyEntry.newValue);

    if (result.valid) {
      await secureKeyStorage.setKey(provider, keyEntry.newValue);
      setKeys(keys.map(k =>
        k.provider === provider
          ? { ...k, isEditing: false, masked: maskKey(keyEntry.newValue!), isValidating: false }
          : k
      ));
      if (onKeysChanged) {
        onKeysChanged();
      }
    } else {
      setKeys(keys.map(k =>
        k.provider === provider
          ? { ...k, validationResult: result, isValidating: false }
          : k
      ));
    }
  };

  const handleCancelEdit = (provider: string) => {
    setKeys(keys.map(k =>
      k.provider === provider
        ? { ...k, isEditing: false, newValue: undefined, validationResult: undefined }
        : k
    ));
  };

  const handleToggleShow = async (provider: string) => {
    if (showKey[provider]) {
      setShowKey({ ...showKey, [provider]: false });
    } else {
      const key = await secureKeyStorage.getKey(provider);
      if (key) {
        setKeys(keys.map(k =>
          k.provider === provider
            ? { ...k, masked: key }
            : k
        ));
        setShowKey({ ...showKey, [provider]: true });

        // Hide again after 5 seconds
        setTimeout(() => {
          setShowKey(prev => ({ ...prev, [provider]: false }));
          loadKeys();
        }, 5000);
      }
    }
  };

  const handleAddNew = async () => {
    if (!newKey) return;

    setIsValidating(true);
    const result = await apiKeyValidator.validateKey(newProvider, newKey);
    setValidationResult(result);
    setIsValidating(false);

    if (result.valid) {
      await secureKeyStorage.setKey(newProvider, newKey);
      setAddingNew(false);
      setNewKey('');
      setNewProvider('anthropic');
      setValidationResult(null);
      loadKeys();
      if (onKeysChanged) {
        onKeysChanged();
      }
    }
  };

  const availableProviders = providers.filter(
    p => !keys.some(k => k.provider === p)
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Manage API Keys</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Alert severity="info" sx={{ mb: 2 }}>
          Keys are encrypted and stored locally. They are never sent to the backend.
        </Alert>

        <List>
          {keys.map((keyEntry) => (
            <React.Fragment key={keyEntry.provider}>
              <ListItem>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {keyEntry.provider}
                      </Typography>
                      <Chip label="Stored" size="small" color="success" />
                    </Box>
                  }
                  secondary={
                    keyEntry.isEditing ? (
                      <Box mt={1}>
                        <TextField
                          fullWidth
                          size="small"
                          type="password"
                          placeholder="Enter new API key"
                          value={keyEntry.newValue || ''}
                          onChange={(e) => setKeys(keys.map(k =>
                            k.provider === keyEntry.provider
                              ? { ...k, newValue: e.target.value, validationResult: undefined }
                              : k
                          ))}
                          disabled={keyEntry.isValidating}
                        />
                        {keyEntry.validationResult && !keyEntry.validationResult.valid && (
                          <Alert severity="error" sx={{ mt: 1 }}>
                            {keyEntry.validationResult.error}
                          </Alert>
                        )}
                        <Box mt={1} display="flex" gap={1}>
                          <Button
                            size="small"
                            variant="contained"
                            startIcon={keyEntry.isValidating ? <CircularProgress size={16} /> : <SaveIcon />}
                            onClick={() => handleSaveEdit(keyEntry.provider)}
                            disabled={!keyEntry.newValue || keyEntry.isValidating}
                          >
                            Save
                          </Button>
                          <Button
                            size="small"
                            onClick={() => handleCancelEdit(keyEntry.provider)}
                            disabled={keyEntry.isValidating}
                          >
                            Cancel
                          </Button>
                        </Box>
                      </Box>
                    ) : (
                      <Typography
                        variant="body2"
                        fontFamily="monospace"
                        sx={{ mt: 0.5 }}
                      >
                        {keyEntry.masked}
                      </Typography>
                    )
                  }
                />
                {!keyEntry.isEditing && (
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => handleToggleShow(keyEntry.provider)}
                      sx={{ mr: 1 }}
                    >
                      {showKey[keyEntry.provider] ? <HideIcon /> : <ShowIcon />}
                    </IconButton>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => handleEdit(keyEntry.provider)}
                      sx={{ mr: 1 }}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => handleDelete(keyEntry.provider)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                )}
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>

        {availableProviders.length > 0 && !addingNew && (
          <Button
            startIcon={<AddIcon />}
            onClick={() => setAddingNew(true)}
            fullWidth
            variant="outlined"
            sx={{ mt: 2 }}
          >
            Add New Provider
          </Button>
        )}

        {addingNew && (
          <Box mt={2} p={2} border="1px solid" borderColor="divider" borderRadius={1}>
            <Typography variant="subtitle2" gutterBottom>
              Add New API Key
            </Typography>
            <TextField
              select
              fullWidth
              size="small"
              label="Provider"
              value={newProvider}
              onChange={(e) => setNewProvider(e.target.value as ProviderType)}
              sx={{ mb: 2 }}
              SelectProps={{ native: true }}
            >
              {availableProviders.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </TextField>
            <TextField
              fullWidth
              size="small"
              type="password"
              label="API Key"
              value={newKey}
              onChange={(e) => {
                setNewKey(e.target.value);
                setValidationResult(null);
              }}
              disabled={isValidating}
              sx={{ mb: 1 }}
            />
            {validationResult && !validationResult.valid && (
              <Alert severity="error" sx={{ mb: 1 }}>
                {validationResult.error}
              </Alert>
            )}
            <Box display="flex" gap={1}>
              <Button
                variant="contained"
                startIcon={isValidating ? <CircularProgress size={16} /> : <AddIcon />}
                onClick={handleAddNew}
                disabled={!newKey || isValidating}
              >
                Add
              </Button>
              <Button
                onClick={() => {
                  setAddingNew(false);
                  setNewKey('');
                  setValidationResult(null);
                }}
                disabled={isValidating}
              >
                Cancel
              </Button>
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};
