/**
 * Draggable Panel Grid Component
 *
 * Allows users to reorder SmartHelper panels via drag-and-drop
 * Uses react-beautiful-dnd for smooth drag interactions
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Chip
} from '@mui/material';
import {
  DragIndicator,
  Settings,
  LockOpen,
  Lock
} from '@mui/icons-material';

export interface PanelConfig {
  id: string;
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
  statusChip?: React.ReactNode;
  locked?: boolean; // Prevent reordering
  minHeight?: number;
}

interface DraggablePanelGridProps {
  panels: PanelConfig[];
  onPanelOrderChange?: (newOrder: string[]) => void;
  enableDragDrop?: boolean;
  columns?: 1 | 2 | 3 | 4; // Grid columns
}

export const DraggablePanelGrid: React.FC<DraggablePanelGridProps> = ({
  panels: initialPanels,
  onPanelOrderChange,
  enableDragDrop = true,
  columns = 2
}) => {
  const [panels, setPanels] = useState<PanelConfig[]>(initialPanels);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>, index: number) => {
    if (!enableDragDrop || panels[index].locked) {
      e.preventDefault();
      return;
    }

    setDraggedIndex(index);
    setIsDragging(true);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.currentTarget.id);

    // Add ghost image
    if (e.currentTarget) {
      e.dataTransfer.setDragImage(e.currentTarget, 50, 50);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>, index: number) => {
    if (!enableDragDrop || panels[index].locked) {
      return;
    }

    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    if (draggedIndex !== null && draggedIndex !== index) {
      setDragOverIndex(index);
    }
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>, index: number) => {
    if (!enableDragDrop || panels[index].locked) {
      return;
    }

    e.preventDefault();
    setDragOverIndex(index);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOverIndex(null);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>, dropIndex: number) => {
    e.preventDefault();
    e.stopPropagation();

    if (draggedIndex === null || !enableDragDrop || panels[dropIndex].locked) {
      return;
    }

    const newPanels = [...panels];
    const [draggedPanel] = newPanels.splice(draggedIndex, 1);
    newPanels.splice(dropIndex, 0, draggedPanel);

    setPanels(newPanels);

    if (onPanelOrderChange) {
      onPanelOrderChange(newPanels.map(p => p.id));
    }

    setDraggedIndex(null);
    setDragOverIndex(null);
    setIsDragging(false);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    setDragOverIndex(null);
    setIsDragging(false);
  };

  const resetOrder = () => {
    setPanels(initialPanels);
    if (onPanelOrderChange) {
      onPanelOrderChange(initialPanels.map(p => p.id));
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Controls */}
      {enableDragDrop && (
        <Box sx={{ display: 'flex', gap: 1, mb: 2, justifyContent: 'flex-end', alignItems: 'center' }}>
          <Typography variant="caption" color="textSecondary" sx={{ mr: 'auto' }}>
            {isDragging ? 'Drop to reorder' : 'Drag panels to reorder'}
          </Typography>
          <Tooltip title="Reset to Default Order">
            <IconButton size="small" onClick={resetOrder} sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              <Settings fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      {/* Panel Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gap: 2,
          '@media (max-width: 900px)': {
            gridTemplateColumns: '1fr'
          }
        }}
      >
        {panels.map((panel, index) => {
          const isBeingDragged = draggedIndex === index;
          const isDropTarget = dragOverIndex === index;

          return (
            <Box
              key={panel.id}
              id={`panel-${panel.id}`}
              draggable={enableDragDrop && !panel.locked}
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnter={(e) => handleDragEnter(e, index)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, index)}
              onDragEnd={handleDragEnd}
              sx={{
                position: 'relative',
                opacity: isBeingDragged ? 0.5 : 1,
                transform: isDropTarget ? 'scale(0.98)' : 'scale(1)',
                transition: 'all 0.2s ease',
                cursor: enableDragDrop && !panel.locked ? 'move' : 'default',
                minHeight: panel.minHeight || 'auto',
                gridColumn: columns === 1 ? 'span 1' : undefined
              }}
            >
              <Paper
                elevation={isDropTarget ? 8 : 2}
                sx={{
                  p: 2,
                  height: '100%',
                  backgroundColor: 'rgba(33, 33, 33, 0.9)',
                  border: isDropTarget
                    ? '2px solid rgba(33, 150, 243, 0.6)'
                    : '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 2,
                  transition: 'all 0.2s ease',
                  position: 'relative',
                  '&:hover': enableDragDrop && !panel.locked ? {
                    boxShadow: '0 4px 12px rgba(33, 150, 243, 0.3)',
                    borderColor: 'rgba(33, 150, 243, 0.5)'
                  } : {}
                }}
              >
                {/* Panel Header */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  {/* Drag Handle */}
                  {enableDragDrop && !panel.locked && (
                    <DragIndicator
                      sx={{
                        color: 'rgba(255, 255, 255, 0.4)',
                        cursor: 'move',
                        fontSize: 20,
                        '&:hover': {
                          color: 'primary.main'
                        }
                      }}
                    />
                  )}

                  {/* Lock Icon */}
                  {panel.locked && (
                    <Lock
                      sx={{
                        color: 'rgba(255, 255, 255, 0.3)',
                        fontSize: 16
                      }}
                    />
                  )}

                  {/* Panel Icon */}
                  {panel.icon}

                  {/* Panel Title */}
                  <Typography variant="subtitle2" fontWeight="bold" color="white">
                    {panel.title}
                  </Typography>

                  {/* Status Chip */}
                  {panel.statusChip && (
                    <Box sx={{ ml: 'auto' }}>
                      {panel.statusChip}
                    </Box>
                  )}
                </Box>

                {/* Panel Content */}
                <Box>
                  {panel.content}
                </Box>

                {/* Drag Overlay */}
                {isBeingDragged && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      backgroundColor: 'rgba(33, 150, 243, 0.1)',
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      pointerEvents: 'none'
                    }}
                  >
                    <Typography variant="h6" color="primary.main" fontWeight="bold">
                      Dragging...
                    </Typography>
                  </Box>
                )}

                {/* Drop Target Indicator */}
                {isDropTarget && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: -4,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: '80%',
                      height: 4,
                      backgroundColor: 'primary.main',
                      borderRadius: 2,
                      boxShadow: '0 0 8px rgba(33, 150, 243, 0.8)',
                      pointerEvents: 'none'
                    }}
                  />
                )}
              </Paper>
            </Box>
          );
        })}
      </Box>

      {/* Empty State */}
      {panels.length === 0 && (
        <Box
          sx={{
            p: 4,
            textAlign: 'center',
            color: 'rgba(255, 255, 255, 0.5)',
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 2,
            border: '1px dashed rgba(255, 255, 255, 0.1)'
          }}
        >
          <Typography variant="body2">
            No panels configured
          </Typography>
        </Box>
      )}
    </Box>
  );
};

