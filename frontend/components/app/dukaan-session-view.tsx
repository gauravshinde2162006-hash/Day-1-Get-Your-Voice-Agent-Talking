'use client';

import React from 'react';
import { useAgent, useSessionContext } from '@livekit/components-react';
import { AudioVisualizer } from '@/components/agents-ui/blocks/agent-session-view-01/components/audio-visualizer';
import { AgentControlBar } from '@/components/agents-ui/agent-control-bar';
import type { AgentSessionView_01Props } from '@/components/agents-ui/blocks/agent-session-view-01/components/agent-session-block';
import { ShopfrontIllustration } from '@/components/app/shopfront-illustration';

/* ---------- Inline SVG icons for each state ---------- */
function ConnectingIcon() {
  return <div className="dukaan-connecting-spinner" />;
}

function ListeningIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

function SpeakingIcon() {
  return (
    <div className="dukaan-sound-bars">
      <div className="dukaan-sound-bar" />
      <div className="dukaan-sound-bar" />
      <div className="dukaan-sound-bar" />
      <div className="dukaan-sound-bar" />
      <div className="dukaan-sound-bar" />
    </div>
  );
}

function ThinkingIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  );
}

function EndedIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function RestartIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

interface DukaanSessionViewProps extends React.ComponentProps<'section'>, AgentSessionView_01Props {
  hasEnded?: boolean;
  onRestart?: () => void;
}

export function DukaanSessionView({
  audioVisualizerType = 'wave',
  audioVisualizerColor = '#f97316',
  audioVisualizerColorShift = 0,
  audioVisualizerBarCount = 5,
  audioVisualizerRadialBarCount = 30,
  audioVisualizerRadialRadius = 50,
  audioVisualizerGridRowCount = 5,
  audioVisualizerGridColumnCount = 5,
  audioVisualizerWaveLineWidth = 4,
  hasEnded = false,
  onRestart,
  className,
}: DukaanSessionViewProps) {
  const session = useSessionContext();
  const { state: agentState } = useAgent();

  // Determine current visual state
  type VisualState = 'connecting' | 'listening' | 'speaking' | 'thinking' | 'ended';
  let visualState: VisualState = 'connecting';
  let stateText = 'Judai ho rahe hain...';
  let stateSubtext = 'Kripya thoda intezaar karein';

  if (hasEnded && !session.isConnected) {
    visualState = 'ended';
    stateText = 'Baat khatam ho gayi';
    stateSubtext = 'Dhanyavaad! Phir se baat karne ke liye neeche click karein';
  } else if (session.isConnected) {
    if (agentState === 'speaking') {
      visualState = 'speaking';
      stateText = 'Dukaan Mitra bol raha hai...';
      stateSubtext = 'Agent aapko jawaab de raha hai';
    } else if (agentState === 'listening') {
      visualState = 'listening';
      stateText = 'Sun raha hoon...';
      stateSubtext = 'Aap bol sakte hain';
    } else if (agentState === 'thinking') {
      visualState = 'thinking';
      stateText = 'Soch raha hoon...';
      stateSubtext = 'Jawaab tayyaar ho raha hai';
    } else {
      visualState = 'connecting';
      stateText = 'Kripya intezaar karein...';
      stateSubtext = 'Agent se connection ho raha hai';
    }
  }

  // For ended state — show a different layout
  if (visualState === 'ended') {
    return (
      <section className={`bg-[#06060f] fixed inset-0 z-[100] h-svh w-svw overflow-hidden flex flex-col ${className || ''}`}>
        <div className="dukaan-bg-gradient-1" />
        <div className="dukaan-bg-gradient-2" />
        <div className="dukaan-bg-grid" />
        <div className="dukaan-shopfront-bg">
          <ShopfrontIllustration className="dukaan-shopfront-svg" />
        </div>
        <div className="dukaan-shopfront-overlay" />

        <div className="flex-1 flex flex-col items-center justify-center relative z-20 px-4">
          <div className="dukaan-ended-card">
            <div className={`dukaan-state-indicator dukaan-state-ended`}>
              <div className="dukaan-state-icon">
                <EndedIcon />
              </div>
              <div className="dukaan-state-text">{stateText}</div>
            </div>
            <p>Aapki baat Dukaan Mitra ke saath khatam ho gayi. Agar aapko kuch aur chahiye toh phir se call karein!</p>
            <button className="dukaan-restart-btn" onClick={onRestart}>
              <RestartIcon />
              Phir se Baat Karein
            </button>
          </div>
        </div>

        <div className="dukaan-footer">
          <p>
            Built for <strong>#VoiceForBharat</strong> · 10 Days of Voice Agents Challenge
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className={`bg-[#06060f] fixed inset-0 z-[100] h-svh w-svw overflow-hidden flex flex-col ${className || ''}`}>
      {/* Background gradients */}
      <div className="dukaan-bg-gradient-1" />
      <div className="dukaan-bg-gradient-2" />
      <div className="dukaan-bg-grid" />

      {/* Shopfront illustration background */}
      <div className="dukaan-shopfront-bg">
        <ShopfrontIllustration className="dukaan-shopfront-svg" />
      </div>
      {/* Dark overlay on top of illustration for readability */}
      <div className="dukaan-shopfront-overlay" />

      {/* Main content area */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-20">
        {/* State indicator */}
        <div className={`dukaan-state-indicator dukaan-state-${visualState}`}>
          <div className="dukaan-state-icon" style={{ position: 'relative' }}>
            {visualState === 'connecting' && <ConnectingIcon />}
            {visualState === 'listening' && (
              <>
                <ListeningIcon />
                <div className="dukaan-mic-pulse" />
              </>
            )}
            {visualState === 'speaking' && <SpeakingIcon />}
            {visualState === 'thinking' && <ThinkingIcon />}
          </div>
          <div className="dukaan-state-text">{stateText}</div>
          <div className="dukaan-state-subtext">{stateSubtext}</div>
        </div>

        {/* Visualizer Tile */}
        <div className="relative w-full max-w-lg h-48 md:h-72 mx-auto flex items-center justify-center">
           {session.isConnected ? (
             <AudioVisualizer
              isChatOpen={false}
              audioVisualizerType={audioVisualizerType}
              audioVisualizerColor={agentState === 'speaking' ? '#fbbf24' : audioVisualizerColor}
              audioVisualizerColorShift={audioVisualizerColorShift}
              audioVisualizerBarCount={audioVisualizerBarCount}
              audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
              audioVisualizerRadialRadius={audioVisualizerRadialRadius}
              audioVisualizerGridRowCount={audioVisualizerGridRowCount}
              audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
              audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
              className="bg-transparent"
            />
           ) : (
             <div className="dukaan-connecting-spinner" style={{ width: 48, height: 48, borderWidth: 4 }} />
           )}
        </div>
      </div>

      {/* Control Bar */}
      <div className="relative z-30 w-full max-w-xl mx-auto pb-6 px-4">
        <AgentControlBar
          variant="livekit"
          controls={{
            leave: true,
            microphone: true,
            chat: false,
            camera: false,
            screenShare: false,
          }}
          isChatOpen={false}
          isConnected={session.isConnected}
          onDisconnect={session.end}
          onIsChatOpenChange={() => {}}
        />
      </div>
    </section>
  );
}
