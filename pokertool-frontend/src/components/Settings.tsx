/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/Settings.tsx
version: v79.0.0
last_commit: '2025-10-22T12:15:00+01:00'
fixes:
- date: '2025-10-22'
  summary: Added financial history reset workflow with confirmation dialog
---
POKERTOOL-HEADER-END */

import React, { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import SavingsIcon from '@mui/icons-material/Savings';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { useAppDispatch, useAppSelector } from '../store';
import {
  resetBankroll,
  setCurrency,
  updateLimits,
} from '../store/slices/bankrollSlice';
import { resetTournaments } from '../store/slices/tournamentSlice';
import { clearSession } from '../store/slices/sessionSlice';

export const Settings: React.FC = () => {
  const dispatch = useAppDispatch();
  const bankroll = useAppSelector((state) => state.bankroll);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [resetComplete, setResetComplete] = useState(false);

  const hasCustomLimits = useMemo(
    () => Object.values(bankroll.limits).some((value) => value !== null),
    [bankroll.limits]
  );

  const handleResetClick = () => {
    setConfirmOpen(true);
  };

  const handleCloseDialog = () => {
    if (isResetting) {
      return;
    }
    setConfirmOpen(false);
  };

  const handleConfirmReset = () => {
    setIsResetting(true);

    const { currency, limits } = bankroll;

    dispatch(resetBankroll());
    dispatch(resetTournaments());
    dispatch(clearSession());

    if (currency && currency !== 'USD') {
      dispatch(setCurrency(currency));
    }

    if (hasCustomLimits) {
      dispatch(updateLimits(limits));
    }

    setIsResetting(false);
    setConfirmOpen(false);
    setResetComplete(true);
  };

  return (
    <Box sx={{ p: 3, maxWidth: 960, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Stack spacing={3}>
        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SavingsIcon color="primary" />
              <Typography variant="h6">
                Financial History Reset
              </Typography>
            </Box>
            <Typography color="text.secondary">
              Start fresh by clearing bankroll transactions, tournament results,
              and in-session profit tracking. Learning datasets—such as opponent
              models and active learning feedback—stay intact so the system keeps
              everything it has learned about your play.
            </Typography>
            <Divider />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Button
                variant="contained"
                color="error"
                startIcon={<RestartAltIcon />}
                onClick={handleResetClick}
                sx={{ alignSelf: { xs: 'stretch', sm: 'flex-start' } }}
              >
                Reset Money History
              </Button>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PsychologyIcon color="action" />
                <Typography variant="body2" color="text.secondary">
                  Learning insights remain untouched.
                </Typography>
              </Box>
            </Stack>
            {resetComplete && (
              <Alert
                severity="success"
                onClose={() => setResetComplete(false)}
                sx={{ mt: 1 }}
              >
                Financial history cleared. Your learning data is still available.
              </Alert>
            )}
          </Stack>
        </Paper>
      </Stack>

      <Dialog
        open={confirmOpen}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reset money history?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will remove all bankroll transactions, tournament records, and
            session profit metrics so you can begin tracking from zero. Learning
            information, calibration data, and coaching preferences will be kept.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={isResetting}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirmReset}
            color="error"
            variant="contained"
            disabled={isResetting}
          >
            {isResetting ? 'Resetting…' : 'Confirm Reset'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
