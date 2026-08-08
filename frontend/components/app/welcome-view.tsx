import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ShopfrontIllustration } from '@/components/app/shopfront-illustration';

function StoreIcon() {
  return (
    <div className="dukaan-orb-container">
      <div className="dukaan-orb-glow" />
      <div className="dukaan-orb" style={{ background: 'linear-gradient(135deg, #f97316 0%, #fbbf24 100%)', boxShadow: '0 0 40px rgba(249,115,22,0.3)', border: '1px solid rgba(253,186,116,0.3)' }}>
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      </div>
      {/* Floating particles */}
      <div className="dukaan-particle dukaan-particle-1" />
      <div className="dukaan-particle dukaan-particle-2" />
      <div className="dukaan-particle dukaan-particle-3" />
      <div className="dukaan-particle dukaan-particle-4" />
      <div className="dukaan-particle dukaan-particle-5" />
      <div className="dukaan-particle dukaan-particle-6" />
    </div>
  );
}

function FeaturePill({ text }: { text: string }) {
  return (
    <span className="dukaan-pill">
      {text}
    </span>
  );
}

/** Mic error card with step-by-step bilingual instructions */
function MicErrorCard({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="dukaan-mic-error">
      <div className="dukaan-mic-error-header">
        <div className="dukaan-mic-error-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="1" y1="1" x2="23" y2="23" />
            <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
            <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .76-.12 1.49-.34 2.18" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
        </div>
        <span className="dukaan-mic-error-title">🎤 Microphone Access Denied</span>
      </div>
      <ul className="dukaan-mic-error-steps">
        <li>
          <span className="dukaan-mic-error-step-num">1</span>
          <span>Browser ke address bar mein 🔒 lock icon par click karein</span>
        </li>
        <li>
          <span className="dukaan-mic-error-step-num">2</span>
          <span>Site Settings ya Permissions kholein</span>
        </li>
        <li>
          <span className="dukaan-mic-error-step-num">3</span>
          <span>Microphone → <strong>Allow</strong> select karein</span>
        </li>
        <li>
          <span className="dukaan-mic-error-step-num">4</span>
          <span>Page refresh karein ya neeche Retry dabayein</span>
        </li>
      </ul>
      <button className="dukaan-mic-error-retry" onClick={onRetry}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="23 4 23 10 17 10" />
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
        </svg>
        Retry Karein
      </button>
    </div>
  );
}

/** Generic error card for non-mic errors */
function GenericErrorCard({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="dukaan-mic-error" style={{ borderColor: 'rgba(249, 115, 22, 0.2)', background: 'rgba(249, 115, 22, 0.06)' }}>
      <div className="dukaan-mic-error-header">
        <div className="dukaan-mic-error-icon" style={{ background: 'rgba(249, 115, 22, 0.15)' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f97316" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <span className="dukaan-mic-error-title" style={{ color: '#fdba74' }}>⚠️ Connection Error</span>
      </div>
      <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '12px' }}>
        {message}
      </p>
      <button className="dukaan-mic-error-retry" style={{ borderColor: 'rgba(249, 115, 22, 0.3)', color: '#fdba74', background: 'rgba(249, 115, 22, 0.1)' }} onClick={onRetry}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="23 4 23 10 17 10" />
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
        </svg>
        Retry
      </button>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [error, setError] = useState<string | null>(null);
  const [isMicError, setIsMicError] = useState(false);

  const handleStart = async () => {
    try {
      setError(null);
      setIsMicError(false);
      await onStartCall();
    } catch (e: any) {
      if (
        e?.message?.includes('NotAllowedError') ||
        e?.name === 'NotAllowedError' ||
        e?.message?.includes('Permission denied') ||
        e?.message?.includes('permission')
      ) {
        setError('mic');
        setIsMicError(true);
      } else {
        setError(e?.message || 'Kuch gadbad ho gayi. Kripya phir se try karein.');
        setIsMicError(false);
      }
    }
  };

  return (
    <div ref={ref} className="dukaan-welcome-root">
      {/* Background gradient effects */}
      <div className="dukaan-bg-gradient-1" />
      <div className="dukaan-bg-gradient-2" />
      <div className="dukaan-bg-grid" />

      {/* Shopfront illustration background */}
      <div className="dukaan-shopfront-bg">
        <ShopfrontIllustration className="dukaan-shopfront-svg" />
      </div>
      <div className="dukaan-shopfront-overlay" />

      <section className="dukaan-welcome-section">
        {/* Badge */}
        <div className="dukaan-badge">
          <span className="dukaan-badge-dot" />
          <span>Local Commerce AI</span>
        </div>

        {/* Orb -> Store Icon */}
        <StoreIcon />

        {/* Title */}
        <h1 className="dukaan-title">
          Dukaan <span className="dukaan-title-accent">Mitra</span>
        </h1>

        <p className="dukaan-subtitle">
          Aapka apna AI shop assistant.
          <br />
          Order likhwayen, stock check karein — bas baat karke.
        </p>

        {/* Feature pills */}
        <div className="dukaan-pills-row">
          <FeaturePill text="📦 Inventory" />
          <FeaturePill text="💰 Billing" />
          <FeaturePill text="📱 UPI & Payments" />
          <FeaturePill text="📊 GST Help" />
        </div>

        {/* CTA Button */}
        <Button
          size="lg"
          onClick={handleStart}
          className="dukaan-cta-button"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" x2="12" y1="19" y2="22"/>
          </svg>
          {startButtonText}
        </Button>

        {/* Error displays */}
        {isMicError && <MicErrorCard onRetry={handleStart} />}
        {error && !isMicError && <GenericErrorCard message={error} onRetry={handleStart} />}

        <p className="dukaan-voice-info">
          🗣️ Powered by <strong>Murf Falcon</strong> · Indian English Voice
        </p>
      </section>

      {/* Footer */}
      <div className="dukaan-footer">
        <p>
          Built for <strong>#VoiceForBharat</strong> · 10 Days of Voice Agents Challenge
        </p>
      </div>
    </div>
  );
};
