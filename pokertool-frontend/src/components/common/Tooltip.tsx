import React from 'react';
import { Tooltip as MuiTooltip, TooltipProps, Zoom } from '@mui/material';
import { styled } from '@mui/material/styles';

// Styled tooltip with enhanced appearance
const StyledTooltip = styled(({ className, ...props }: TooltipProps) => (
  <MuiTooltip {...props} classes={{ popper: className }} />
))(({ theme }) => ({
  '& .MuiTooltip-tooltip': {
    backgroundColor: theme.palette.mode === 'dark' ? '#2d2d2d' : '#424242',
    color: '#ffffff',
    fontSize: '0.75rem',
    fontWeight: 400,
    padding: '8px 12px',
    borderRadius: '6px',
    maxWidth: 300,
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
    lineHeight: 1.5,
  },
  '& .MuiTooltip-arrow': {
    color: theme.palette.mode === 'dark' ? '#2d2d2d' : '#424242',
  },
}));

interface CustomTooltipProps extends Omit<TooltipProps, 'title'> {
  title: string | React.ReactNode;
  children: React.ReactElement;
  placement?:
    | 'top'
    | 'top-start'
    | 'top-end'
    | 'bottom'
    | 'bottom-start'
    | 'bottom-end'
    | 'left'
    | 'left-start'
    | 'left-end'
    | 'right'
    | 'right-start'
    | 'right-end';
  delay?: number;
  disabled?: boolean;
}

/**
 * Enhanced tooltip component with consistent styling across the application
 * 
 * @example
 * ```tsx
 * <Tooltip title="This is a helpful tooltip">
 *   <Button>Hover me</Button>
 * </Tooltip>
 * ```
 */
export const Tooltip: React.FC<CustomTooltipProps> = ({
  title,
  children,
  placement = 'top',
  delay = 500,
  disabled = false,
  arrow = true,
  ...rest
}) => {
  if (disabled || !title) {
    return children;
  }

  return (
    <StyledTooltip
      title={title}
      placement={placement}
      arrow={arrow}
      enterDelay={delay}
      enterNextDelay={delay}
      TransitionComponent={Zoom}
      {...rest}
    >
      {children}
    </StyledTooltip>
  );
};

export default Tooltip;
