import React from 'react';
import { ShieldCheck, Cpu, Database } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="footer-container">
      <div className="footer-content">
        <div className="footer-top">
          <div className="footer-brand">
            <span className="footer-logo">PocketSmart AI</span>
            <p className="footer-description">
              GenAI-powered smart budget planning and cross-platform recommendation system.
              A college capstone engineering project combining Google Gemini AI with deterministic financial safeguards.
            </p>
          </div>

          <div className="footer-badges">
            <div className="tech-badge">
              <Cpu size={14} />
              <span>Google Gemini AI</span>
            </div>
            <div className="tech-badge">
              <ShieldCheck size={14} />
              <span>Deterministic Budget Engine</span>
            </div>
            <div className="tech-badge">
              <Database size={14} />
              <span>FastAPI & SQLite / React 19</span>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p className="footer-copy">
            © 2026 PocketSmart AI — Academic Capstone Project. Currency configured to Indian Rupee (₹ INR).
          </p>
          <div className="footer-modules-list">
            <span>Home Interior</span>
            <span className="dot">•</span>
            <span>Party & Events</span>
            <span className="dot">•</span>
            <span>Jewelry & Multimodal Vision</span>
            <span className="dot">•</span>
            <span>Saved Plans</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
