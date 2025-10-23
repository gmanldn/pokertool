/**Task Search & Filter*/
import React, { useState } from 'react';
import { TextField, Chip, Box } from '@mui/material';

export const TaskSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<string[]>([]);
  
  return (
    <Box>
      <TextField fullWidth placeholder="Search tasks..." value={query} onChange={(e) => setQuery(e.target.value)} />
      <Box>{filters.map(f => <Chip key={f} label={f} onDelete={() => setFilters(filters.filter(x => x !== f))} />)}</Box>
    </Box>
  );
};
