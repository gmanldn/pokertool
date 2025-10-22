/**
 * Mobile-Optimized SmartHelper Layout
 *
 * Responsive layout optimized for mobile devices with:
 * - Bottom sheet for recommendations
 * - Swipeable tabs for different views
 * - Compact visualizations
 * - Touch-friendly controls
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Drawer,
  IconButton,
  Chip,
  Fab,
  SwipeableDrawer,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  Psychology,
  TrendingUp,
  People,
  Settings,
  ExpandLess,
  ExpandMore,
  Close,
  AutoAwesome
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <Box
    role="tabpanel"
    hidden={value !== index}
    id={`mobile-tabpanel-${index}`}
    aria-labelledby={`mobile-tab-${index}`}
    sx={{ height: '100%', overflow: 'auto' }}
  >
    {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
  </Box>
);

interface MobileSmartHelperLayoutProps {
  // Content for each tab
  recommendationContent?: React.ReactNode;
  equityContent?: React.ReactNode;
  opponentContent?: React.ReactNode;
  settingsContent?: React.ReactNode;

  // Recommendation data for FAB badge
  hasActiveRecommendation?: boolean;
  recommendationConfidence?: number;

  // Callbacks
  onTabChange?: (tabIndex: number) => void;
}

export const MobileSmartHelperLayout: React.FC<MobileSmartHelperLayoutProps> = ({
  recommendationContent,
  equityContent,
  opponentContent,
  settingsContent,
  hasActiveRecommendation = false,
  recommendationConfidence = 0,
  onTabChange
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [drawerHeight, setDrawerHeight] = useState<'collapsed' | 'half' | 'full'>('collapsed');

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    if (onTabChange) {
      onTabChange(newValue);
    }
  };

  const toggleDrawer = (open: boolean) => {
    setDrawerOpen(open);
    if (open && drawerHeight === 'collapsed') {
      setDrawerHeight('half');
    } else if (!open) {
      setDrawerHeight('collapsed');
    }
  };

  const cycleDrawerHeight = () => {
    if (drawerHeight === 'collapsed') {
      setDrawerHeight('half');
      setDrawerOpen(true);
    } else if (drawerHeight === 'half') {
      setDrawerHeight('full');
    } else {
      setDrawerHeight('collapsed');
      setDrawerOpen(false);
    }
  };

  const getDrawerHeightValue = () => {
    switch (drawerHeight) {
      case 'collapsed':
        return 0;
      case 'half':
        return '50vh';
      case 'full':
        return '90vh';
      default:
        return 0;
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return '#4caf50';
    if (confidence >= 60) return '#2196f3';
    if (confidence >= 40) return '#ff9800';
    return '#f44336';
  };

  // Desktop layout - return standard layout
  if (!isMobile) {
    return (
      <Box sx={{ width: '100%' }}>
        <Tabs value={activeTab} onChange={handleTabChange} variant="fullWidth">
          <Tab label="Recommend" icon={<Psychology />} iconPosition="start" />
          <Tab label="Equity" icon={<TrendingUp />} iconPosition="start" />
          <Tab label="Opponents" icon={<People />} iconPosition="start" />
          <Tab label="Settings" icon={<Settings />} iconPosition="start" />
        </Tabs>
        <TabPanel value={activeTab} index={0}>{recommendationContent}</TabPanel>
        <TabPanel value={activeTab} index={1}>{equityContent}</TabPanel>
        <TabPanel value={activeTab} index={2}>{opponentContent}</TabPanel>
        <TabPanel value={activeTab} index={3}>{settingsContent}</TabPanel>
      </Box>
    );
  }

  // Mobile layout - bottom sheet with FAB
  return (
    <Box sx={{ position: 'relative', height: '100%' }}>
      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="open smarthelper"
        onClick={() => toggleDrawer(true)}
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          zIndex: theme.zIndex.fab,
          display: drawerHeight !== 'collapsed' ? 'none' : 'flex'
        }}
      >
        <AutoAwesome />
        {hasActiveRecommendation && recommendationConfidence > 0 && (
          <Chip
            label={`${recommendationConfidence}%`}
            size="small"
            sx={{
              position: 'absolute',
              top: -8,
              right: -8,
              height: 24,
              fontSize: '10px',
              fontWeight: 'bold',
              backgroundColor: getConfidenceColor(recommendationConfidence),
              color: 'white',
              boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
            }}
          />
        )}
      </Fab>

      {/* Swipeable Bottom Drawer */}
      <SwipeableDrawer
        anchor="bottom"
        open={drawerOpen}
        onClose={() => toggleDrawer(false)}
        onOpen={() => toggleDrawer(true)}
        disableSwipeToOpen={false}
        swipeAreaWidth={56}
        ModalProps={{
          keepMounted: true // Better mobile performance
        }}
        PaperProps={{
          sx: {
            height: getDrawerHeightValue(),
            borderTopLeftRadius: 16,
            borderTopRightRadius: 16,
            backgroundColor: 'rgba(33, 33, 33, 0.98)',
            backdropFilter: 'blur(10px)',
            transition: 'height 0.3s ease-in-out'
          }
        }}
      >
        <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Drawer Handle */}
          <Box
            onClick={cycleDrawerHeight}
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              py: 1,
              cursor: 'pointer',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <Box
              sx={{
                width: 40,
                height: 4,
                backgroundColor: 'rgba(255, 255, 255, 0.3)',
                borderRadius: 2,
                mb: 0.5
              }}
            />
            {drawerHeight === 'half' && <ExpandLess sx={{ position: 'absolute', right: 16, color: 'white' }} />}
            {drawerHeight === 'full' && <ExpandMore sx={{ position: 'absolute', right: 16, color: 'white' }} />}
          </Box>

          {/* Header */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              px: 2,
              py: 1,
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesome sx={{ color: 'primary.main', fontSize: 24 }} />
              <Typography variant="h6" fontWeight="bold" color="white">
                SmartHelper
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={() => {
                setDrawerHeight('collapsed');
                setDrawerOpen(false);
              }}
              sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
            >
              <Close />
            </IconButton>
          </Box>

          {/* Tabs */}
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              minHeight: 48,
              '& .MuiTab-root': {
                minHeight: 48,
                fontSize: '11px',
                padding: '6px 8px'
              }
            }}
          >
            <Tab
              label="Recommend"
              icon={<Psychology sx={{ fontSize: 18 }} />}
              iconPosition="top"
            />
            <Tab
              label="Equity"
              icon={<TrendingUp sx={{ fontSize: 18 }} />}
              iconPosition="top"
            />
            <Tab
              label="Opponents"
              icon={<People sx={{ fontSize: 18 }} />}
              iconPosition="top"
            />
            <Tab
              label="Settings"
              icon={<Settings sx={{ fontSize: 18 }} />}
              iconPosition="top"
            />
          </Tabs>

          {/* Tab Content */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            <TabPanel value={activeTab} index={0}>
              {recommendationContent || (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Psychology sx={{ fontSize: 48, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                  <Typography variant="body2" color="textSecondary">
                    No active recommendations
                  </Typography>
                </Box>
              )}
            </TabPanel>
            <TabPanel value={activeTab} index={1}>
              {equityContent || (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <TrendingUp sx={{ fontSize: 48, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                  <Typography variant="body2" color="textSecondary">
                    No equity data available
                  </Typography>
                </Box>
              )}
            </TabPanel>
            <TabPanel value={activeTab} index={2}>
              {opponentContent || (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <People sx={{ fontSize: 48, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                  <Typography variant="body2" color="textSecondary">
                    No opponent data available
                  </Typography>
                </Box>
              )}
            </TabPanel>
            <TabPanel value={activeTab} index={3}>
              {settingsContent || (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Settings sx={{ fontSize: 48, color: 'rgba(255, 255, 255, 0.3)', mb: 2 }} />
                  <Typography variant="body2" color="textSecondary">
                    Settings not configured
                  </Typography>
                </Box>
              )}
            </TabPanel>
          </Box>
        </Box>
      </SwipeableDrawer>
    </Box>
  );
};

/**
 * Compact Recommendation Card for Mobile
 */
interface CompactRecommendationProps {
  action: string;
  confidence: number;
  amount?: number;
  reasoning: string[];
}

export const CompactRecommendation: React.FC<CompactRecommendationProps> = ({
  action,
  confidence,
  amount,
  reasoning
}) => (
  <Paper
    elevation={2}
    sx={{
      p: 2,
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      borderRadius: 2,
      border: '1px solid rgba(255, 255, 255, 0.1)'
    }}
  >
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
      <Typography variant="h6" fontWeight="bold" color="white">
        {action}
      </Typography>
      <Chip
        label={`${confidence}%`}
        size="small"
        sx={{
          backgroundColor: confidence >= 70 ? '#4caf50' : '#ff9800',
          color: 'white',
          fontWeight: 'bold'
        }}
      />
    </Box>

    {amount && (
      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
        Amount: ${amount.toFixed(2)}
      </Typography>
    )}

    <Box sx={{ mt: 1 }}>
      {reasoning.slice(0, 3).map((reason, index) => (
        <Typography
          key={index}
          variant="caption"
          color="textSecondary"
          sx={{ display: 'block', mb: 0.5, fontSize: '11px' }}
        >
          • {reason}
        </Typography>
      ))}
    </Box>
  </Paper>
);
