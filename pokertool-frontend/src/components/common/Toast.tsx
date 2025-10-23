import React, { createContext, useContext, useState, useCallback } from 'react';
import {
  Snackbar,
  Alert,
  AlertColor,
  Slide,
  SlideProps,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon, Warning, Info } from '@mui/icons-material';

interface ToastMessage {
  id: string;
  message: string;
  severity: AlertColor;
  duration?: number;
}

interface ToastContextType {
  showToast: (
    message: string,
    severity?: AlertColor,
    duration?: number
  ) => void;
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback(
    (message: string, severity: AlertColor = 'info', duration = 4000) => {
      const id = `toast-${Date.now()}-${Math.random()}`;
      const newToast: ToastMessage = { id, message, severity, duration };
      setToasts((prev) => [...prev, newToast]);
    },
    []
  );

  const showSuccess = useCallback(
    (message: string, duration = 4000) => {
      showToast(message, 'success', duration);
    },
    [showToast]
  );

  const showError = useCallback(
    (message: string, duration = 6000) => {
      showToast(message, 'error', duration);
    },
    [showToast]
  );

  const showWarning = useCallback(
    (message: string, duration = 5000) => {
      showToast(message, 'warning', duration);
    },
    [showToast]
  );

  const showInfo = useCallback(
    (message: string, duration = 4000) => {
      showToast(message, 'info', duration);
    },
    [showToast]
  );

  const handleClose = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const getIcon = (severity: AlertColor) => {
    switch (severity) {
      case 'success':
        return <CheckCircle fontSize="inherit" />;
      case 'error':
        return <ErrorIcon fontSize="inherit" />;
      case 'warning':
        return <Warning fontSize="inherit" />;
      case 'info':
        return <Info fontSize="inherit" />;
      default:
        return undefined;
    }
  };

  return (
    <ToastContext.Provider
      value={{ showToast, showSuccess, showError, showWarning, showInfo }}
    >
      {children}
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open={true}
          autoHideDuration={toast.duration}
          onClose={() => handleClose(toast.id)}
          TransitionComponent={SlideTransition}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{
            bottom: index * 70 + 24, // Stack toasts vertically
          }}
        >
          <Alert
            onClose={() => handleClose(toast.id)}
            severity={toast.severity}
            variant="filled"
            iconMapping={{
              success: getIcon('success'),
              error: getIcon('error'),
              warning: getIcon('warning'),
              info: getIcon('info'),
            }}
            sx={{
              minWidth: '300px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            }}
          >
            {toast.message}
          </Alert>
        </Snackbar>
      ))}
    </ToastContext.Provider>
  );
};

/**
 * Hook to use toast notifications
 * 
 * @example
 * ```tsx
 * const toast = useToast();
 * 
 * // Show different types of toasts
 * toast.showSuccess('Operation completed!');
 * toast.showError('Something went wrong');
 * toast.showWarning('Please be careful');
 * toast.showInfo('Here is some information');
 * 
 * // Custom toast with duration
 * toast.showToast('Custom message', 'success', 3000);
 * ```
 */
export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export default ToastProvider;
