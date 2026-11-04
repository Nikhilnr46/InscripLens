import React from 'react';
import { Sparkles, Layers, Search, Cpu, Globe } from 'lucide-react';

const MARQUEE_ITEMS = [
  { label: 'Enhance', icon: Sparkles },
  { label: 'Foreground mask', icon: Layers },
  { label: 'Candidate regions', icon: Search },
  { label: 'Kannada inscriptions', icon: Globe },
  { label: 'Runs locally', icon: Cpu }
];

export default function Marquee() {
  // Repeat items 4 times to ensure uninterrupted looping across any ultrawide viewport
  const duplicatedItems = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS, ...MARQUEE_ITEMS, ...MARQUEE_ITEMS];

  return (
    <div className="landing-marquee-wrapper" aria-hidden="true">
      <div className="landing-marquee-track">
        {duplicatedItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <div key={index} className="landing-marquee-item">
              <span className="marquee-dot">·</span>
              <Icon size={14} className="marquee-icon" />
              <span className="marquee-text">{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

