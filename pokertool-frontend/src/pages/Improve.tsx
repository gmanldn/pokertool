import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Select,
  MenuItem,
  TextField,
  IconButton,
  Grid,
  Chip,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  Alert,
  Tooltip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Add as AddIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
} from '@mui/icons-material';

interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'loading' | 'working' | 'committing' | 'done' | 'error';
  currentTask: string;
  tasksCompleted: number;
  totalTasks: number;
}

type AIProvider = 'claude-code' | 'anthropic' | 'openrouter' | 'openai';

// SuperAdmin password hash - SHA-256 hash of the password
const SUPERADMIN_PASSWORD_HASH = 'afcf0cafd8f0161edc400dc94d14892a3da4862423863be5f6be6b530ca59416';

/**
 * Hash a string using SHA-256
 */
async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
}

const Improve: React.FC = () => {
  // State management
  const [provider, setProvider] = useState<AIProvider>('claude-code');
  const [apiKey, setApiKey] = useState('');
  const [agents, setAgents] = useState<AgentStatus[]>([
    { id: 'agent-1', name: 'Top 20 Agent', status: 'idle', currentTask: '', tasksCompleted: 0, totalTasks: 20 },
    { id: 'agent-2', name: 'Bottom 20 Agent', status: 'idle', currentTask: '', tasksCompleted: 0, totalTasks: 20 },
    { id: 'agent-3', name: 'Random 20 Agent', status: 'idle', currentTask: '', tasksCompleted: 0, totalTasks: 20 },
  ]);
  const [isRunning, setIsRunning] = useState(false);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);

  // SuperAdmin authentication state
  const [isSuperAdminEnabled, setIsSuperAdminEnabled] = useState(false);
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');

  // Terminal refs
  const terminal1Ref = useRef<HTMLDivElement>(null);
  const terminal2Ref = useRef<HTMLDivElement>(null);
  const terminal3Ref = useRef<HTMLDivElement>(null);

  // Load saved API key from localStorage
  useEffect(() => {
    const savedKey = localStorage.getItem(`ai_api_key_${provider}`);
    if (savedKey) {
      setApiKey(savedKey);
    }
  }, [provider]);

  // Check for SuperAdmin session on mount
  useEffect(() => {
    const superAdminSession = sessionStorage.getItem('superadmin_enabled');
    if (superAdminSession === 'true') {
      setIsSuperAdminEnabled(true);
    }
  }, []);

  // Provider change handler
  const handleProviderChange = (event: SelectChangeEvent<AIProvider>) => {
    const newProvider = event.target.value as AIProvider;
    setProvider(newProvider);

    // Check if we need API key for this provider
    const needsApiKey = newProvider !== 'claude-code';
    setShowApiKeyInput(needsApiKey);
  };

  // API key save handler
  const handleSaveApiKey = () => {
    if (apiKey) {
      localStorage.setItem(`ai_api_key_${provider}`, apiKey);
      alert('API key saved securely');
    }
  };

  // SuperAdmin authentication handler
  const handleSuperAdminAuth = async () => {
    if (!authPassword) {
      setAuthError('Please enter a password');
      return;
    }

    try {
      const hashedInput = await hashPassword(authPassword);

      if (hashedInput === SUPERADMIN_PASSWORD_HASH) {
        setIsSuperAdminEnabled(true);
        sessionStorage.setItem('superadmin_enabled', 'true');
        setShowAuthDialog(false);
        setAuthPassword('');
        setAuthError('');
      } else {
        setAuthError('Invalid password');
      }
    } catch (error) {
      setAuthError('Authentication error');
      console.error('SuperAdmin auth error:', error);
    }
  };

  // Handle SuperAdmin toggle
  const handleSuperAdminToggle = () => {
    if (isSuperAdminEnabled) {
      // Disable SuperAdmin mode
      setIsSuperAdminEnabled(false);
      sessionStorage.removeItem('superadmin_enabled');
    } else {
      // Show authentication dialog
      setShowAuthDialog(true);
      setAuthError('');
    }
  };

  // Handle dialog close
  const handleDialogClose = () => {
    setShowAuthDialog(false);
    setAuthPassword('');
    setAuthError('');
  };

  // Start agents
  const handleDoActions = async () => {
    if (provider !== 'claude-code' && !apiKey) {
      alert('Please enter an API key first');
      return;
    }

    setIsRunning(true);

    // Update all agents to loading status
    setAgents(agents.map(agent => ({
      ...agent,
      status: 'loading',
      currentTask: 'Loading tasks from TODO.md...'
    })));

    // TODO: Implement actual agent spawning
    // For now, simulate with a message
    console.log('Starting AI agents with provider:', provider);

    // Simulate agent activity after 2 seconds
    setTimeout(() => {
      setAgents(agents.map(agent => ({
        ...agent,
        status: 'working',
        currentTask: 'Analyzing task requirements...'
      })));
    }, 2000);
  };

  // Stop all agents
  const handleStopAll = () => {
    setIsRunning(false);
    setAgents(agents.map(agent => ({
      ...agent,
      status: 'idle',
      currentTask: ''
    })));
  };

  // Stop individual agent
  const handleStopAgent = (agentId: string) => {
    setAgents(agents.map(agent =>
      agent.id === agentId
        ? { ...agent, status: 'idle', currentTask: '' }
        : agent
    ));
  };

  // Get status color
  const getStatusColor = (status: AgentStatus['status']): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
    switch (status) {
      case 'idle': return 'default';
      case 'loading': return 'info';
      case 'working': return 'primary';
      case 'committing': return 'secondary';
      case 'done': return 'success';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3, height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            🚀 AI Development Automation Hub
            <Chip label="BETA" color="warning" size="small" />
            {isSuperAdminEnabled && (
              <Chip label="SUPERADMIN" color="error" size="small" />
            )}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Autonomous AI agents working in parallel to complete TODO tasks, test, commit, and document changes.
          </Typography>
        </Box>

        {/* SuperAdmin Toggle Button */}
        <Tooltip title={isSuperAdminEnabled ? "Disable SuperAdmin Mode" : "Enable SuperAdmin Mode"}>
          <Button
            variant={isSuperAdminEnabled ? "contained" : "outlined"}
            color={isSuperAdminEnabled ? "error" : "primary"}
            startIcon={isSuperAdminEnabled ? <LockOpenIcon /> : <LockIcon />}
            onClick={handleSuperAdminToggle}
            sx={{ minWidth: '160px' }}
          >
            SuperAdmin
          </Button>
        </Tooltip>
      </Box>

      {/* Alert for new feature */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <strong>New Feature:</strong> This is a revolutionary development automation system.
        AI agents will work independently on tasks from your TODO.md file. Always review changes before merging!
      </Alert>

      {/* Disabled overlay when SuperAdmin is not enabled */}
      {!isSuperAdminEnabled && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <strong>Feature Locked:</strong> This feature requires SuperAdmin authentication. Click the SuperAdmin button to enable.
        </Alert>
      )}

      {/* Control Panel */}
      <Paper sx={{ p: 2, mb: 2, opacity: isSuperAdminEnabled ? 1 : 0.5, pointerEvents: isSuperAdminEnabled ? 'auto' : 'none' }}>
        <Grid container spacing={2} alignItems="center">
          {/* Add New Task Button */}
          <Grid item>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => alert('Task creator coming soon!')}
              disabled={!isSuperAdminEnabled}
            >
              Add New Task(s)
            </Button>
          </Grid>

          {/* Provider Selector */}
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>AI Provider</InputLabel>
              <Select
                value={provider}
                label="AI Provider"
                onChange={handleProviderChange}
              >
                <MenuItem value="claude-code">Claude Code (Default)</MenuItem>
                <MenuItem value="anthropic">Anthropic API</MenuItem>
                <MenuItem value="openrouter">OpenRouter</MenuItem>
                <MenuItem value="openai">OpenAI</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* API Key Input (conditional) */}
          {showApiKeyInput && (
            <Grid item xs={12} sm={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  type="password"
                  label="API Key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                />
                <Button
                  variant="contained"
                  size="small"
                  onClick={handleSaveApiKey}
                  sx={{ minWidth: '80px' }}
                >
                  Save
                </Button>
              </Box>
            </Grid>
          )}

          {/* Spacer */}
          <Grid item xs />

          {/* Action Buttons */}
          <Grid item>
            {!isRunning ? (
              <Button
                variant="contained"
                color="primary"
                size="large"
                startIcon={<PlayIcon />}
                onClick={handleDoActions}
                sx={{ fontWeight: 'bold' }}
                disabled={!isSuperAdminEnabled}
              >
                DoActions
              </Button>
            ) : (
              <Button
                variant="contained"
                color="error"
                size="large"
                startIcon={<StopIcon />}
                onClick={handleStopAll}
                disabled={!isSuperAdminEnabled}
              >
                Stop All
              </Button>
            )}
          </Grid>

          <Grid item>
            <Tooltip title="Refresh TODO.md">
              <IconButton disabled={!isSuperAdminEnabled}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Grid>

          <Grid item>
            <Tooltip title="Settings">
              <IconButton disabled={!isSuperAdminEnabled}>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>
      </Paper>

      {/* Agent Terminals Grid */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 2, overflow: 'hidden', opacity: isSuperAdminEnabled ? 1 : 0.5 }}>
        {agents.map((agent, index) => (
          <Paper
            key={agent.id}
            sx={{
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              border: '2px solid',
              borderColor: agent.status === 'working' ? 'primary.main' : 'divider'
            }}
          >
            {/* Agent Header */}
            <Box
              sx={{
                p: 1,
                bgcolor: 'background.default',
                borderBottom: '1px solid',
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <Typography variant="subtitle2" fontWeight="bold">
                {agent.name}
              </Typography>

              <Chip
                label={agent.status.toUpperCase()}
                color={getStatusColor(agent.status)}
                size="small"
              />

              {agent.currentTask && (
                <Typography variant="caption" color="text.secondary" sx={{ flex: 1, ml: 1 }}>
                  {agent.currentTask}
                </Typography>
              )}

              <Typography variant="caption" color="text.secondary">
                {agent.tasksCompleted}/{agent.totalTasks} tasks
              </Typography>

              {agent.status !== 'idle' && (
                <IconButton
                  size="small"
                  onClick={() => handleStopAgent(agent.id)}
                  sx={{ ml: 'auto' }}
                >
                  <StopIcon fontSize="small" />
                </IconButton>
              )}
            </Box>

            {/* Terminal Window */}
            <Box
              ref={index === 0 ? terminal1Ref : index === 1 ? terminal2Ref : terminal3Ref}
              sx={{
                flexGrow: 1,
                bgcolor: '#1e1e1e',
                color: '#d4d4d4',
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                fontSize: '13px',
                p: 1,
                overflow: 'auto',
                position: 'relative'
              }}
            >
              {agent.status === 'idle' ? (
                <Typography sx={{ color: '#6a9955', fontStyle: 'italic' }}>
                  # Agent idle. Click "DoActions" to start...
                </Typography>
              ) : (
                <Box>
                  <Typography sx={{ color: '#4ec9b0' }}>
                    $ AI Agent {agent.id} initializing...
                  </Typography>
                  <Typography sx={{ color: '#9cdcfe' }}>
                    Provider: {provider}
                  </Typography>
                  <Typography sx={{ color: '#ce9178' }}>
                    Strategy: {agent.name}
                  </Typography>
                  <Typography sx={{ color: '#6a9955', mt: 1 }}>
                    # Terminal integration with xterm.js coming soon...
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
        ))}
      </Box>

      {/* Footer Info */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          💡 Tip: Agents will automatically commit changes, run tests, and update TODO.md.
          Use git to review and rollback if needed.
        </Typography>
      </Box>

      {/* SuperAdmin Authentication Dialog */}
      <Dialog open={showAuthDialog} onClose={handleDialogClose} maxWidth="xs" fullWidth>
        <DialogTitle>SuperAdmin Authentication</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This feature is restricted to SuperAdmin users only. Please enter the SuperAdmin password to continue.
          </Typography>
          <TextField
            autoFocus
            fullWidth
            type="password"
            label="Password"
            value={authPassword}
            onChange={(e) => setAuthPassword(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSuperAdminAuth();
              }
            }}
            error={!!authError}
            helperText={authError}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleSuperAdminAuth} variant="contained" color="primary">
            Authenticate
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Improve;
