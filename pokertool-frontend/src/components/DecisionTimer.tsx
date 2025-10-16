import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Paper,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  AlertTitle,
} from '@mui/material';
import { Timer, VolumeUp, VolumeOff, AccessTime, Warning, Speed } from '@mui/icons-material';
import { keyframes } from '@mui/system';

// Define pulsing animation for urgency
const pulse = keyframes`
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
`;

// Define flashing animation for critical time
const flash = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
`;

interface DecisionTimerProps {
  totalTime?: number; // Total time in seconds
  timeLimit?: number; // Optional alias for total time
  timeBank?: number; // Optional time bank in seconds
  onTimeout?: () => void; // Callback when time expires
  isActive?: boolean; // Whether timer is active
  soundEnabled?: boolean; // Whether sound alerts are enabled
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  compact?: boolean; // Render compact variant
}

interface TimerState {
  timeRemaining: number;
  timeBankRemaining: number;
  isUsingTimeBank: boolean;
  hasPlayedWarning: boolean;
  hasPlayedCritical: boolean;
  hasPlayedTimeBank: boolean;
}

export const DecisionTimer: React.FC<DecisionTimerProps> = (props) => {
  if (props.compact) {
    return (
      <CompactDecisionTimer
        totalTime={props.totalTime}
        timeLimit={props.timeLimit}
        isActive={props.isActive}
      />
    );
  }

  return <FullDecisionTimer {...props} />;
};

const FullDecisionTimer: React.FC<DecisionTimerProps> = ({
  totalTime = 30,
  timeLimit,
  timeBank = 30,
  onTimeout,
  isActive = true,
  soundEnabled = true,
  position = 'top-right',
}: DecisionTimerProps) => {
  const effectiveTotalTime = timeLimit ?? totalTime;

  const [state, setState] = useState<TimerState>({
    timeRemaining: effectiveTotalTime,
    timeBankRemaining: timeBank,
    isUsingTimeBank: false,
    hasPlayedWarning: false,
    hasPlayedCritical: false,
    hasPlayedTimeBank: false,
  });

  const [isSoundEnabled, setIsSoundEnabled] = useState(soundEnabled);
  const audioContextRef = useRef<AudioContext | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize audio context
  useEffect(() => {
    if (typeof window !== 'undefined' && 'AudioContext' in window) {
      audioContextRef.current = new AudioContext();
    }
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Play sound effect
  const playSound = useCallback((frequency: number, duration: number, volume: number = 0.3) => {
    if (!isSoundEnabled || !audioContextRef.current) return;

    try {
      const oscillator = audioContextRef.current.createOscillator();
      const gainNode = audioContextRef.current.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContextRef.current.destination);

      oscillator.frequency.value = frequency;
      oscillator.type = 'sine';

      gainNode.gain.value = volume;
      gainNode.gain.exponentialRampToValueAtTime(
        0.01,
        audioContextRef.current.currentTime + duration
      );

      oscillator.start(audioContextRef.current.currentTime);
      oscillator.stop(audioContextRef.current.currentTime + duration);
    } catch (error) {
      console.error('Error playing sound:', error);
    }
  }, [isSoundEnabled]);

  // Reset timer
  const resetTimer = useCallback(() => {
    setState({
      timeRemaining: effectiveTotalTime,
      timeBankRemaining: timeBank,
      isUsingTimeBank: false,
      hasPlayedWarning: false,
      hasPlayedCritical: false,
      hasPlayedTimeBank: false,
    });
  }, [effectiveTotalTime, timeBank]);

  // Timer effect
  useEffect(() => {
    if (!isActive) {
      resetTimer();
      return;
    }

    intervalRef.current = setInterval(() => {
      setState((prevState) => {
        let newState = { ...prevState };

        if (!newState.isUsingTimeBank && newState.timeRemaining > 0) {
          // Using regular time
          newState.timeRemaining -= 1;

          // Sound alerts for regular time
          if (newState.timeRemaining === 10 && !newState.hasPlayedWarning) {
            playSound(440, 0.1); // A4 note, short beep
            newState.hasPlayedWarning = true;
          } else if (newState.timeRemaining === 5 && !newState.hasPlayedCritical) {
            playSound(880, 0.2); // A5 note, longer beep
            newState.hasPlayedCritical = true;
          } else if (newState.timeRemaining <= 3 && newState.timeRemaining > 0) {
            playSound(1000 + (3 - newState.timeRemaining) * 200, 0.15, 0.4); // Increasing pitch
          }

          // Switch to time bank
          if (newState.timeRemaining === 0 && newState.timeBankRemaining > 0) {
            newState.isUsingTimeBank = true;
            if (!newState.hasPlayedTimeBank) {
              playSound(660, 0.3, 0.5); // E5 note for time bank activation
              newState.hasPlayedTimeBank = true;
            }
          }
        } else if (newState.isUsingTimeBank && newState.timeBankRemaining > 0) {
          // Using time bank
          newState.timeBankRemaining -= 1;

          // Sound alerts for time bank
          if (newState.timeBankRemaining <= 5 && newState.timeBankRemaining > 0) {
            playSound(1500 + (5 - newState.timeBankRemaining) * 300, 0.2, 0.5); // High pitch warning
          }
        }

        // Check for timeout
        if (newState.timeRemaining === 0 && newState.timeBankRemaining === 0) {
          if (onTimeout) {
            onTimeout();
          }
          playSound(300, 0.5, 0.6); // Low pitch for timeout
        }

        return newState;
      });
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isActive, playSound, onTimeout, resetTimer]);

  // Get timer color based on remaining time
  const getTimerColor = () => {
    const currentTime = state.isUsingTimeBank ? state.timeBankRemaining : state.timeRemaining;
    const maxTime = state.isUsingTimeBank ? timeBank : effectiveTotalTime;
    const percentage = (currentTime / maxTime) * 100;

    if (state.isUsingTimeBank) return '#9C27B0'; // Purple for time bank
    if (percentage > 50) return '#4CAF50'; // Green
    if (percentage > 25) return '#FFC107'; // Yellow
    if (percentage > 10) return '#FF9800'; // Orange
    return '#F44336'; // Red
  };

  // Get urgency level for animations
  const getUrgencyLevel = () => {
    const currentTime = state.isUsingTimeBank ? state.timeBankRemaining : state.timeRemaining;
    if (currentTime <= 3) return 'critical';
    if (currentTime <= 5) return 'high';
    if (currentTime <= 10) return 'medium';
    return 'low';
  };

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}s`;
  };

  // Get position styles
  const getPositionStyles = () => {
    const base = { position: 'fixed' as const, zIndex: 1000, margin: '20px' };
    switch (position) {
      case 'top-left':
        return { ...base, top: 0, left: 0 };
      case 'top-right':
        return { ...base, top: 0, right: 0 };
      case 'bottom-left':
        return { ...base, bottom: 0, left: 0 };
      case 'bottom-right':
        return { ...base, bottom: 0, right: 0 };
      default:
        return { ...base, top: 0, right: 0 };
    }
  };

  const currentTime = state.isUsingTimeBank ? state.timeBankRemaining : state.timeRemaining;
  const maxTime = state.isUsingTimeBank ? timeBank : effectiveTotalTime;
  const progress = (currentTime / maxTime) * 100;
  const urgency = getUrgencyLevel();
  const color = getTimerColor();

  if (!isActive) {
    return null;
  }

  return (
    <Paper
      elevation={6}
      sx={{
        ...getPositionStyles(),
        padding: 2,
        minWidth: 200,
        backgroundColor: urgency === 'critical' ? 'rgba(244, 67, 54, 0.1)' : 'background.paper',
        border: urgency === 'critical' ? '2px solid #F44336' : 'none',
        animation:
          urgency === 'critical'
            ? `${flash} 0.5s infinite`
            : urgency === 'high'
            ? `${pulse} 1s infinite`
            : 'none',
      }}
    >
      {/* Header with sound toggle */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Box display="flex" alignItems="center" gap={0.5}>
          <Timer fontSize="small" />
          <Typography variant="caption" fontWeight="bold">
            Decision Timer
          </Typography>
        </Box>
        <IconButton
          size="small"
          onClick={() => setIsSoundEnabled(!isSoundEnabled)}
          color={isSoundEnabled ? 'primary' : 'default'}
        >
          {isSoundEnabled ? <VolumeUp fontSize="small" /> : <VolumeOff fontSize="small" />}
        </IconButton>
      </Box>

      {/* Main timer display */}
      <Box position="relative" display="inline-flex" width="100%">
        <Box width="100%" textAlign="center">
          <Typography
            variant="h3"
            fontWeight="bold"
            sx={{
              color,
              textShadow: urgency === 'critical' ? '0 0 10px rgba(244, 67, 54, 0.5)' : 'none',
            }}
          >
            {formatTime(currentTime)}
          </Typography>
        </Box>
      </Box>

      {/* Progress bar */}
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{
          height: 8,
          borderRadius: 4,
          mt: 1,
          mb: 1,
          backgroundColor: 'rgba(0, 0, 0, 0.1)',
          '& .MuiLinearProgress-bar': {
            backgroundColor: color,
            transition: 'background-color 0.3s',
          },
        }}
      />

      {/* Status chips */}
      <Box display="flex" gap={1} justifyContent="center" flexWrap="wrap">
        {state.isUsingTimeBank && (
          <Chip
            icon={<AccessTime />}
            label="Time Bank"
            size="small"
            color="secondary"
            variant="filled"
          />
        )}
        {urgency === 'critical' && (
          <Chip
            icon={<Warning />}
            label="Act Now!"
            size="small"
            color="error"
            variant="filled"
            sx={{ animation: `${pulse} 0.5s infinite` }}
          />
        )}
        {urgency === 'high' && (
          <Chip
            icon={<Speed />}
            label="Hurry!"
            size="small"
            color="warning"
            variant="filled"
          />
        )}
      </Box>

      {/* Time bank indicator */}
      {!state.isUsingTimeBank && timeBank > 0 && (
        <Box mt={1}>
          <Typography variant="caption" color="textSecondary">
            Time Bank: {formatTime(state.timeBankRemaining)}
          </Typography>
        </Box>
      )}

      {/* Urgency message */}
      {urgency === 'critical' && (
        <Alert severity="error" variant="filled" sx={{ mt: 1, py: 0.5 }}>
          <AlertTitle sx={{ fontSize: '0.75rem', mb: 0 }}>
            {state.isUsingTimeBank ? 'Time Bank Running Out!' : 'Time Almost Up!'}
          </AlertTitle>
        </Alert>
      )}
    </Paper>
  );
};

