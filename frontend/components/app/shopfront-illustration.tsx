'use client';

import React from 'react';
import Image from 'next/image';

/**
 * ShopfrontIllustration — Renders a high-quality photorealistic image of the shopfront
 * (stored in public/shopfront-bg.png).
 */
export function ShopfrontIllustration({ className }: { className?: string }) {
  return (
    <img
      src="/shopfront-bg.png"
      alt="Grocery Shopfront"
      className={className}
      style={{ objectFit: 'cover', objectPosition: 'center center', transform: 'scale(1.15)', position: 'absolute', inset: 0, width: '100%', height: '100%' }}
    />
  );
}
