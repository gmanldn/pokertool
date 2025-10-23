/**Task Editor Modal - Rich editor for adding tasks to TODO.md*/
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Typography,
  Chip,
  Alert,
  IconButton
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
  Save as SaveIcon
} from '@mui/icons-material';

export interface TaskData {
  title: string;
  description: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  effort: 'S' | 'M' | 'L';
  filePath?: string;
}

export interface TaskEditorModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (task: TaskData) => void;
  initialData?: Partial<TaskData>;
}

export const TaskEditorModal: React.FC<TaskEditorModalProps> = ({
  open,
  onClose,
  onSave,
  initialData
}) => {
  const [task, setTask] = useState<TaskData>({
    title: initialData?.title || '',
    description: initialData?.description || '',
    priority: initialData?.priority || 'P1',
    effort: initialData?.effort || 'M',
    filePath: initialData?.filePath || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: keyof TaskData, value: string) => {
    setTask(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!task.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (task.title.length < 10) {
      newErrors.title = 'Title must be at least 10 characters';
    }

    if (task.description && task.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validate()) {
      onSave(task);
      handleClose();
    }
  };

  const handleClose = () => {
    setTask({
      title: '',
      description: '',
      priority: 'P1',
      effort: 'M',
      filePath: ''
    });
    setErrors({});
    onClose();
  };

  const getPreview = (): string => {
    const desc = task.description ? ` — ${task.description}` : '';
    const file = task.filePath ? ` \`${task.filePath}\`` : '';
    return `- [ ] [${task.priority}][${task.effort}] ${task.title}${desc}${file}`;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Add New Task</Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box display="flex" flexDirection="column" gap={2}>
          {/* Title */}
          <TextField
            label="Task Title"
            fullWidth
            required
            value={task.title}
            onChange={(e) => handleChange('title', e.target.value)}
            error={Boolean(errors.title)}
            helperText={errors.title || 'Clear, concise task title (min 10 chars)'}
            placeholder="Add [feature] — Implement [description]"
          />

          {/* Description */}
          <TextField
            label="Description (Optional)"
            fullWidth
            multiline
            rows={3}
            value={task.description}
            onChange={(e) => handleChange('description', e.target.value)}
            error={Boolean(errors.description)}
            helperText={errors.description || 'Additional context or details'}
            placeholder="Detailed description of the task..."
          />

          {/* Priority and Effort */}
          <Box display="flex" gap={2}>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={task.priority}
                onChange={(e) => handleChange('priority', e.target.value)}
                label="Priority"
              >
                <MenuItem value="P0">
                  <Chip label="P0" color="error" size="small" sx={{ mr: 1 }} />
                  Critical
                </MenuItem>
                <MenuItem value="P1">
                  <Chip label="P1" color="warning" size="small" sx={{ mr: 1 }} />
                  High
                </MenuItem>
                <MenuItem value="P2">
                  <Chip label="P2" color="info" size="small" sx={{ mr: 1 }} />
                  Medium
                </MenuItem>
                <MenuItem value="P3">
                  <Chip label="P3" color="default" size="small" sx={{ mr: 1 }} />
                  Low
                </MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Effort</InputLabel>
              <Select
                value={task.effort}
                onChange={(e) => handleChange('effort', e.target.value)}
                label="Effort"
              >
                <MenuItem value="S">
                  <Chip label="S" size="small" sx={{ mr: 1 }} />
                  Small (&lt;1 hour)
                </MenuItem>
                <MenuItem value="M">
                  <Chip label="M" size="small" sx={{ mr: 1 }} />
                  Medium (1-4 hours)
                </MenuItem>
                <MenuItem value="L">
                  <Chip label="L" size="small" sx={{ mr: 1 }} />
                  Large (&gt;4 hours)
                </MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* File Path */}
          <TextField
            label="File Path (Optional)"
            fullWidth
            value={task.filePath}
            onChange={(e) => handleChange('filePath', e.target.value)}
            helperText="Primary file this task relates to"
            placeholder="src/pokertool/module.py"
          />

          {/* Preview */}
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Preview (TODO.md format)
            </Typography>
            <Alert severity="info" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
              {getPreview()}
            </Alert>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={<SaveIcon />}
          disabled={!task.title.trim()}
        >
          Add Task
        </Button>
      </DialogActions>
    </Dialog>
  );
};
