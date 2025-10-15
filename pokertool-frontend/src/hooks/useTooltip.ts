/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/hooks/useTooltip.ts
version: v76.0.0
last_commit: '2025-10-15T04:09:00Z'
fixes:
- date: '2025-10-15'
  summary: Created useTooltip hook for contextual poker term explanations
---
POKERTOOL-HEADER-END */

import { useState, useCallback, useMemo } from 'react';
import tooltipContent from '../data/tooltipContent.json';

export interface TooltipContent {
  term: string;
  title: string;
  definition: string;
  formula: string;
  example: string;
  strategicImplication: string;
  idealRange: string;
  learnMoreUrl: string;
}

export interface TooltipConfig {
  delayMs?: number;
  maxWidth?: number;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  arrow?: boolean;
}

const DEFAULT_CONFIG: Required<TooltipConfig> = {
  delayMs: 500,
  maxWidth: 400,
  placement: 'top',
  arrow: true,
};

/**
 * Hook for managing poker term tooltips
 * 
 * @param termKey - Key of the poker term in tooltipContent.json
 * @param config - Optional tooltip configuration
 * @returns Tooltip content and utilities
 */
export const useTooltip = (
  termKey: keyof typeof tooltipContent,
  config?: TooltipConfig
) => {
  const [isOpen, setIsOpen] = useState(false);
  const [openedAt, setOpenedAt] = useState<number | null>(null);

  // Merge config with defaults
  const finalConfig = useMemo(
    () => ({ ...DEFAULT_CONFIG, ...config }),
    [config]
  );

  // Get tooltip content
  const content = useMemo((): TooltipContent | null => {
    const data = tooltipContent[termKey];
    if (!data) {
      console.warn(`Tooltip content not found for term: ${termKey}`);
      return null;
    }
    return data as TooltipContent;
  }, [termKey]);

  // Open tooltip with delay
  const handleOpen = useCallback(() => {
    const timer = setTimeout(() => {
      setIsOpen(true);
      setOpenedAt(Date.now());
    }, finalConfig.delayMs);

    return () => clearTimeout(timer);
  }, [finalConfig.delayMs]);

  // Close tooltip
  const handleClose = useCallback(() => {
    setIsOpen(false);
    setOpenedAt(null);
  }, []);

  // Toggle tooltip
  const handleToggle = useCallback(() => {
    if (isOpen) {
      handleClose();
    } else {
      setIsOpen(true);
      setOpenedAt(Date.now());
    }
  }, [isOpen, handleClose]);

  // Format tooltip title with rich content
  const formattedTitle = useMemo(() => {
    if (!content) return '';
    return `${content.term} - ${content.title}`;
  }, [content]);

  // Format tooltip body with sections
  const formattedBody = useMemo(() => {
    if (!content) return null;

    return {
      definition: content.definition,
      formula: content.formula,
      example: content.example,
      strategicImplication: content.strategicImplication,
      idealRange: content.idealRange,
    };
  }, [content]);

  // Get duration tooltip has been open
  const openDuration = useMemo(() => {
    if (!openedAt) return 0;
    return Date.now() - openedAt;
  }, [openedAt, isOpen]);

  return {
    content,
    isOpen,
    config: finalConfig,
    formattedTitle,
    formattedBody,
    openDuration,
    handlers: {
      onOpen: handleOpen,
      onClose: handleClose,
      onToggle: handleToggle,
    },
  };
};

/**
 * Hook for managing multiple tooltips with keyboard shortcuts
 * 
 * @returns Global tooltip utilities
 */
export const useTooltipManager = () => {
  const [globalDelay, setGlobalDelay] = useState(DEFAULT_CONFIG.delayMs);
  const [showAllTooltips, setShowAllTooltips] = useState(true);
  const [helpOverlayOpen, setHelpOverlayOpen] = useState(false);

  // Get all available terms
  const availableTerms = useMemo(
    () => Object.keys(tooltipContent) as Array<keyof typeof tooltipContent>,
    []
  );

  // Toggle help overlay (keyboard shortcut: ?)
  const toggleHelpOverlay = useCallback(() => {
    setHelpOverlayOpen((prev) => !prev);
  }, []);

  // Update global delay
  const updateDelay = useCallback((delayMs: number) => {
    setGlobalDelay(Math.max(0, Math.min(delayMs, 2000)));
  }, []);

  // Toggle all tooltips
  const toggleAllTooltips = useCallback(() => {
    setShowAllTooltips((prev) => !prev);
  }, []);

  // Search for terms
  const searchTerms = useCallback((query: string): Array<keyof typeof tooltipContent> => {
    const lowerQuery = query.toLowerCase();
    return availableTerms.filter((key) => {
      const content = tooltipContent[key] as TooltipContent;
      return (
        content.term.toLowerCase().includes(lowerQuery) ||
        content.title.toLowerCase().includes(lowerQuery) ||
        content.definition.toLowerCase().includes(lowerQuery)
      );
    });
  }, [availableTerms]);

  // Get content for a term
  const getContent = useCallback(
    (termKey: keyof typeof tooltipContent): TooltipContent | null => {
      const data = tooltipContent[termKey];
      return data ? (data as TooltipContent) : null;
    },
    []
  );

  // Get all content
  const getAllContent = useCallback((): Record<string, TooltipContent> => {
    return tooltipContent as Record<string, TooltipContent>;
  }, []);

  return {
    globalDelay,
    showAllTooltips,
    helpOverlayOpen,
    availableTerms,
    actions: {
      updateDelay,
      toggleAllTooltips,
      toggleHelpOverlay,
      searchTerms,
      getContent,
      getAllContent,
    },
  };
};

/**
 * Get tooltip content for Material-UI Tooltip component
 * Returns formatted string for simple tooltips
 * 
 * @param termKey - Key of the poker term
 * @returns Formatted tooltip text
 */
export const getTooltipText = (
  termKey: keyof typeof tooltipContent
): string => {
  const content = tooltipContent[termKey] as TooltipContent | undefined;

  if (!content) {
    return '';
  }

  let text = `${content.term} - ${content.title}\n\n${content.definition}`;
  
  if (content.formula) {
    text += `\n\nFormula: ${content.formula}`;
  }
  
  if (content.example) {
    text += `\n\nExample: ${content.example}`;
  }
  
  if (content.strategicImplication) {
    text += `\n\nStrategy: ${content.strategicImplication}`;
  }
  
  if (content.idealRange) {
    text += `\n\nIdeal Range: ${content.idealRange}`;
  }

  return text;
};

/**
 * Get structured tooltip content for custom rendering
 * 
 * @param termKey - Key of the poker term
 * @returns Structured content object
 */
export const getTooltipContent = (
  termKey: keyof typeof tooltipContent
): TooltipContent | null => {
  const content = tooltipContent[termKey] as TooltipContent | undefined;
  return content || null;
};

export default useTooltip;
