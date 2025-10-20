import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Dashboard as DashboardIcon,
  Casino as CasinoIcon,
  BarChart as StatsIcon,
  AccountBalance as BankrollIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useAppSelector, RootState } from '../store';
import { SettingsState } from '../store/slices/settingsSlice';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
  { path: '/tables', label: 'Tables', icon: <CasinoIcon /> },
  { path: '/statistics', label: 'Stats', icon: <StatsIcon /> },
  { path: '/bankroll', label: 'Bankroll', icon: <BankrollIcon /> },
  { path: '/settings', label: 'Settings', icon: <SettingsIcon /> },
];

export const MobileBottomNav: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mobileLayout, bottomNavigation } = useAppSelector((state: RootState) => state.settings) as SettingsState;

  // Only show on mobile layout if enabled in settings
  if (!mobileLayout || !bottomNavigation) {
    return null;
  }

  const handleNavClick = (path: string) => {
    navigate(path);
  };

  return (
    <nav className="bottom-nav">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        
        return (
          <div
            key={item.path}
            className={`bottom-nav-item ${isActive ? 'active' : ''}`}
            onClick={() => handleNavClick(item.path)}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                handleNavClick(item.path);
              }
            }}
            aria-label={item.label}
            aria-current={isActive ? 'page' : undefined}
          >
            {item.icon}
            <span>{item.label}</span>
          </div>
        );
      })}
    </nav>
  );
};
