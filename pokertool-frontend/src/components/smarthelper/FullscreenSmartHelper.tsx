/**
 * Fullscreen SmartHelper Mode
 *
 * Immersive fullscreen view for SmartHelper with:
 * - Full viewport coverage
 * - Escape key to exit
 * - Keyboard shortcuts
 * - Maximized content area
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  IconButton,
  Tooltip,
  Fade,
  Paper,
  Typography,
  Chip
} from '@mui/material';
import {
  Fullscreen,
  FullscreenExit,
  Close,
  KeyboardArrowLeft,
  KeyboardArrowRight
} from '@mui/icons-material';

interface FullscreenSmartHelperProps {
  children: React.ReactNode;
  isFullscreen: boolean;
  onFullscreenChange: (fullscreen: boolean) => void;
  title?: string;
  showControls?: boolean;
  keyboardShortcuts?: boolean;
}

export const FullscreenSmartHelper: React.FC<FullscreenSmartHelperProps> = ({
  children,
  isFullscreen,
  onFullscreenChange,
  title = 'SmartHelper',
  showControls = true,
  keyboardShortcuts = true
}) => {
  const [controlsVisible, setControlsVisible] = useState(true);
  const [mouseIdle, setMouseIdle] = useState(false);

  // Auto-hide controls after mouse idle
  useEffect(() => {
    if (!isFullscreen) return;

    let timeoutId: NodeJS.Timeout;

    const resetIdleTimer = () => {
      setMouseIdle(false);
      setControlsVisible(true);

      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        setMouseIdle(true);
        setControlsVisible(false);
      }, 3000); // Hide after 3 seconds of inactivity
    };

    const handleMouseMove = () => resetIdleTimer();
    const handleMouseEnter = () => resetIdleTimer();

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseenter', handleMouseEnter);

    resetIdleTimer();

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseenter', handleMouseEnter);
    };
  }, [isFullscreen]);

  // Keyboard shortcuts
  useEffect(() => {
    if (!keyboardShortcuts) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      // Escape to exit fullscreen
      if (e.key === 'Escape' && isFullscreen) {
        onFullscreenChange(false);
      }

      // F11 or Cmd/Ctrl+Shift+F to toggle fullscreen
      if (
        e.key === 'F11' ||
        ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'F')
      ) {
        e.preventDefault();
        onFullscreenChange(!isFullscreen);
      }

      // Show/hide controls with 'C' key
      if (e.key === 'c' || e.key === 'C') {
        setControlsVisible((prev) => !prev);
      }
    };

    document.addEventListener('keydown', handleKeyPress);

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [isFullscreen, keyboardShortcuts, onFullscreenChange]);

  // Browser fullscreen API
  const handleNativeFullscreen = useCallback(() => {
    const elem = document.documentElement;

    if (!document.fullscreenElement) {
      elem.requestFullscreen?.();
      onFullscreenChange(true);
    } else {
      document.exitFullscreen?.();
      onFullscreenChange(false);
    }
  }, [onFullscreenChange]);

  if (!isFullscreen) {
    return (
      <Box sx={{ position: 'relative' }}>
        {children}
        {showControls && (
          <Tooltip title="Enter Fullscreen (F11)">
            <IconButton
              onClick={() => onFullscreenChange(true)}
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                color: 'rgba(255, 255, 255, 0.7)',
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.5)'
                }
              }}
            >
              <Fullscreen />
            </IconButton>
          </Tooltip>
        )}
      </Box>
    );
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 9999,
        backgroundColor: '#1a1a1a',
        overflow: 'auto'
      }}
    >
      {/* Top Controls Bar */}
      <Fade in={controlsVisible} timeout={300}>
        <Paper
          elevation={4}
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2,
            py: 1,
            backgroundColor: 'rgba(33, 33, 33, 0.95)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          {/* Title */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" fontWeight="bold" color="white">
              {title}
            </Typography>
            <Chip
              label="Fullscreen"
              size="small"
              sx={{
                height: 20,
                fontSize: '10px',
                backgroundColor: 'primary.main',
                color: 'white'
              }}
            />
          </Box>

          {/* Controls */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Previous (Left Arrow)">
              <IconButton size="small" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                <KeyboardArrowLeft />
              </IconButton>
            </Tooltip>

            <Tooltip title="Next (Right Arrow)">
              <IconButton size="small" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                <KeyboardArrowRight />
              </IconButton>
            </Tooltip>

            <Tooltip title="Browser Fullscreen">
              <IconButton
                size="small"
                onClick={handleNativeFullscreen}
                sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
              >
                {document.fullscreenElement ? <FullscreenExit /> : <Fullscreen />}
              </IconButton>
            </Tooltip>

            <Tooltip title="Exit Fullscreen (Esc)">
              <IconButton
                size="small"
                onClick={() => onFullscreenChange(false)}
                sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
              >
                <Close />
              </IconButton>
            </Tooltip>
          </Box>
        </Paper>
      </Fade>

      {/* Main Content */}
      <Box
        sx={{
          pt: controlsVisible ? 8 : 2,
          pb: 2,
          px: 3,
          minHeight: '100vh',
          transition: 'padding-top 0.3s ease'
        }}
      >
        {children}
      </Box>

      {/* Keyboard Shortcuts Help */}
      <Fade in={controlsVisible} timeout={300}>
        <Paper
          elevation={2}
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            zIndex: 10000,
            p: 1.5,
            backgroundColor: 'rgba(33, 33, 33, 0.9)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            maxWidth: 250
          }}
        >
          <Typography variant="caption" fontWeight="bold" color="white" sx={{ display: 'block', mb: 0.5 }}>
            Keyboard Shortcuts
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
              <Box component="span" sx={{ fontWeight: 'bold', color: 'primary.main' }}>ESC</Box> Exit fullscreen
            </Typography>
            <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
              <Box component="span" sx={{ fontWeight: 'bold', color: 'primary.main' }}>F11</Box> Browser fullscreen
            </Typography>
            <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
              <Box component="span" sx={{ fontWeight: 'bold', color: 'primary.main' }}>C</Box> Toggle controls
            </Typography>
            <Typography variant="caption" color="textSecondary" sx={{ fontSize: '10px' }}>
              <Box component="span" sx={{ fontWeight: 'bold', color: 'primary.main' }}>←/→</Box> Navigate
            </Typography>
          </Box>
        </Paper>
      </Fade>

      {/* Mouse idle hint */}
      {mouseIdle && (
        <Fade in={mouseIdle} timeout={500}>
          <Box
            sx={{
              position: 'fixed',
              bottom: '50%',
              left: '50%',
              transform: 'translate(-50%, 50%)',
              zIndex: 9998,
              pointerEvents: 'none'
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255, 255, 255, 0.3)',
                fontSize: '12px',
                animation: 'pulse 2s ease-in-out infinite',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 0.3 },
                  '50%': { opacity: 0.6 }
                }
              }}
            >
              Move mouse to show controls
            </Typography>
          </Box>
        </Fade>
      )}
    </Box>
  );
};

