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
    { name: 'Classic Elegance', family: '"Great Vibes", cursive' },
    { name: 'Modern Flow', family: '"Dancing Script", cursive' },
    { name: 'Artistic Brush', family: '"Alex Brush", cursive' },
    { name: 'Vintage Script', family: '"Pinyon Script", cursive' },
    { name: 'Bold Statement', family: '"Dancing Script", cursive' },
    { name: 'Minimalist Chic', family: '"Great Vibes", cursive' },
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
