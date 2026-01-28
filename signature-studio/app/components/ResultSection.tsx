'use client';

import { Download, Copy, CheckCircle } from 'lucide-react';
import { useState } from 'react';

interface ResultSectionProps {
  name: string;
}

export default function ResultSection({ name }: ResultSectionProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Simulated signature variations
  const signatures = [
    { id: 1, style: 'Classic', path: 'M 20 48 Q 40 20, 80 48 T 150 48 Q 180 60, 220 40' },
    { id: 2, style: 'Elegant', path: 'M 10 40 Q 60 10, 110 40 Q 160 70, 240 30' },
    { id: 3, style: 'Modern', path: 'M 30 50 L 90 50 Q 120 30, 150 50 L 220 50' },
    { id: 4, style: 'Artistic', path: 'M 20 60 Q 40 20, 80 60 Q 120 100, 160 60 Q 200 20, 230 60' },
    { id: 5, style: 'Minimal', path: 'M 40 48 L 120 48 Q 150 38, 180 48 L 220 48' },
    { id: 6, style: 'Bold', path: 'M 15 45 Q 50 15, 90 45 T 170 45 Q 210 60, 240 35' },
  ];

  const handleDownload = (id: number, style: string) => {
    console.log(`Downloading signature ${id}: ${style}`);
    // TODO: Implement actual download logic
  };

  const handleCopy = (id: number) => {
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 2000);
    console.log(`Copied signature ${id} to clipboard`);
    // TODO: Implement actual copy to clipboard logic
  };

  return (
    <div className="min-h-screen bg-white py-16 px-8">
      <div className="w-full max-w-6xl mx-auto space-y-16">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl md:text-6xl font-serif font-normal tracking-tight">
            Your signatures, {name}
          </h1>
          <p className="text-xl font-light text-gray-600 tracking-wide">
            Choose your favorite and download
          </p>
        </div>

        {/* Signatures Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {signatures.map((signature) => (
            <div
              key={signature.id}
              className="group relative bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* Signature Preview */}
              <div className="aspect-video bg-gray-50 flex items-center justify-center p-8">
                <svg
                  className="w-full h-full"
                  viewBox="0 0 256 96"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d={signature.path}
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="none"
                    className="text-gray-900"
                  />
                </svg>
              </div>

              {/* Info and Actions */}
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 tracking-wide">
                    {signature.style}
                  </span>
                  <span className="text-xs text-gray-500 font-light">
                    PNG • Transparent
                  </span>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDownload(signature.id, signature.style)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-normal"
                  >
                    <Download size={16} strokeWidth={1.5} />
                    Download
                  </button>
                  <button
                    onClick={() => handleCopy(signature.id)}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-normal"
                  >
                    {copiedIndex === signature.id ? (
                      <>
                        <CheckCircle size={16} strokeWidth={1.5} className="text-green-600" />
                        <span className="text-green-600">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy size={16} strokeWidth={1.5} />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className="text-center space-y-4 pt-8 border-t border-gray-200">
          <p className="text-gray-600 font-light">
            All signatures are licensed for commercial use
          </p>
          <button className="text-sm text-gray-500 hover:text-gray-900 transition-colors underline">
            Need more variations? Generate new set
          </button>
        </div>
      </div>
    </div>
  );
}
