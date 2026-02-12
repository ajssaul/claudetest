// 띠 (Chinese Zodiac)
export const CHINESE_ZODIAC = [
  { animal: '쥐', emoji: '🐀', element: '水', trait: '지혜롭고 민첩함' },
  { animal: '소', emoji: '🐂', element: '土', trait: '성실하고 인내심 강함' },
  { animal: '호랑이', emoji: '🐅', element: '木', trait: '용감하고 자신감 있음' },
  { animal: '토끼', emoji: '🐇', element: '木', trait: '온화하고 예술적임' },
  { animal: '용', emoji: '🐉', element: '土', trait: '카리스마 있고 야망적임' },
  { animal: '뱀', emoji: '🐍', element: '火', trait: '지혜롭고 직관적임' },
  { animal: '말', emoji: '🐎', element: '火', trait: '활동적이고 자유로움' },
  { animal: '양', emoji: '🐏', element: '土', trait: '온순하고 창의적임' },
  { animal: '원숭이', emoji: '🐒', element: '金', trait: '영리하고 재치 있음' },
  { animal: '닭', emoji: '🐓', element: '金', trait: '근면하고 관찰력 있음' },
  { animal: '개', emoji: '🐕', element: '土', trait: '충성스럽고 정직함' },
  { animal: '돼지', emoji: '🐷', element: '水', trait: '관대하고 성실함' },
]

// 별자리 (Western Zodiac)
export const WESTERN_ZODIAC = [
  { sign: '염소자리', emoji: '♑', dates: '12/22-1/19', element: '흙', ruling: '토성', trait: '야망적이고 책임감 있음' },
  { sign: '물병자리', emoji: '♒', dates: '1/20-2/18', element: '공기', ruling: '천왕성', trait: '독창적이고 인도주의적' },
  { sign: '물고기자리', emoji: '♓', dates: '2/19-3/20', element: '물', ruling: '해왕성', trait: '직관적이고 감성적' },
  { sign: '양자리', emoji: '♈', dates: '3/21-4/19', element: '불', ruling: '화성', trait: '열정적이고 리더십 있음' },
  { sign: '황소자리', emoji: '♉', dates: '4/20-5/20', element: '흙', ruling: '금성', trait: '안정적이고 신뢰할 수 있음' },
  { sign: '쌍둥이자리', emoji: '♊', dates: '5/21-6/20', element: '공기', ruling: '수성', trait: '다재다능하고 소통을 잘함' },
  { sign: '게자리', emoji: '♋', dates: '6/21-7/22', element: '물', ruling: '달', trait: '보호적이고 가정적' },
  { sign: '사자자리', emoji: '♌', dates: '7/23-8/22', element: '불', ruling: '태양', trait: '당당하고 창의적' },
  { sign: '처녀자리', emoji: '♍', dates: '8/23-9/22', element: '흙', ruling: '수성', trait: '분석적이고 세심함' },
  { sign: '천칭자리', emoji: '♎', dates: '9/23-10/22', element: '공기', ruling: '금성', trait: '조화롭고 공정함' },
  { sign: '전갈자리', emoji: '♏', dates: '10/23-11/21', element: '물', ruling: '명왕성', trait: '강렬하고 통찰력 있음' },
  { sign: '사수자리', emoji: '♐', dates: '11/22-12/21', element: '불', ruling: '목성', trait: '낙천적이고 모험적' },
]

export function getChineseZodiac(year: number) {
  const index = (year - 4) % 12
  return CHINESE_ZODIAC[index]
}

export function getWesternZodiac(month: number, day: number) {
  const zodiacDates = [
    { month: 1, day: 20 },  // 물병자리 시작
    { month: 2, day: 19 },  // 물고기자리 시작
    { month: 3, day: 21 },  // 양자리 시작
    { month: 4, day: 20 },  // 황소자리 시작
    { month: 5, day: 21 },  // 쌍둥이자리 시작
    { month: 6, day: 21 },  // 게자리 시작
    { month: 7, day: 23 },  // 사자자리 시작
    { month: 8, day: 23 },  // 처녀자리 시작
    { month: 9, day: 23 },  // 천칭자리 시작
    { month: 10, day: 23 }, // 전갈자리 시작
    { month: 11, day: 22 }, // 사수자리 시작
    { month: 12, day: 22 }, // 염소자리 시작
  ]

  let index = 0
  for (let i = 0; i < zodiacDates.length; i++) {
    if (month === zodiacDates[i].month && day >= zodiacDates[i].day) {
      index = i + 1
    } else if (month > zodiacDates[i].month) {
      index = i + 1
    }
  }

  return WESTERN_ZODIAC[index % 12]
}

// 생명수 (Life Path Number)
export function getLifePathNumber(year: number, month: number, day: number): number {
  const sum = String(year) + String(month).padStart(2, '0') + String(day).padStart(2, '0')
  let result = sum.split('').reduce((acc, digit) => acc + parseInt(digit), 0)

  while (result > 9 && result !== 11 && result !== 22 && result !== 33) {
    result = String(result).split('').reduce((acc, digit) => acc + parseInt(digit), 0)
  }

  return result
}

