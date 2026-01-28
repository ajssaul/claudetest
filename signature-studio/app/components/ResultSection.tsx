'use client';

import { Download, Copy, CheckCircle } from 'lucide-react';
import { useState, useRef } from 'react';
import { toPng } from 'html-to-image';
import SignatureCanvas from './SignatureCanvas';
import { generateSignatureStyles } from '../lib/signatureStyles';

interface ResultSectionProps {
  name: string;
}

export default function ResultSection({ name }: ResultSectionProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [downloadingIndex, setDownloadingIndex] = useState<number | null>(null);
  const canvasRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});

  const styles = generateSignatureStyles(name);

  const handleDownload = async (id: number, styleName: string) => {
    const canvasElement = canvasRefs.current[id];
    if (!canvasElement) return;

    setDownloadingIndex(id);

    try {
      const dataUrl = await toPng(canvasElement, {
        quality: 1.0,
        pixelRatio: 3,
        backgroundColor: null,
      });

      const link = document.createElement('a');
      link.download = `signature-${styleName.toLowerCase().replace(/\s+/g, '-')}-${name.toLowerCase()}.png`;
      link.href = dataUrl;
      link.click();
    } catch (error) {
      console.error('Failed to download signature:', error);
    } finally {
      setDownloadingIndex(null);
    }
  };

  const handleCopy = async (id: number) => {
    const canvasElement = canvasRefs.current[id];
    if (!canvasElement) return;

    try {
      const dataUrl = await toPng(canvasElement, {
        quality: 1.0,
        pixelRatio: 2,
        backgroundColor: null,
      });

      const blob = await (await fetch(dataUrl)).blob();
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob }),
      ]);

      setCopiedIndex(id);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (error) {
      console.error('Failed to copy signature:', error);
    }
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
          {styles.map((style) => (
            <div
              key={style.id}
              className="group relative bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* Signature Preview */}
              <div className="aspect-video bg-gray-50 flex items-center justify-center">
                <div
                  ref={(el) => {
                    canvasRefs.current[style.id] = el;
                  }}
                  className="w-full h-full"
                >
                  <SignatureCanvas
                    text={name}
                    style={style}
                    showWatermark={false}
                    animated={false}
                  />
                </div>
              </div>

              {/* Info and Actions */}
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 tracking-wide">
                    {style.name}
                  </span>
                  <span className="text-xs text-gray-500 font-light">
                    PNG • Transparent
                  </span>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDownload(style.id, style.name)}
                    disabled={downloadingIndex === style.id}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-normal disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Download size={16} strokeWidth={1.5} />
                    {downloadingIndex === style.id ? 'Downloading...' : 'Download'}
                  </button>
                  <button
                    onClick={() => handleCopy(style.id)}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-normal"
                  >
                    {copiedIndex === style.id ? (
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
          <button
            onClick={() => window.location.reload()}
            className="text-sm text-gray-500 hover:text-gray-900 transition-colors underline"
          >
            Need more variations? Start over
          </button>
        </div>
      </div>
    </div>
  );
}
