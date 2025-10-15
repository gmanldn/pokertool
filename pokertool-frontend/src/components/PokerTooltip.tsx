/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/PokerTooltip.tsx
version: v76.0.0
last_commit: '2025-10-15T04:10:00Z'
fixes:
- date: '2025-10-15'
  summary: Created PokerTooltip component for contextual term explanations
---
POKERTOOL-HEADER-END */

import React, { ReactElement } from 'react';
import {
  Tooltip,
  TooltipProps,
  Box,
  Typography,
  Link,
  Divider,
} from '@mui/material';
import {
  Help as HelpIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { getTooltipContent, TooltipContent } from '../hooks/useTooltip';
import tooltipContent from '../data/tooltipContent.json';

interface PokerTooltipProps {
  term: keyof typeof tooltipContent;
  children: ReactElement;
  placement?: TooltipProps['placement'];
  arrow?: boolean;
  maxWidth?: number;
  enterDelay?: number;
}

/**
 * Enhanced tooltip component for poker terminology
 * Wraps children with a rich, informative tooltip
 */
export const PokerTooltip: React.FC<PokerTooltipProps> = ({
  term,
  children,
  placement = 'top',
  arrow = true,
  maxWidth = 400,
  enterDelay = 500,
}) => {
  const content = getTooltipContent(term);

  if (!content) {
    return children;
  }

  const tooltipTitle = (
    <Box sx={{ maxWidth, p: 1 }}>
      {/* Header */}
      <Box sx={{ mb: 1 }}>
        <Typography
          variant="subtitle2"
          sx={{
            fontWeight: 'bold',
            fontSize: '0.95rem',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
          }}
        >
          <HelpIcon fontSize="small" />
          {content.term} - {content.title}
        </Typography>
      </Box>

      <Divider sx={{ mb: 1, borderColor: 'rgba(255,255,255,0.2)' }} />

      {/* Definition */}
      <Typography
        variant="body2"
        sx={{ mb: 1, fontSize: '0.85rem', lineHeight: 1.5 }}
      >
        {content.definition}
      </Typography>

      {/* Formula */}
      {content.formula && (
        <Box sx={{ mb: 1 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 'bold',
              fontSize: '0.75rem',
              color: '#90caf9',
            }}
          >
            Formula:
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontSize: '0.8rem',
              fontFamily: 'monospace',
              backgroundColor: 'rgba(0,0,0,0.3)',
              p: 0.5,
              borderRadius: 0.5,
              mt: 0.5,
            }}
          >
            {content.formula}
          </Typography>
        </Box>
      )}

      {/* Example */}
      {content.example && (
        <Box sx={{ mb: 1 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 'bold',
              fontSize: '0.75rem',
              color: '#90caf9',
            }}
          >
            Example:
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontSize: '0.8rem',
              fontStyle: 'italic',
              opacity: 0.9,
              mt: 0.5,
            }}
          >
            {content.example}
          </Typography>
        </Box>
      )}

      {/* Strategic Implication */}
      {content.strategicImplication && (
        <Box sx={{ mb: 1 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 'bold',
              fontSize: '0.75rem',
              color: '#81c784',
            }}
          >
            Strategy:
          </Typography>
          <Typography
            variant="body2"
            sx={{ fontSize: '0.8rem', opacity: 0.9, mt: 0.5 }}
          >
            {content.strategicImplication}
          </Typography>
        </Box>
      )}

      {/* Ideal Range */}
      {content.idealRange && (
        <Box sx={{ mb: 1 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 'bold',
              fontSize: '0.75rem',
              color: '#ffb74d',
            }}
          >
            Ideal Range:
          </Typography>
          <Typography
            variant="body2"
            sx={{ fontSize: '0.8rem', opacity: 0.9, mt: 0.5 }}
          >
            {content.idealRange}
          </Typography>
        </Box>
      )}

      {/* Learn More Link */}
      {content.learnMoreUrl && (
        <>
          <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.2)' }} />
          <Link
            href={content.learnMoreUrl}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              fontSize: '0.75rem',
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: '#90caf9',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            Learn more about {content.term}
            <OpenInNewIcon sx={{ fontSize: '0.875rem' }} />
          </Link>
        </>
      )}
    </Box>
  );

  return (
    <Tooltip
      title={tooltipTitle}
      placement={placement}
      arrow={arrow}
      enterDelay={enterDelay}
      enterNextDelay={enterDelay}
      leaveDelay={200}
      componentsProps={{
        tooltip: {
          sx: {
            backgroundColor: 'rgba(33, 33, 33, 0.98)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
            border: '1px solid rgba(255,255,255,0.1)',
            maxWidth: maxWidth,
          },
        },
        arrow: {
          sx: {
            color: 'rgba(33, 33, 33, 0.98)',
          },
        },
      }}
    >
      {children}
    </Tooltip>
  );
};

/**
 * Inline text with tooltip - for use within paragraphs
 */
interface PokerTermProps {
  term: keyof typeof tooltipContent;
  children?: React.ReactNode;
}

export const PokerTerm: React.FC<PokerTermProps> = ({ term, children }) => {
  const content = getTooltipContent(term);
  
  const displayText = children || content?.term || term;

  return (
    <PokerTooltip term={term}>
      <Typography
        component="span"
        sx={{
          textDecoration: 'underline dotted',
          textDecorationColor: 'rgba(144, 202, 249, 0.5)',
          cursor: 'help',
          '&:hover': {
            textDecorationColor: 'rgba(144, 202, 249, 1)',
          },
        }}
      >
        {displayText}
      </Typography>
    </PokerTooltip>
  );
};

export default PokerTooltip;
