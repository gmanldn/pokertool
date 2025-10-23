import React from 'react';
import { Button } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

interface DoActionsButtonProps {
  onExecute: () => void;
  disabled?: boolean;
}

/**
 * Button to spawn AI agents and execute tasks
 */
export const DoActionsButton: React.FC<DoActionsButtonProps> = ({ onExecute, disabled }) => {
  return (
    <Button
      variant="contained"
      color="primary"
      startIcon={<PlayArrowIcon />}
      onClick={onExecute}
      disabled={disabled}
      size="large"
    >
      Do Actions
    </Button>
  );
};
