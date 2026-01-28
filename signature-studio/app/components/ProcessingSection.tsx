'use client';

import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

interface ProcessingSectionProps {
  name: string;
  onComplete: () => void;
}

export default function ProcessingSection({ name, onComplete }: ProcessingSectionProps) {
  useEffect(() => {
    // Simulate processing for 3 seconds
    const timer = setTimeout(() => {
      onComplete();
    }, 3000);

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-8">
      <div className="w-full max-w-2xl mx-auto text-center space-y-12">
        {/* Processing Animation */}
        <div className="flex flex-col items-center gap-8">
          {/* Animated signature line */}
          <div className="relative w-full h-32 flex items-center justify-center">
            <svg
              className="w-64 h-24"
              viewBox="0 0 256 96"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M 10 48 Q 40 20, 80 48 T 150 48 Q 180 60, 220 40"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                fill="none"
                className="text-gray-400"
                style={{
                  strokeDasharray: 300,
                  strokeDashoffset: 300,
                  animation: 'drawSignature 2s ease-in-out infinite',
                }}
              />
            </svg>
          </div>

          {/* Loading spinner */}
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" strokeWidth={1.5} />
        </div>

        {/* Status Text */}
        <div className="space-y-4">
          <h2 className="text-3xl md:text-4xl font-serif font-normal tracking-tight">
            Analyzing your character...
          </h2>
          <p className="text-lg font-light text-gray-500 tracking-wide">
            Creating personalized signatures for {name}
          </p>
        </div>
      </div>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes drawSignature {
          0% {
            stroke-dashoffset: 300;
            opacity: 0.3;
          }
          50% {
            stroke-dashoffset: 0;
            opacity: 1;
          }
          100% {
            stroke-dashoffset: -300;
            opacity: 0.3;
          }
        }
      `}</style>
    </div>
  );
}
