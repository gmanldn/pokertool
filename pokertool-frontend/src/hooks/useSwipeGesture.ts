import { useState, useEffect, useRef, useCallback } from 'react';

export interface SwipeGestureOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  minSwipeDistance?: number;
  maxSwipeTime?: number;
}

export interface SwipeGestureState {
  isSwiping: boolean;
  direction: 'left' | 'right' | 'up' | 'down' | null;
}

/**
 * Custom hook for detecting swipe gestures on touch devices
 * 
 * @param options - Configuration options for swipe detection
 * @returns Ref to attach to swipeable element and current swipe state
 * 
 * @example
 * const { ref, swipeState } = useSwipeGesture({
 *   onSwipeLeft: () => navigate('/next'),
 *   onSwipeRight: () => navigate('/prev'),
 *   minSwipeDistance: 50,
 * });
 * 
 * return <div ref={ref}>Swipeable content</div>;
 */
export const useSwipeGesture = (options: SwipeGestureOptions = {}) => {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    minSwipeDistance = 50,
    maxSwipeTime = 500,
  } = options;

  const [swipeState, setSwipeState] = useState<SwipeGestureState>({
    isSwiping: false,
    direction: null,
  });

  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const elementRef = useRef<HTMLElement | null>(null);

  const handleTouchStart = useCallback((e: TouchEvent) => {
    const touch = e.touches[0];
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };
    setSwipeState({ isSwiping: true, direction: null });
  }, []);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!touchStartRef.current) return;

    const touch = e.touches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;

    // Determine direction based on larger delta
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // Horizontal swipe
      if (Math.abs(deltaX) > minSwipeDistance / 2) {
        setSwipeState({
          isSwiping: true,
          direction: deltaX > 0 ? 'right' : 'left',
        });
      }
    } else {
      // Vertical swipe
      if (Math.abs(deltaY) > minSwipeDistance / 2) {
        setSwipeState({
          isSwiping: true,
          direction: deltaY > 0 ? 'down' : 'up',
        });
      }
    }
  }, [minSwipeDistance]);

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (!touchStartRef.current) return;

    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;
    const deltaTime = Date.now() - touchStartRef.current.time;

    // Check if swipe meets criteria
    if (deltaTime <= maxSwipeTime) {
      const absX = Math.abs(deltaX);
      const absY = Math.abs(deltaY);

      // Horizontal swipe
      if (absX > absY && absX > minSwipeDistance) {
        if (deltaX > 0 && onSwipeRight) {
          onSwipeRight();
        } else if (deltaX < 0 && onSwipeLeft) {
          onSwipeLeft();
        }
      }
      // Vertical swipe
      else if (absY > absX && absY > minSwipeDistance) {
        if (deltaY > 0 && onSwipeDown) {
          onSwipeDown();
        } else if (deltaY < 0 && onSwipeUp) {
          onSwipeUp();
        }
      }
    }

    // Reset state
    touchStartRef.current = null;
    setSwipeState({ isSwiping: false, direction: null });
  }, [maxSwipeTime, minSwipeDistance, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Add event listeners
    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchmove', handleTouchMove, { passive: true });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    // Cleanup
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    ref: elementRef,
    swipeState,
  };
};