/**
 * Hook to manage panel order state
 */
export const usePanelOrder = (defaultOrder: string[]) => {
  const [panelOrder, setPanelOrder] = useState<string[]>(defaultOrder);

  const reorderPanels = <T extends { id: string }>(items: T[]): T[] => {
    const orderMap = new Map(panelOrder.map((id, index) => [id, index]));
    return [...items].sort((a, b) => {
      const aIndex = orderMap.get(a.id) ?? 999;
      const bIndex = orderMap.get(b.id) ?? 999;
      return aIndex - bIndex;
    });
  };

  const handleOrderChange = (newOrder: string[]) => {
    setPanelOrder(newOrder);
    // Persist to localStorage or backend
    try {
      localStorage.setItem('smarthelper-panel-order', JSON.stringify(newOrder));
    } catch (e) {
      console.error('Failed to save panel order:', e);
    }
  };

  const loadSavedOrder = () => {
    try {
      const saved = localStorage.getItem('smarthelper-panel-order');
      if (saved) {
        setPanelOrder(JSON.parse(saved));
      }
    } catch (e) {
      console.error('Failed to load panel order:', e);
    }
  };

  return {
    panelOrder,
    setPanelOrder,
    reorderPanels,
    handleOrderChange,
    loadSavedOrder
  };
};
