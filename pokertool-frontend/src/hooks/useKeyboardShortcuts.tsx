import React, { useEffect, useCallback, useState, useRef } from 'react';
import { useDispatch } from 'react-redux';

// Types for keyboard shortcuts
export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
  description: string;
  category: string;
  action: () => void;
  enabled?: boolean;
}

export interface ShortcutCategory {
  name: string;
  icon?: string;
  shortcuts: KeyboardShortcut[];
}

// Default shortcuts configuration
export const defaultShortcuts: KeyboardShortcut[] = [
  // Action shortcuts
  {
    key: 'f',
    description: 'Fold',
    category: 'Actions',
    action: () => console.log('Fold action triggered'),
    enabled: true,
  },
  {
    key: 'c',
    description: 'Call',
    category: 'Actions',
    action: () => console.log('Call action triggered'),
    enabled: true,
  },
  {
    key: 'r',
    description: 'Raise',
    category: 'Actions',
    action: () => console.log('Raise action triggered'),
    enabled: true,
  },
  {
    key: 'a',
    description: 'All-in',
    category: 'Actions',
    action: () => console.log('All-in action triggered'),
    enabled: true,
  },
  
  // Bet sizing shortcuts
  {
    key: '1',
    description: '33% Pot',
    category: 'Bet Sizing',
    action: () => console.log('Bet 33% pot'),
    enabled: true,
  },
  {
    key: '2',
    description: '50% Pot',
    category: 'Bet Sizing',
    action: () => console.log('Bet 50% pot'),
    enabled: true,
  },
  {
    key: '3',
    description: '75% Pot',
    category: 'Bet Sizing',
    action: () => console.log('Bet 75% pot'),
    enabled: true,
  },
  {
    key: '4',
    description: 'Pot Size',
    category: 'Bet Sizing',
    action: () => console.log('Bet pot size'),
    enabled: true,
  },
  {
    key: '5',
    description: '2x Pot',
    category: 'Bet Sizing',
    action: () => console.log('Bet 2x pot'),
    enabled: true,
  },
  
  // View toggles
  {
    key: 'a',
    ctrl: true,
    description: 'Toggle Advice',
    category: 'Views',
    action: () => console.log('Toggle advice'),
    enabled: true,
  },
  {
    key: 's',
    ctrl: true,
    description: 'Toggle Statistics',
    category: 'Views',
    action: () => console.log('Toggle statistics'),
    enabled: true,
  },
  {
    key: 'h',
    ctrl: true,
    description: 'Toggle History',
    category: 'Views',
    action: () => console.log('Toggle history'),
    enabled: true,
  },
  {
    key: 'o',
    ctrl: true,
    description: 'Toggle Opponents',
    category: 'Views',
    action: () => console.log('Toggle opponents'),
    enabled: true,
  },
  {
    key: 't',
    ctrl: true,
    description: 'Toggle Timer',
    category: 'Views',
    action: () => console.log('Toggle timer'),
    enabled: true,
  },
  
  // Navigation
  {
    key: 'ArrowLeft',
    description: 'Previous Hand',
    category: 'Navigation',
    action: () => console.log('Previous hand'),
    enabled: true,
  },
  {
    key: 'ArrowRight',
    description: 'Next Hand',
    category: 'Navigation',
    action: () => console.log('Next hand'),
    enabled: true,
  },
  {
    key: 'Escape',
    description: 'Close Modal/Panel',
    category: 'Navigation',
    action: () => console.log('Close modal'),
    enabled: true,
  },
  
  // Help
  {
    key: '?',
    description: 'Show Help',
    category: 'Help',
    action: () => console.log('Show help'),
    enabled: true,
  },
  {
    key: '/',
    description: 'Search',
    category: 'Help',
    action: () => console.log('Open search'),
    enabled: true,
  },
];

interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
  customShortcuts?: KeyboardShortcut[];
  preventDefault?: boolean;
  stopPropagation?: boolean;
}

