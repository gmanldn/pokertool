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
  Radio,
  RadioGroup,
  FormControlLabel,
  FormLabel,
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
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'loading' | 'working' | 'committing' | 'done' | 'error';
  currentTask: string;
  tasksCompleted: number;
  totalTasks: number;
}

type AIProvider = 'claude-code' | 'anthropic' | 'openrouter' | 'openai';
type TaskPriority = 'P0' | 'P1' | 'P2' | 'P3';
type TaskSize = 'S' | 'M' | 'L';

interface NewTask {
  description: string;
  priority: TaskPriority;
  size: TaskSize;
  file?: string;
}

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

  // Task creator state
  const [showTaskCreator, setShowTaskCreator] = useState(false);
  const [taskDescription, setTaskDescription] = useState('');
  const [taskPriority, setTaskPriority] = useState<TaskPriority>('P0');
  const [taskSize, setTaskSize] = useState<TaskSize>('M');
  const [taskFile, setTaskFile] = useState('');
  const [bulkTasksText, setBulkTasksText] = useState('');
  const [isBulkMode, setIsBulkMode] = useState(false);

  // SuperAdmin authentication state
  const [isSuperAdminEnabled, setIsSuperAdminEnabled] = useState(false);
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');

  // Terminal refs
  const terminal1Ref = useRef<HTMLDivElement>(null);
  const terminal2Ref = useRef<HTMLDivElement>(null);
  const terminal3Ref = useRef<HTMLDivElement>(null);

  // Terminal instances
  const terminalInstances = useRef<(Terminal | null)[]>([null, null, null]);
  const fitAddons = useRef<(FitAddon | null)[]>([null, null, null]);
  const websockets = useRef<(WebSocket | null)[]>([null, null, null]);

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

  // Initialize xterm terminals
  useEffect(() => {
    const terminalRefs = [terminal1Ref, terminal2Ref, terminal3Ref];

    terminalRefs.forEach((ref, index) => {
      if (ref.current && !terminalInstances.current[index]) {
        // Create terminal instance
        const terminal = new Terminal({
          cursorBlink: true,
          fontSize: 13,
          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
          theme: {
            background: '#1e1e1e',
            foreground: '#d4d4d4',
            cursor: '#aeafad',
            black: '#000000',
            red: '#cd3131',
            green: '#0dbc79',
            yellow: '#e5e510',
            blue: '#2472c8',
            magenta: '#bc3fbc',
            cyan: '#11a8cd',
            white: '#e5e5e5',
            brightBlack: '#666666',
            brightRed: '#f14c4c',
            brightGreen: '#23d18b',
            brightYellow: '#f5f543',
            brightBlue: '#3b8eea',
            brightMagenta: '#d670d6',
            brightCyan: '#29b8db',
            brightWhite: '#ffffff'
          },
          rows: 20,
          cols: 80,
        });

        // Create fit addon
        const fitAddon = new FitAddon();
        terminal.loadAddon(fitAddon);

        // Open terminal
        terminal.open(ref.current);
        fitAddon.fit();

        // Store instances
        terminalInstances.current[index] = terminal;
        fitAddons.current[index] = fitAddon;

        // Write welcome message
        const agentNames = ['Top 20 Agent', 'Bottom 20 Agent', 'Random 20 Agent'];
        terminal.writeln(`\x1b[32m╔══════════════════════════════════════════╗\x1b[0m`);
        terminal.writeln(`\x1b[32m║  PokerTool AI Development Automation    ║\x1b[0m`);
        terminal.writeln(`\x1b[32m╠══════════════════════════════════════════╣\x1b[0m`);
        terminal.writeln(`\x1b[32m║  Agent: ${agentNames[index].padEnd(31, ' ')}║\x1b[0m`);
        terminal.writeln(`\x1b[32m╚══════════════════════════════════════════╝\x1b[0m`);
        terminal.writeln('');
        terminal.writeln('\x1b[90m# Agent idle. Click "DoActions" to start...\x1b[0m');
        terminal.writeln('');
      }
    });

    // Handle window resize
    const handleResize = () => {
      fitAddons.current.forEach(addon => {
        if (addon) {
          try {
            addon.fit();
          } catch (e) {
            console.error('Error fitting terminal:', e);
          }
        }
      });
    };

    window.addEventListener('resize', handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('resize', handleResize);

      terminalInstances.current.forEach((terminal, index) => {
        if (terminal) {
          terminal.dispose();
          terminalInstances.current[index] = null;
        }
      });

      websockets.current.forEach((ws, index) => {
        if (ws) {
          ws.close();
          websockets.current[index] = null;
        }
      });
    };
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

  // Task creator handlers
  const handleOpenTaskCreator = () => {
    setShowTaskCreator(true);
  };

  const handleCloseTaskCreator = () => {
    setShowTaskCreator(false);
    setTaskDescription('');
    setTaskPriority('P0');
    setTaskSize('M');
    setTaskFile('');
    setBulkTasksText('');
    setIsBulkMode(false);
  };

  const handleSaveTask = async () => {
    if (isBulkMode) {
      // Parse bulk tasks
      const tasks = bulkTasksText.split('\n').filter(line => line.trim());
      if (tasks.length === 0) {
        alert('Please enter at least one task');
        return;
      }

      // Send bulk tasks to backend
      try {
        const response = await fetch('/api/improve/add-tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tasks: tasks.map(t => ({ description: t, priority: taskPriority, size: taskSize, file: taskFile })) })
        });

        if (response.ok) {
          alert(`Successfully added ${tasks.length} tasks to TODO.md`);
          handleCloseTaskCreator();
        } else {
          alert('Failed to add tasks. Check console for details.');
        }
      } catch (error) {
        console.error('Error adding bulk tasks:', error);
        alert('Error adding tasks: ' + error);
      }
    } else {
      // Single task mode
      if (!taskDescription.trim()) {
        alert('Please enter a task description');
        return;
      }

      // Send single task to backend
      try {
        const response = await fetch('/api/improve/add-tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tasks: [{ description: taskDescription, priority: taskPriority, size: taskSize, file: taskFile }] })
        });

        if (response.ok) {
          alert('Task added successfully to TODO.md');
          handleCloseTaskCreator();
        } else {
          alert('Failed to add task. Check console for details.');
        }
      } catch (error) {
        console.error('Error adding task:', error);
        alert('Error adding task: ' + error);
      }
    }
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
              onClick={handleOpenTaskCreator}
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
                overflow: 'hidden',
                position: 'relative',
                '& .xterm': {
                  height: '100%',
                  padding: '8px'
                },
                '& .xterm-viewport': {
                  overflow: 'auto !important'
                }
              }}
            />
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

      {/* Task Creator Dialog */}
      <Dialog open={showTaskCreator} onClose={handleCloseTaskCreator} maxWidth="md" fullWidth>
        <DialogTitle>
          Add New Task(s) to TODO.md
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {/* Mode selector */}
            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel component="legend">Task Mode</FormLabel>
              <RadioGroup
                row
                value={isBulkMode ? 'bulk' : 'single'}
                onChange={(e) => setIsBulkMode(e.target.value === 'bulk')}
              >
                <FormControlLabel value="single" control={<Radio />} label="Single Task" />
                <FormControlLabel value="bulk" control={<Radio />} label="Bulk Tasks" />
              </RadioGroup>
            </FormControl>

            {isBulkMode ? (
              /* Bulk mode */
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Enter one task per line. Priority and size will be applied to all tasks.
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  label="Tasks (one per line)"
                  value={bulkTasksText}
                  onChange={(e) => setBulkTasksText(e.target.value)}
                  placeholder="Create user authentication system&#10;Add password reset functionality&#10;Implement 2FA support"
                  sx={{ mb: 2 }}
                />
              </Box>
            ) : (
              /* Single mode */
              <TextField
                fullWidth
                label="Task Description"
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="e.g., Create user authentication system"
                sx={{ mb: 2 }}
              />
            )}

            <Grid container spacing={2} sx={{ mb: 2 }}>
              {/* Priority selector */}
              <Grid item xs={4}>
                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={taskPriority}
                    label="Priority"
                    onChange={(e) => setTaskPriority(e.target.value as TaskPriority)}
                  >
                    <MenuItem value="P0">P0 - Critical</MenuItem>
                    <MenuItem value="P1">P1 - High</MenuItem>
                    <MenuItem value="P2">P2 - Medium</MenuItem>
                    <MenuItem value="P3">P3 - Low</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Size selector */}
              <Grid item xs={4}>
                <FormControl fullWidth>
                  <InputLabel>Size</InputLabel>
                  <Select
                    value={taskSize}
                    label="Size"
                    onChange={(e) => setTaskSize(e.target.value as TaskSize)}
                  >
                    <MenuItem value="S">S - Small (1-2 hrs)</MenuItem>
                    <MenuItem value="M">M - Medium (2-8 hrs)</MenuItem>
                    <MenuItem value="L">L - Large (1-3 days)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* File/component path */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="File/Component Path (optional)"
                  value={taskFile}
                  onChange={(e) => setTaskFile(e.target.value)}
                  placeholder="e.g., src/components/auth/Login.tsx"
                  helperText="Specify the file or component this task relates to"
                />
              </Grid>
            </Grid>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Format:</strong> Tasks will be added to TODO.md with the format:<br />
                <code>- [ ] [P{taskPriority}][{taskSize}] {'{'}description{'}'} — {'{'}file{'}'}</code>
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseTaskCreator} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleSaveTask} variant="contained" color="primary">
            {isBulkMode ? 'Add Tasks' : 'Add Task'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Improve;
