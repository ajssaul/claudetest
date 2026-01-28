export interface SignatureStyle {
  id: number;
  name: string;
  fontFamily: string;
  fontSize: number;
  rotation: number;
  letterSpacing: number;
  strokeWidth: number;
  color: string;
}

export function generateSignatureStyles(name: string): SignatureStyle[] {
  const fonts = [
    { name: 'Classic Elegance', family: 'var(--font-great-vibes)' },
    { name: 'Modern Flow', family: 'var(--font-dancing-script)' },
    { name: 'Artistic Brush', family: 'var(--font-alex-brush)' },
    { name: 'Vintage Script', family: 'var(--font-pinyon-script)' },
    { name: 'Bold Statement', family: 'var(--font-dancing-script)' },
    { name: 'Minimalist Chic', family: 'var(--font-great-vibes)' },
  ];

  return fonts.map((font, index) => {
    // Random variations for each signature
    const baseRotation = [-3, -2, -1, 0, 1, 2];
    const baseFontSize = [48, 52, 56, 60, 64, 68];
    const baseLetterSpacing = [0, 0.02, 0.04, 0.06, 0.08, 0.1];
    const baseStrokeWidth = [0, 0.5, 1, 1.5, 0, 0.5];

    return {
      id: index + 1,
      name: font.name,
      fontFamily: font.family,
      fontSize: baseFontSize[index],
      rotation: baseRotation[index],
      letterSpacing: baseLetterSpacing[index],
      strokeWidth: baseStrokeWidth[index],
      color: '#000000',
    };
  });
}
