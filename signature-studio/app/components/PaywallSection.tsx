'use client';

import { Check, Lock } from 'lucide-react';
import SignatureCanvas from './SignatureCanvas';
import { generateSignatureStyles } from '../lib/signatureStyles';

interface PaywallSectionProps {
  name: string;
  onPaymentComplete: () => void;
}

export default function PaywallSection({ name, onPaymentComplete }: PaywallSectionProps) {
  const features = [
    '6 unique handcrafted styles',
    'High-resolution transparent PNG',
    'Commercial license included',
    'Instant download',
  ];

  const styles = generateSignatureStyles(name);

  const handlePayment = () => {
    // Simulate payment processing
    setTimeout(() => {
      onPaymentComplete();
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col py-16 px-8">
      <div className="w-full max-w-4xl mx-auto space-y-16">
        {/* Headline */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl md:text-6xl font-serif font-normal tracking-tight">
            Your unique signatures are ready.
          </h1>
          <p className="text-xl font-light text-gray-600 tracking-wide">
            Unlock your personalized collection
          </p>
        </div>

        {/* Signature Preview Grid with Watermark */}
        <div className="relative">
          <div className="grid grid-cols-2 gap-6">
            {styles.slice(0, 4).map((style) => (
              <div
                key={style.id}
                className="aspect-video bg-gray-50 rounded-lg border border-gray-200 overflow-hidden"
              >
                <SignatureCanvas
                  text={name}
                  style={style}
                  showWatermark={true}
                  animated={false}
                />
              </div>
            ))}
          </div>

          {/* Lock Icon Overlay */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="bg-white rounded-full p-6 shadow-xl">
              <Lock size={40} strokeWidth={1.5} className="text-gray-800" />
            </div>
          </div>
        </div>

        {/* Features List */}
        <div className="bg-gray-50 rounded-2xl p-8 md:p-12">
          <h3 className="text-2xl font-serif font-normal mb-8 text-center">
            What you'll get
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {features.map((feature, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-black rounded-full flex items-center justify-center">
                  <Check size={14} className="text-white" strokeWidth={2.5} />
                </div>
                <span className="text-lg font-light tracking-wide">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Payment Button */}
        <div className="text-center space-y-4">
          <button
            onClick={handlePayment}
            className="group mx-auto flex items-center gap-3 px-12 py-5 bg-black text-white rounded-full hover:bg-gray-800 transition-all text-lg font-normal tracking-wide"
          >
            Get My Signatures Now
            <span className="ml-2">$19</span>
          </button>
          <p className="text-sm text-gray-500 font-light">
            One-time payment • Instant access • Money-back guarantee
          </p>
        </div>
      </div>
    </div>
  );
}
