import React, { useState } from 'react';
import { Select, MenuItem, FormControl, InputLabel } from '@mui/material';

/**
 * Log level control component
 */
export const LogLevelControl: React.FC = () => {
  const [level, setLevel] = useState('INFO');

  return (
    <FormControl fullWidth>
      <InputLabel>Log Level</InputLabel>
      <Select value={level} onChange={(e) => setLevel(e.target.value)}>
        <MenuItem value="DEBUG">DEBUG</MenuItem>
        <MenuItem value="INFO">INFO</MenuItem>
        <MenuItem value="WARNING">WARNING</MenuItem>
        <MenuItem value="ERROR">ERROR</MenuItem>
      </Select>
    </FormControl>
  );
};
