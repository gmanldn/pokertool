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
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Add as AddIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
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
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          🚀 AI Development Automation Hub
          <Chip label="BETA" color="warning" size="small" />
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Autonomous AI agents working in parallel to complete TODO tasks, test, commit, and document changes.
        </Typography>
      </Box>

      {/* Alert for new feature */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <strong>New Feature:</strong> This is a revolutionary development automation system.
        AI agents will work independently on tasks from your TODO.md file. Always review changes before merging!
      </Alert>

      {/* Control Panel */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          {/* Add New Task Button */}
          <Grid item>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => alert('Task creator coming soon!')}
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
              >
                Stop All
              </Button>
            )}
          </Grid>

          <Grid item>
            <Tooltip title="Refresh TODO.md">
              <IconButton>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Grid>

          <Grid item>
            <Tooltip title="Settings">
              <IconButton>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>
      </Paper>

      {/* Agent Terminals Grid */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 2, overflow: 'hidden' }}>
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
    </Box>
  );
};

export default Improve;
