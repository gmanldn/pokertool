/**
 * FPS Counter Component for HUD Overlay
 */
import React, { useEffect, useState } from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { Speed } from '@mui/icons-material';
import axios from 'axios';
import { buildApiUrl } from '../config/api';

interface FPSData {
  fps: number;
  avg_frame_time_ms: number;
}

export const FPSCounter: React.FC<{ compact?: boolean }> = React.memo(({ compact = false }) => {
  const [fpsData, setFpsData] = useState<FPSData>({ fps: 0, avg_frame_time_ms: 0 });

  useEffect(() => {
    const fetchFPS = async () => {
      try {
        const response = await axios.get<FPSData>(buildApiUrl('/api/detection/fps'));
        setFpsData(response.data);
      } catch (error) {
        console.error('Failed to fetch FPS:', error);
      }
    };

    const interval = setInterval(fetchFPS, 1000);
    fetchFPS();
    return () => clearInterval(interval);
  }, []);

  const getColor = () => {
    if (fpsData.fps >= 20) return 'success';
    if (fpsData.fps >= 10) return 'warning';
    return 'error';
  };

  const fpsDisplay = fpsData.fps.toFixed(1) + ' FPS';
  const avgDisplay = fpsData.avg_frame_time_ms.toFixed(1) + 'ms avg';

  if (compact) {
    return (
      <Chip
        icon={<Speed />}
        label={fpsDisplay}
        color={getColor()}
        size="small"
        sx={{ fontWeight: 'bold' }}
      />
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, padding: 1, backgroundColor: 'rgba(0, 0, 0, 0.7)', borderRadius: 1 }}>
      <Speed sx={{ color: 'primary.main' }} />
      <Box>
        <Typography variant="body2" fontWeight="bold" color="white">
          {fpsDisplay}
        </Typography>
        <Typography variant="caption" color="rgba(255, 255, 255, 0.7)">
          {avgDisplay}
        </Typography>
      </Box>
    </Box>
  );
});

FPSCounter.displayName = 'FPSCounter';
