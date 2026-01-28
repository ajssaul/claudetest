'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import type { SignatureStyle } from '../lib/signatureStyles';

interface SignatureCanvasProps {
  text: string;
  style: SignatureStyle;
  showWatermark?: boolean;
  animated?: boolean;
  onAnimationComplete?: () => void;
}

export default function SignatureCanvas({
  text,
  style,
  showWatermark = false,
  animated = false,
  onAnimationComplete,
}: SignatureCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [isAnimating, setIsAnimating] = useState(animated);

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => {
        setIsAnimating(false);
        onAnimationComplete?.();
      }, text.length * 200 + 500);
      return () => clearTimeout(timer);
    }
  }, [animated, text.length, onAnimationComplete]);

  return (
    <div
      ref={canvasRef}
      className="relative w-full h-full flex items-center justify-center overflow-hidden bg-white"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E")`,
      }}
    >
      {/* Signature Text */}
      <motion.div
        initial={animated ? { opacity: 0 } : { opacity: 1 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10"
        style={{
          fontFamily: style.fontFamily,
          fontSize: `${style.fontSize}px`,
          transform: `rotate(${style.rotation}deg)`,
          letterSpacing: `${style.letterSpacing}em`,
          color: style.color,
          WebkitTextStroke: style.strokeWidth > 0 ? `${style.strokeWidth}px ${style.color}` : 'none',
        }}
      >
        {isAnimating ? (
          <span className="inline-block">
            {text.split('').map((char, index) => (
              <motion.span
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{
                  duration: 0.3,
                  delay: index * 0.1,
                  ease: 'easeOut',
                }}
                className="inline-block"
              >
                {char}
              </motion.span>
            ))}
          </span>
        ) : (
          text
        )}
      </motion.div>

      {/* Watermark Overlay */}
      {showWatermark && (
        <div className="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
          <div
            className="text-gray-300 font-light text-4xl tracking-wider"
            style={{
              transform: 'rotate(-45deg)',
              opacity: 0.15,
              textShadow: '0 0 20px rgba(255,255,255,0.8)',
            }}
          >
            PREVIEW
          </div>
        </div>
      )}
    </div>
  );
}
