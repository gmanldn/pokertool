/**Agent Controls - Stop, pause, and resume controls for AI agents*/
import React from 'react';
import { IconButton, Tooltip, Box, Button } from '@mui/material';
import {
  Stop as StopIcon,
  Pause as PauseIcon,
  PlayArrow as ResumeIcon,
  RestartAlt as RestartIcon
} from '@mui/icons-material';

export interface AgentControlsProps {
  agentId: string;
  isRunning: boolean;
  isPaused: boolean;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
  onRestart: () => void;
  disabled?: boolean;
}

export const AgentControls: React.FC<AgentControlsProps> = ({
  agentId,
  isRunning,
  isPaused,
  onStop,
  onPause,
  onResume,
  onRestart,
  disabled = false
}) => {
  return (
    <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
      {isRunning && !isPaused && (
        <>
          <Tooltip title="Pause Agent">
            <span>
              <IconButton
                size="small"
                onClick={onPause}
                disabled={disabled}
                color="warning"
              >
                <PauseIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Stop Agent">
            <span>
              <IconButton
                size="small"
                onClick={onStop}
                disabled={disabled}
                color="error"
              >
                <StopIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </>
      )}
      {isRunning && isPaused && (
        <>
          <Tooltip title="Resume Agent">
            <span>
              <IconButton
                size="small"
                onClick={onResume}
                disabled={disabled}
                color="primary"
              >
                <ResumeIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Stop Agent">
            <span>
              <IconButton
                size="small"
                onClick={onStop}
                disabled={disabled}
                color="error"
              >
                <StopIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </>
      )}
      {!isRunning && (
        <Tooltip title="Restart Agent">
          <span>
            <IconButton
              size="small"
              onClick={onRestart}
              disabled={disabled}
              color="primary"
            >
              <RestartIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      )}
    </Box>
  );
};

export interface EmergencyStopProps {
  onStopAll: () => void;
  disabled?: boolean;
}

export const EmergencyStop: React.FC<EmergencyStopProps> = ({
  onStopAll,
  disabled = false
}) => {
  return (
    <Button
      variant="contained"
      color="error"
      size="small"
      startIcon={<StopIcon />}
      onClick={onStopAll}
      disabled={disabled}
      sx={{
        fontWeight: 'bold',
        animation: disabled ? 'none' : 'glow 2s ease-in-out infinite',
        '@keyframes glow': {
          '0%, 100%': { boxShadow: '0 0 5px rgba(211, 47, 47, 0.5)' },
          '50%': { boxShadow: '0 0 20px rgba(211, 47, 47, 0.8)' }
        }
      }}
    >
      STOP ALL AGENTS
    </Button>
  );
};
