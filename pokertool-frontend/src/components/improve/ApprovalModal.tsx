/**Approval Workflow Modal - Manual approval before commits*/
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Warning as WarningIcon
} from '@mui/icons-material';

export interface FileChange {
  path: string;
  status: 'added' | 'modified' | 'deleted';
  additions: number;
  deletions: number;
  diff?: string;
}

export interface ApprovalRequest {
  taskTitle: string;
  taskDescription: string;
  agentId: string;
  commitMessage: string;
  filesChanged: FileChange[];
  testsStatus: 'passed' | 'failed' | 'skipped' | 'pending';
  warnings?: string[];
}

export interface ApprovalModalProps {
  open: boolean;
  request: ApprovalRequest | null;
  onApprove: () => void;
  onReject: (reason?: string) => void;
  onClose: () => void;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  open,
  request,
  onApprove,
  onReject,
  onClose
}) => {
  const [rejectionReason, setRejectionReason] = useState('');

  if (!request) return null;

  const totalAdditions = request.filesChanged.reduce((sum, f) => sum + f.additions, 0);
  const totalDeletions = request.filesChanged.reduce((sum, f) => sum + f.deletions, 0);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'success';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getFileStatusColor = (status: string) => {
    switch (status) {
      case 'added': return 'success';
      case 'modified': return 'info';
      case 'deleted': return 'error';
      default: return 'default';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { maxHeight: '90vh' } }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Approve Changes</Typography>
          <Chip
            label={request.agentId}
            color="primary"
            size="small"
          />
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {/* Task Info */}
        <Box mb={3}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Task
          </Typography>
          <Typography variant="body1" fontWeight="bold">
            {request.taskTitle}
          </Typography>
          {request.taskDescription && (
            <Typography variant="body2" color="text.secondary" mt={1}>
              {request.taskDescription}
            </Typography>
          )}
        </Box>

        {/* Commit Message */}
        <Box mb={3}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Commit Message
          </Typography>
          <Box
            sx={{
              p: 2,
              bgcolor: 'grey.100',
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem'
            }}
          >
            {request.commitMessage}
          </Box>
        </Box>

        {/* Tests Status */}
        <Box mb={3}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Tests
          </Typography>
          <Chip
            label={request.testsStatus.toUpperCase()}
            color={getStatusColor(request.testsStatus)}
            size="small"
          />
        </Box>

        {/* Warnings */}
        {request.warnings && request.warnings.length > 0 && (
          <Box mb={3}>
            <Alert severity="warning" icon={<WarningIcon />}>
              <Typography variant="subtitle2" gutterBottom>
                Warnings
              </Typography>
              {request.warnings.map((warning, idx) => (
                <Typography key={idx} variant="body2">
                  • {warning}
                </Typography>
              ))}
            </Alert>
          </Box>
        )}

        {/* File Changes */}
        <Box mb={2}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Changed Files ({request.filesChanged.length})
          </Typography>
          <Box display="flex" gap={2} mb={1}>
            <Chip
              label={`+${totalAdditions}`}
              size="small"
              color="success"
              variant="outlined"
            />
            <Chip
              label={`-${totalDeletions}`}
              size="small"
              color="error"
              variant="outlined"
            />
          </Box>

          {request.filesChanged.map((file, idx) => (
            <Accordion key={idx} sx={{ mt: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={1} flex={1}>
                  <Chip
                    label={file.status}
                    size="small"
                    color={getFileStatusColor(file.status) as any}
                  />
                  <Typography variant="body2" fontFamily="monospace">
                    {file.path}
                  </Typography>
                  <Box ml="auto" display="flex" gap={1}>
                    {file.additions > 0 && (
                      <Chip
                        label={`+${file.additions}`}
                        size="small"
                        color="success"
                        variant="outlined"
                      />
                    )}
                    {file.deletions > 0 && (
                      <Chip
                        label={`-${file.deletions}`}
                        size="small"
                        color="error"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box
                  sx={{
                    bgcolor: 'grey.100',
                    p: 2,
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    maxHeight: 300,
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {file.diff || 'No diff available'}
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button
          onClick={() => onReject(rejectionReason)}
          color="error"
          startIcon={<RejectIcon />}
        >
          Reject
        </Button>
        <Button
          onClick={onApprove}
          variant="contained"
          color="success"
          startIcon={<ApproveIcon />}
          autoFocus
        >
          Approve & Commit
        </Button>
      </DialogActions>
    </Dialog>
  );
};
