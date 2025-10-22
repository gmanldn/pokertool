/**Priority & Effort Selectors*/
import React from 'react';
import { Select, MenuItem } from '@mui/material';

export const PrioritySelector: React.FC<{value: string, onChange: (v: string) => void}> = ({value, onChange}) => (
  <Select value={value} onChange={(e) => onChange(e.target.value as string)}>
    {['P0', 'P1', 'P2', 'P3'].map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}
  </Select>
);

export const EffortSelector: React.FC<{value: string, onChange: (v: string) => void}> = ({value, onChange}) => (
  <Select value={value} onChange={(e) => onChange(e.target.value as string)}>
    {['S', 'M', 'L'].map(e => <MenuItem key={e} value={e}>{e}</MenuItem>)}
  </Select>
);
