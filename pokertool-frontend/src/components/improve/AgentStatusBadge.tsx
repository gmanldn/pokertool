/**Agent Status Badge - Live status indicators for AI agents*/
import React from 'react';
import { Chip, CircularProgress, Box } from '@mui/material';
import {
  CheckCircle as DoneIcon,
  Error as ErrorIcon,
  Pause as PauseIcon,
  PlayArrow as WorkingIcon,
  Assignment as LoadingTasksIcon,
  Commit as CommittingIcon,
  HourglassEmpty as IdleIcon
} from '@mui/icons-material';

export type AgentStatus =
  | 'idle'
  | 'loading_tasks'
  | 'planning'
  | 'working'
  | 'testing'
  | 'committing'
  | 'done'
  | 'error'
  | 'paused';

interface AgentStatusBadgeProps {
  status: AgentStatus;
  taskInfo?: string;
  error?: string;
}

const STATUS_CONFIG: Record<AgentStatus, {
  label: string;
  color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  icon: React.ReactNode;
  animated: boolean;
}> = {
  idle: {
    label: 'Idle',
    color: 'default',
    icon: <IdleIcon />,
    animated: false
  },
  loading_tasks: {
    label: 'Loading Tasks',
    color: 'info',
    icon: <LoadingTasksIcon />,
    animated: true
  },
  planning: {
    label: 'Planning',
    color: 'info',
    icon: <LoadingTasksIcon />,
    animated: true
  },
  working: {
    label: 'Working',
    color: 'primary',
    icon: <WorkingIcon />,
    animated: true
  },
  testing: {
    label: 'Testing',
    color: 'secondary',
    icon: <CircularProgress size={16} />,
    animated: true
  },
  committing: {
    label: 'Committing',
    color: 'secondary',
    icon: <CommittingIcon />,
    animated: true
  },
  done: {
    label: 'Done',
    color: 'success',
    icon: <DoneIcon />,
    animated: false
  },
  error: {
    label: 'Error',
    color: 'error',
    icon: <ErrorIcon />,
    animated: false
  },
  paused: {
    label: 'Paused',
    color: 'warning',
    icon: <PauseIcon />,
    animated: false
  }
};

export const AgentStatusBadge: React.FC<AgentStatusBadgeProps> = ({
  status,
  taskInfo,
  error
}) => {
  const config = STATUS_CONFIG[status];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      <Chip
        icon={config.icon as any}
        label={config.label}
        color={config.color}
        size="small"
        sx={{
          animation: config.animated ? 'pulse 2s ease-in-out infinite' : 'none',
          '@keyframes pulse': {
            '0%, 100%': { opacity: 1 },
            '50%': { opacity: 0.7 }
          }
        }}
      />
      {taskInfo && (
        <Box sx={{ fontSize: '0.75rem', color: 'text.secondary', pl: 1 }}>
          {taskInfo}
        </Box>
      )}
      {error && (
        <Box sx={{ fontSize: '0.75rem', color: 'error.main', pl: 1 }}>
          {error}
        </Box>
      )}
    </Box>
  );
};