export const LIFE_PATH_MEANINGS: Record<number, { title: string; description: string; strengths: string[]; challenges: string[] }> = {
  1: {
    title: '리더',
    description: '독립적이고 창의적인 개척자입니다. 새로운 길을 개척하고 다른 사람들을 이끄는 능력이 있습니다.',
    strengths: ['리더십', '독창성', '결단력', '야망'],
    challenges: ['고집', '자기중심적', '인내심 부족']
  },
  2: {
    title: '중재자',
    description: '협력적이고 조화를 추구합니다. 관계와 파트너십에서 빛을 발합니다.',
    strengths: ['외교력', '협력', '직관력', '배려심'],
    challenges: ['우유부단', '과민함', '의존성']
  },
  3: {
    title: '표현자',
    description: '창의적이고 표현력이 풍부합니다. 예술과 소통에 재능이 있습니다.',
    strengths: ['창의력', '낙관성', '소통능력', '영감'],
    challenges: ['산만함', '과장', '감정 기복']
  },
  4: {
    title: '건설자',
    description: '실용적이고 체계적입니다. 안정적인 기반을 만드는 데 탁월합니다.',
    strengths: ['근면함', '신뢰성', '조직력', '인내심'],
    challenges: ['완고함', '융통성 부족', '과로']
  },
  5: {
    title: '자유인',
    description: '모험적이고 변화를 추구합니다. 다양한 경험을 통해 성장합니다.',
    strengths: ['적응력', '다재다능', '호기심', '매력'],
    challenges: ['불안정', '충동성', '책임 회피']
  },
  6: {
    title: '양육자',
    description: '책임감 있고 보호적입니다. 가정과 공동체에 헌신합니다.',
    strengths: ['책임감', '사랑', '치유력', '봉사정신'],
    challenges: ['과잉보호', '간섭', '자기희생']
  },
  7: {
    title: '탐구자',
    description: '분석적이고 영적입니다. 깊은 진리를 추구합니다.',
    strengths: ['지성', '직관', '분석력', '내면의 지혜'],
    challenges: ['고립', '비판적', '의심']
  },
  8: {
    title: '성취자',
    description: '야망적이고 실질적입니다. 물질적 성공을 이루는 능력이 있습니다.',
    strengths: ['추진력', '사업 감각', '권위', '효율성'],
    challenges: ['물질주의', '지배적', '워커홀릭']
  },
  9: {
    title: '인도주의자',
    description: '이타적이고 자비롭습니다. 인류에 봉사하는 사명이 있습니다.',
    strengths: ['자비', '관대함', '창의력', '지혜'],
    challenges: ['이상주의', '감정적 거리', '순교자 기질']
  },
  11: {
    title: '영적 메신저',
    description: '직관적이고 영감을 주는 마스터 넘버입니다. 영적 통찰력이 있습니다.',
    strengths: ['영적 통찰', '영감', '이상주의', '카리스마'],
    challenges: ['긴장', '자기 의심', '비현실적']
  },
  22: {
    title: '마스터 빌더',
    description: '비전과 실행력을 겸비한 마스터 넘버입니다. 큰 꿈을 현실로 만듭니다.',
    strengths: ['비전', '실현력', '리더십', '실용성'],
    challenges: ['압박감', '완벽주의', '자기 과시']
  },
  33: {
    title: '마스터 티처',
    description: '사랑과 치유의 마스터 넘버입니다. 다른 이들을 고양시킵니다.',
    strengths: ['무조건적 사랑', '치유력', '봉사', '영적 성장'],
    challenges: ['과도한 책임', '순교 의식', '자기 소홀']
  },
}

// 오늘의 운세 생성
export function generateDailyFortune(lifePath: number, zodiacSign: string): string[] {
  const fortunes = [
    '오늘 예상치 못한 기회가 찾아올 것입니다. 열린 마음으로 받아들이세요.',
    '소중한 인연과의 대화에서 깊은 통찰을 얻게 됩니다.',
    '창의적인 에너지가 높아지는 날입니다. 새로운 프로젝트를 시작하기 좋습니다.',
    '재정적인 결정은 신중하게 하세요. 충동적인 지출은 삼가세요.',
    '건강에 신경 쓰는 것이 좋습니다. 충분한 휴식을 취하세요.',
    '오래된 관계가 새롭게 발전할 수 있습니다.',
    '직감을 믿으세요. 당신의 내면의 목소리가 정확합니다.',
    '작은 친절이 큰 행운으로 돌아올 것입니다.',
  ]

  // 생명수와 별자리를 기반으로 운세 선택
  const seed = lifePath + zodiacSign.length + new Date().getDate()
  const selectedFortunes: string[] = []

  for (let i = 0; i < 3; i++) {
    const index = (seed + i * 3) % fortunes.length
    selectedFortunes.push(fortunes[index])
  }

  return selectedFortunes
}

// 궁합 점수
export function getCompatibilityScore(lifePath: number): { love: number; career: number; health: number; wealth: number } {
  const base = (lifePath * 11 + new Date().getMonth()) % 30 + 70
  return {
    love: Math.min(99, base + (lifePath % 5)),
    career: Math.min(99, base + ((lifePath * 2) % 7)),
    health: Math.min(99, base + ((lifePath * 3) % 6)),
    wealth: Math.min(99, base + ((lifePath * 4) % 8)),
  }
}

// 럭키 정보
export function getLuckyInfo(lifePath: number, month: number) {
  const colors = ['빨강', '주황', '노랑', '초록', '파랑', '남색', '보라', '흰색', '검정', '금색']
  const numbers = [1, 3, 7, 8, 9, 11, 13, 17, 21, 27, 33]
  const directions = ['동', '서', '남', '북', '동남', '동북', '서남', '서북']

  return {
    color: colors[(lifePath + month) % colors.length],
    number: numbers[(lifePath * 2 + month) % numbers.length],
    direction: directions[(lifePath + month * 2) % directions.length],
  }
}
