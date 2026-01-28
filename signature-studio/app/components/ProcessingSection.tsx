'use client';

import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import SignatureCanvas from './SignatureCanvas';
import { generateSignatureStyles } from '../lib/signatureStyles';

interface ProcessingSectionProps {
  name: string;
  onComplete: () => void;
}

export default function ProcessingSection({ name, onComplete }: ProcessingSectionProps) {
  const [showAnimation, setShowAnimation] = useState(false);
  const styles = generateSignatureStyles(name);

  useEffect(() => {
    // Start animation after a brief delay
    const animationTimer = setTimeout(() => {
      setShowAnimation(true);
    }, 500);

    // Complete processing after animation
    const completeTimer = setTimeout(() => {
      onComplete();
    }, 3500);

    return () => {
      clearTimeout(animationTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-8">
      <div className="w-full max-w-2xl mx-auto text-center space-y-12">
        {/* Processing Animation */}
        <div className="flex flex-col items-center gap-8">
          {/* Animated signature preview */}
          <div className="relative w-full h-32 flex items-center justify-center bg-gray-50 rounded-lg">
            {showAnimation && (
              <SignatureCanvas
                text={name}
                style={styles[0]}
                animated={true}
                showWatermark={false}
              />
            )}
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
    </div>
  );
}
