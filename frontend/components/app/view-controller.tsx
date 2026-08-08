'use client';
import React, { useState, useEffect, useRef } from 'react';

import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { DukaanSessionView } from '@/components/app/dukaan-session-view';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(DukaanSessionView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const [hasEnded, setHasEnded] = useState(false);

  useEffect(() => {
    if (isConnected) {
      setHasEnded(false);
    }
  }, [isConnected]);

  const wasConnected = useRef(false);
  useEffect(() => {
    if (isConnected) wasConnected.current = true;
    if (!isConnected && wasConnected.current) {
      setHasEnded(true);
    }
  }, [isConnected]);

  // Show ended state inside session view when call has ended
  const showSessionView = isConnected || hasEnded;

  const handleRestart = () => {
    setHasEnded(false);
    // Small delay to allow welcome view to render before starting
    setTimeout(() => {
      start();
    }, 100);
  };

  return (
    <AnimatePresence mode="wait">
      {/* Welcome view — shown only when not connected and not ended */}
      {!showSessionView && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText="Baat Shuru Karein"
          onStartCall={start}
        />
      )}
      {/* Session view — shown when connected OR when call has ended (to show ended state) */}
      {showSessionView && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          hasEnded={hasEnded && !isConnected}
          onRestart={handleRestart}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