// Optional: Compact version for mobile or minimal UI
export const CompactDecisionTimer: React.FC<DecisionTimerProps> = ({
  totalTime = 30,
  timeLimit,
  isActive = true,
}) => {
  const effectiveTotalTime = timeLimit ?? totalTime;
  const [timeRemaining, setTimeRemaining] = useState(effectiveTotalTime);

  useEffect(() => {
    if (!isActive) {
      setTimeRemaining(effectiveTotalTime);
      return;
    }

    const interval = setInterval(() => {
      setTimeRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, effectiveTotalTime]);

  const progress = (timeRemaining / effectiveTotalTime) * 100;
  const color = progress > 50 ? '#4CAF50' : progress > 20 ? '#FFC107' : '#F44336';

  if (!isActive) return null;

  return (
    <Box display="flex" alignItems="center" gap={1}>
      <Timer fontSize="small" style={{ color }} />
      <Typography variant="body2" fontWeight="bold" style={{ color }}>
        {timeRemaining}s
      </Typography>
      <CircularProgress
        variant="determinate"
        value={progress}
        size={20}
        thickness={4}
        sx={{
          color,
          '& .MuiCircularProgress-circle': {
            strokeLinecap: 'round',
          },
        }}
      />
    </Box>
  );
};

export default DecisionTimer;
