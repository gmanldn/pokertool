import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Button,
  Box,
  Typography,
} from '@mui/material';
import { Warning, Error as ErrorIcon, Info, HelpOutline } from '@mui/icons-material';
import styles from './ConfirmDialog.module.css';

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  severity?: 'warning' | 'error' | 'info' | 'question';
  onConfirm: () => void;
  onCancel: () => void;
  confirmButtonColor?: 'primary' | 'secondary' | 'error' | 'warning';
  loading?: boolean;
}

/**
 * Confirmation dialog for destructive or important actions
 * 
 * @example
 * ```tsx
 * const [open, setOpen] = useState(false);
 * 
 * <ConfirmDialog
 *   open={open}
 *   title="Delete Hand History"
 *   message="Are you sure you want to delete this hand? This action cannot be undone."
 *   severity="error"
 *   confirmText="Delete"
 *   cancelText="Cancel"
 *   confirmButtonColor="error"
 *   onConfirm={() => {
 *     deleteHand();
 *     setOpen(false);
 *   }}
 *   onCancel={() => setOpen(false)}
 * />
 * ```
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  severity = 'warning',
  onConfirm,
  onCancel,
  confirmButtonColor = 'primary',
  loading = false,
}) => {
  const getIcon = () => {
    switch (severity) {
      case 'error':
        return <ErrorIcon className={styles.iconError} />;
      case 'warning':
        return <Warning className={styles.iconWarning} />;
      case 'info':
        return <Info className={styles.iconInfo} />;
      case 'question':
        return <HelpOutline className={styles.iconQuestion} />;
      default:
        return null;
    }
  };

  const getIconColor = () => {
    switch (severity) {
      case 'error':
        return '#f44336';
      case 'warning':
        return '#ff9800';
      case 'info':
        return '#2196f3';
      case 'question':
        return '#9c27b0';
      default:
        return undefined;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onCancel}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      maxWidth="sm"
      fullWidth
      className={styles.dialog}
    >
      <DialogTitle id="confirm-dialog-title" className={styles.title}>
        <Box className={styles.titleContainer}>
          <Box
            className={styles.iconContainer}
            sx={{ color: getIconColor() }}
          >
            {getIcon()}
          </Box>
          <Typography variant="h6" component="span">
            {title}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <DialogContentText
          id="confirm-dialog-description"
          className={styles.message}
        >
          {message}
        </DialogContentText>
      </DialogContent>

      <DialogActions className={styles.actions}>
        <Button
          onClick={onCancel}
          variant="outlined"
          disabled={loading}
          className={styles.cancelButton}
        >
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color={confirmButtonColor}
          disabled={loading}
          autoFocus
          className={styles.confirmButton}
        >
          {loading ? 'Processing...' : confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