export const useKeyboardShortcuts = (options: UseKeyboardShortcutsOptions = {}) => {
  const {
    enabled = true,
    customShortcuts = [],
    preventDefault = true,
    stopPropagation = true,
  } = options;

  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([
    ...defaultShortcuts,
    ...customShortcuts,
  ]);
  const [isHelpVisible, setIsHelpVisible] = useState(false);
  const [lastShortcut, setLastShortcut] = useState<string>('');
  const shortcutsRef = useRef<KeyboardShortcut[]>(shortcuts);

  // Update ref when shortcuts change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  // Format shortcut display
  const formatShortcut = useCallback((shortcut: KeyboardShortcut): string => {
    const parts: string[] = [];
    if (shortcut.meta) parts.push('⌘');
    if (shortcut.ctrl) parts.push('Ctrl');
    if (shortcut.alt) parts.push('Alt');
    if (shortcut.shift) parts.push('Shift');
    
    // Format special keys
    let key = shortcut.key;
    if (key === 'ArrowLeft') key = '←';
    else if (key === 'ArrowRight') key = '→';
    else if (key === 'ArrowUp') key = '↑';
    else if (key === 'ArrowDown') key = '↓';
    else if (key === 'Escape') key = 'Esc';
    else if (key === ' ') key = 'Space';
    else key = key.toUpperCase();
    
    parts.push(key);
    
    return parts.join('+');
  }, []);

  // Check if shortcut matches event
  const matchesShortcut = useCallback((event: KeyboardEvent, shortcut: KeyboardShortcut): boolean => {
    return (
      event.key.toLowerCase() === shortcut.key.toLowerCase() &&
      !!event.ctrlKey === !!shortcut.ctrl &&
      !!event.altKey === !!shortcut.alt &&
      !!event.shiftKey === !!shortcut.shift &&
      !!event.metaKey === !!shortcut.meta
    );
  }, []);

  // Handle keyboard event
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;

    // Skip if user is typing in an input field
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.contentEditable === 'true'
    ) {
      return;
    }

    // Find matching shortcut
    const matchingShortcut = shortcutsRef.current.find(
      (shortcut) => shortcut.enabled !== false && matchesShortcut(event, shortcut)
    );

    if (matchingShortcut) {
      if (preventDefault) event.preventDefault();
      if (stopPropagation) event.stopPropagation();

      // Show help modal for ? key
      if (matchingShortcut.key === '?') {
        setIsHelpVisible(true);
      } else {
        matchingShortcut.action();
        setLastShortcut(formatShortcut(matchingShortcut));
      }
    }
  }, [enabled, preventDefault, stopPropagation, matchesShortcut, formatShortcut]);

  // Set up event listener
  useEffect(() => {
    if (enabled) {
      window.addEventListener('keydown', handleKeyDown);
      return () => {
        window.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [enabled, handleKeyDown]);

  // Add custom shortcut
  const addShortcut = useCallback((shortcut: KeyboardShortcut) => {
    setShortcuts((prev) => {
      // Remove existing shortcut with same key combination
      const filtered = prev.filter(
        (s) =>
          !(
            s.key === shortcut.key &&
            s.ctrl === shortcut.ctrl &&
            s.alt === shortcut.alt &&
            s.shift === shortcut.shift &&
            s.meta === shortcut.meta
          )
      );
      return [...filtered, shortcut];
    });
  }, []);

  // Remove shortcut
  const removeShortcut = useCallback((key: string, modifiers?: Partial<KeyboardShortcut>) => {
    setShortcuts((prev) =>
      prev.filter(
        (s) =>
          !(
            s.key === key &&
            s.ctrl === modifiers?.ctrl &&
            s.alt === modifiers?.alt &&
            s.shift === modifiers?.shift &&
            s.meta === modifiers?.meta
          )
      )
    );
  }, []);

  // Update shortcut
  const updateShortcut = useCallback((
    key: string,
    modifiers: Partial<KeyboardShortcut>,
    updates: Partial<KeyboardShortcut>
  ) => {
    setShortcuts((prev) =>
      prev.map((s) =>
        s.key === key &&
        s.ctrl === modifiers.ctrl &&
        s.alt === modifiers.alt &&
        s.shift === modifiers.shift &&
        s.meta === modifiers.meta
          ? { ...s, ...updates }
          : s
      )
    );
  }, []);

  // Toggle shortcut enabled state
  const toggleShortcut = useCallback((key: string, modifiers?: Partial<KeyboardShortcut>) => {
    setShortcuts((prev) =>
      prev.map((s) =>
        s.key === key &&
        s.ctrl === modifiers?.ctrl &&
        s.alt === modifiers?.alt &&
        s.shift === modifiers?.shift &&
        s.meta === modifiers?.meta
          ? { ...s, enabled: !s.enabled }
          : s
      )
    );
  }, []);

  // Get shortcuts by category
  const getShortcutsByCategory = useCallback((): ShortcutCategory[] => {
    const categories: Record<string, KeyboardShortcut[]> = {};
    
    shortcuts.forEach((shortcut) => {
      if (!categories[shortcut.category]) {
        categories[shortcut.category] = [];
      }
      categories[shortcut.category].push(shortcut);
    });

    return Object.entries(categories).map(([name, shortcuts]) => ({
      name,
      shortcuts,
    }));
  }, [shortcuts]);

  // Reset to defaults
  const resetToDefaults = useCallback(() => {
    setShortcuts([...defaultShortcuts, ...customShortcuts]);
  }, [customShortcuts]);

  // Export shortcuts configuration
  const exportShortcuts = useCallback((): string => {
    return JSON.stringify(shortcuts, null, 2);
  }, [shortcuts]);

  // Import shortcuts configuration
  const importShortcuts = useCallback((json: string) => {
    try {
      const imported = JSON.parse(json) as KeyboardShortcut[];
      setShortcuts(imported);
      return true;
    } catch (error) {
      console.error('Failed to import shortcuts:', error);
      return false;
    }
  }, []);

  return {
    shortcuts,
    isHelpVisible,
    setIsHelpVisible,
    lastShortcut,
    addShortcut,
    removeShortcut,
    updateShortcut,
    toggleShortcut,
    getShortcutsByCategory,
    resetToDefaults,
    exportShortcuts,
    importShortcuts,
    formatShortcut,
  };
};

// Helper component for displaying shortcuts
export const KeyboardShortcutDisplay: React.FC<{
  shortcut: KeyboardShortcut;
  compact?: boolean;
}> = ({ shortcut, compact = false }) => {
  const formatKey = (key: string): string => {
    if (key === 'ArrowLeft') return '←';
    if (key === 'ArrowRight') return '→';
    if (key === 'ArrowUp') return '↑';
    if (key === 'ArrowDown') return '↓';
    if (key === 'Escape') return 'Esc';
    if (key === ' ') return 'Space';
    return key.toUpperCase();
  };

  const parts: string[] = [];
  if (shortcut.meta) parts.push('⌘');
  if (shortcut.ctrl) parts.push('Ctrl');
  if (shortcut.alt) parts.push('Alt');
  if (shortcut.shift) parts.push('⇧');
  parts.push(formatKey(shortcut.key));

  if (compact) {
    return <span>{parts.join('')}</span>;
  }

  return (
    <span style={{ display: 'inline-flex', gap: '2px' }}>
      {parts.map((part, index) => (
        <kbd
          key={index}
          style={{
            padding: '2px 4px',
            backgroundColor: '#f0f0f0',
            border: '1px solid #ccc',
            borderRadius: '3px',
            fontSize: '0.85em',
            fontFamily: 'monospace',
          }}
        >
          {part}
        </kbd>
      ))}
    </span>
  );
};
