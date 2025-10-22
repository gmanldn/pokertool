/**Terminal Context Menu - Right-click menu for copy/paste*/
import React, { useState, useCallback } from 'react';
import { Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material';
import {
  ContentCopy as CopyIcon,
  ContentPaste as PasteIcon,
  SelectAll as SelectAllIcon,
  Clear as ClearIcon
} from '@mui/icons-material';

export interface TerminalContextMenuProps {
  terminalRef: React.RefObject<any>;
  onCopy?: () => void;
  onPaste?: (text: string) => void;
  onSelectAll?: () => void;
  onClear?: () => void;
}

export const useTerminalContextMenu = () => {
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);

  const handleContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    setContextMenu(
      contextMenu === null
        ? { mouseX: event.clientX + 2, mouseY: event.clientY - 6 }
        : null
    );
  }, [contextMenu]);

  const handleClose = useCallback(() => {
    setContextMenu(null);
  }, []);

  return { contextMenu, handleContextMenu, handleClose };
};

export const TerminalContextMenu: React.FC<TerminalContextMenuProps & {
  contextMenu: { mouseX: number; mouseY: number } | null;
  onClose: () => void;
}> = ({ contextMenu, onClose, terminalRef, onCopy, onPaste, onSelectAll, onClear }) => {
  const handleCopy = async () => {
    if (onCopy) {
      onCopy();
    } else if (terminalRef.current) {
      // Default copy implementation using xterm.js selection
      const terminal = terminalRef.current;
      const selection = terminal.getSelection();
      if (selection) {
        try {
          await navigator.clipboard.writeText(selection);
        } catch (err) {
          console.error('Failed to copy:', err);
        }
      }
    }
    onClose();
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (onPaste) {
        onPaste(text);
      } else if (terminalRef.current) {
        // Default paste implementation
        terminalRef.current.paste(text);
      }
    } catch (err) {
      console.error('Failed to paste:', err);
    }
    onClose();
  };

  const handleSelectAll = () => {
    if (onSelectAll) {
      onSelectAll();
    } else if (terminalRef.current) {
      // Default select all implementation
      terminalRef.current.selectAll();
    }
    onClose();
  };

  const handleClear = () => {
    if (onClear) {
      onClear();
    } else if (terminalRef.current) {
      // Default clear implementation
      terminalRef.current.clear();
    }
    onClose();
  };

  return (
    <Menu
      open={contextMenu !== null}
      onClose={onClose}
      anchorReference="anchorPosition"
      anchorPosition={
        contextMenu !== null
          ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
          : undefined
      }
    >
      <MenuItem onClick={handleCopy}>
        <ListItemIcon>
          <CopyIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>Copy</ListItemText>
      </MenuItem>
      <MenuItem onClick={handlePaste}>
        <ListItemIcon>
          <PasteIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>Paste</ListItemText>
      </MenuItem>
      <MenuItem onClick={handleSelectAll}>
        <ListItemIcon>
          <SelectAllIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>Select All</ListItemText>
      </MenuItem>
      <MenuItem onClick={handleClear}>
        <ListItemIcon>
          <ClearIcon fontSize="small" />
        </ListItemIcon>
        <ListItemText>Clear Terminal</ListItemText>
      </MenuItem>
    </Menu>
  );
};
