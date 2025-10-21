import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Checkbox,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
} from '@mui/material';
import { buildApiUrl } from '../config/api';

interface TodoItem {
  checked: boolean;
  priority: string;
  effort: string;
  title: string;
  description: string;
}

interface TodoData {
  raw_content: string;
  items: TodoItem[];
  total_items: number;
  completed_items: number;
  error?: string;
}

export const TodoList: React.FC = () => {
  const [todoData, setTodoData] = useState<TodoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTodo = async () => {
      try {
        const response = await fetch(buildApiUrl('/api/todo'));
        const data = await response.json();

        if (data.error) {
          setError(data.error);
        } else {
          setTodoData(data);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load TODO list');
      } finally {
        setLoading(false);
      }
    };

    fetchTodo();
    const interval = setInterval(fetchTodo, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'P0': return 'error';
      case 'P1': return 'warning';
      case 'P2': return 'info';
      case 'P3': return 'default';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!todoData) {
    return null;
  }

  const completionPercent = todoData.total_items > 0
    ? Math.round((todoData.completed_items / todoData.total_items) * 100)
    : 0;

  return (
    <Box p={3}>
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Development TODO List
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Progress: {todoData.completed_items} / {todoData.total_items} tasks completed ({completionPercent}%)
        </Typography>
        <LinearProgress
          variant="determinate"
          value={completionPercent}
          sx={{ mt: 2, height: 8, borderRadius: 4 }}
        />
      </Paper>

      <List>
        {todoData.items.map((item, index) => (
          <Paper key={index} elevation={1} sx={{ mb: 1 }}>
            <ListItem disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={item.checked}
                    tabIndex={-1}
                    disableRipple
                    inputProps={{ 'aria-labelledby': `todo-item-${index}` }}
                    disabled
                  />
                </ListItemIcon>
                <ListItemText
                  id={`todo-item-${index}`}
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={item.priority}
                        size="small"
                        color={getPriorityColor(item.priority)}
                      />
                      <Chip
                        label={item.effort}
                        size="small"
                        variant="outlined"
                      />
                      <Typography
                        variant="body1"
                        sx={{
                          textDecoration: item.checked ? 'line-through' : 'none',
                          color: item.checked ? 'text.disabled' : 'text.primary'
                        }}
                      >
                        {item.title}
                      </Typography>
                    </Box>
                  }
                  secondary={item.description}
                />
              </ListItemButton>
            </ListItem>
          </Paper>
        ))}
      </List>
    </Box>
  );
};