/**
 * Hook to manage fullscreen state
 */
export const useFullscreen = () => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen((prev) => !prev);
  }, []);

  const enterFullscreen = useCallback(() => {
    setIsFullscreen(true);
  }, []);

  const exitFullscreen = useCallback(() => {
    setIsFullscreen(false);
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  }, []);

  return {
    isFullscreen,
    setIsFullscreen,
    toggleFullscreen,
    enterFullscreen,
    exitFullscreen
  };
};

/**
 * Fullscreen Button Component
 */
interface FullscreenButtonProps {
  onClick: () => void;
  isFullscreen: boolean;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export const FullscreenButton: React.FC<FullscreenButtonProps> = ({
  onClick,
  isFullscreen,
  position = 'top-right'
}) => {
  const positionStyles = {
    'top-left': { top: 8, left: 8 },
    'top-right': { top: 8, right: 8 },
    'bottom-left': { bottom: 8, left: 8 },
    'bottom-right': { bottom: 8, right: 8 }
  };

  return (
    <Tooltip title={isFullscreen ? 'Exit Fullscreen (Esc)' : 'Enter Fullscreen (F11)'}>
      <IconButton
        onClick={onClick}
        sx={{
          position: 'absolute',
          ...positionStyles[position],
          color: 'rgba(255, 255, 255, 0.7)',
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            color: 'white'
          },
          zIndex: 1000
        }}
      >
        {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
      </IconButton>
    </Tooltip>
  );
};
