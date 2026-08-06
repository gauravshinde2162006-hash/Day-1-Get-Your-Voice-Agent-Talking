import { Button } from '@/components/ui/button';

function PulsingOrb() {
  return (
    <div className="dukaan-orb-container">
      <div className="dukaan-orb-glow" />
      <div className="dukaan-orb">
        <svg
          width="40"
          height="40"
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M10 14V26C10 26.5304 9.78929 27.0391 9.41421 27.4142C9.03914 27.7893 8.53043 28 8 28C7.46957 28 6.96086 27.7893 6.58579 27.4142C6.21071 27.0391 6 26.5304 6 26V14C6 13.4696 6.21071 12.9609 6.58579 12.5858C6.96086 12.2107 7.46957 12 8 12C8.53043 12 9.03914 12.2107 9.41421 12.5858C9.78929 12.9609 10 13.4696 10 14ZM15 3C14.4696 3 13.9609 3.21071 13.5858 3.58579C13.2107 3.96086 13 4.46957 13 5V35C13 35.5304 13.2107 36.0391 13.5858 36.4142C13.9609 36.7893 14.4696 37 15 37C15.5304 37 16.0391 36.7893 16.4142 36.4142C16.7893 36.0391 17 35.5304 17 35V5C17 4.46957 16.7893 3.96086 16.4142 3.58579C16.0391 3.21071 15.5304 3 15 3ZM22 8C21.4696 8 20.9609 8.21071 20.5858 8.58579C20.2107 8.96086 20 9.46957 20 10V30C20 30.5304 20.2107 31.0391 20.5858 31.4142C20.9609 31.7893 21.4696 32 22 32C22.5304 32 23.0391 31.7893 23.4142 31.4142C23.7893 31.0391 24 30.5304 24 30V10C24 9.46957 23.7893 8.96086 23.4142 8.58579C23.0391 8.21071 22.5304 8 22 8ZM29 12C28.4696 12 27.9609 12.2107 27.5858 12.5858C27.2107 12.9609 27 13.4696 27 14V26C27 26.5304 27.2107 27.0391 27.5858 27.4142C27.9609 27.7893 28.4696 28 29 28C29.5304 28 30.0391 27.7893 30.4142 27.4142C30.7893 27.0391 31 26.5304 31 26V14C31 13.4696 30.7893 12.9609 30.4142 12.5858C30.0391 12.2107 29.5304 12 29 12ZM36 10C35.4696 10 34.9609 10.2107 34.5858 10.5858C34.2107 10.9609 34 11.4696 34 12V28C34 28.5304 34.2107 29.0391 34.5858 29.4142C34.9609 29.7893 35.4696 30 36 30C36.5304 30 37.0391 29.7893 37.4142 29.4142C37.7893 29.0391 38 28.5304 38 28V12C38 11.4696 37.7893 10.9609 37.4142 10.5858C37.0391 10.2107 36.5304 10 36 10Z"
            fill="currentColor"
          />
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

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="dukaan-welcome-root">
      {/* Background gradient effects */}
      <div className="dukaan-bg-gradient-1" />
      <div className="dukaan-bg-gradient-2" />
      <div className="dukaan-bg-grid" />

      <section className="dukaan-welcome-section">
        {/* Badge */}
        <div className="dukaan-badge">
          <span className="dukaan-badge-dot" />
          <span>Local Commerce AI</span>
        </div>

        {/* Orb */}
        <PulsingOrb />

        {/* Title */}
        <h1 className="dukaan-title">
          Dukaan <span className="dukaan-title-accent">Mitra</span>
        </h1>

        <p className="dukaan-subtitle">
          Your AI-powered shop assistant for Indian local businesses.
          <br />
          Manage inventory, billing, payments & more — just by talking.
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
          onClick={onStartCall}
          className="dukaan-cta-button"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" x2="12" y1="19" y2="22"/>
          </svg>
          {startButtonText}
        </Button>

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
