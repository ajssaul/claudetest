import { NextRequest, NextResponse } from 'next/server'

// 캐시 저장소 (메모리 캐시 - 서버 재시작 시 초기화)
const cache: Map<string, { data: HoroscopeData; timestamp: number }> = new Map()
const CACHE_DURATION = 1000 * 60 * 60 // 1시간

interface HoroscopeData {
  sign: string
  horoscope: string
  date: string
}

// 영어 별자리 이름
const ZODIAC_SIGNS = [
  'capricorn', 'aquarius', 'pisces', 'aries', 'taurus', 'gemini',
  'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius'
]

// 한국어 운세 메시지 템플릿 (API 실패 시 또는 번역용)
const KOREAN_FORTUNES: Record<string, string[]> = {
  love: [
    '오늘은 사랑하는 사람과 깊은 대화를 나눌 좋은 시간입니다.',
    '새로운 인연이 예상치 못한 곳에서 찾아올 수 있습니다.',
    '파트너와의 관계에서 작은 오해가 생길 수 있으니 소통에 신경 쓰세요.',
    '혼자만의 시간이 필요할 수 있습니다. 자신을 돌보는 것도 사랑입니다.',
    '로맨틱한 순간이 찾아올 것입니다. 마음을 열어두세요.',
  ],
  career: [
    '업무에서 새로운 기회가 열릴 수 있습니다. 적극적으로 도전하세요.',
    '동료와의 협력이 좋은 결과를 가져올 것입니다.',
    '중요한 결정은 오후로 미루는 것이 좋겠습니다.',
    '창의적인 아이디어가 인정받을 수 있는 날입니다.',
    '꾸준한 노력이 곧 보상으로 돌아올 것입니다.',
  ],
  health: [
    '충분한 휴식이 필요한 날입니다. 무리하지 마세요.',
    '가벼운 운동이 기분 전환에 도움이 될 것입니다.',
    '수분 섭취에 신경 쓰세요.',
    '스트레스 관리가 중요한 시기입니다. 명상을 추천합니다.',
    '에너지가 넘치는 날입니다. 활동적인 일을 계획해보세요.',
  ],
  general: [
    '긍정적인 에너지가 당신을 감싸고 있습니다.',
    '예상치 못한 행운이 찾아올 수 있습니다.',
    '주변 사람들에게 감사를 표현해보세요.',
    '새로운 시작을 위한 좋은 날입니다.',
    '직감을 믿으세요. 당신의 내면이 정답을 알고 있습니다.',
    '작은 변화가 큰 행복을 가져올 수 있습니다.',
    '오늘 만나는 사람에게서 중요한 영감을 얻을 수 있습니다.',
    '재정적인 결정은 신중하게 하세요.',
  ]
}

// 날짜와 별자리 기반으로 일관된 운세 선택
function getSeededFortune(sign: string, category: string, date: string): string {
  const fortunes = KOREAN_FORTUNES[category] || KOREAN_FORTUNES.general
  const seed = sign.length + date.split('-').reduce((a, b) => a + parseInt(b), 0)
  const index = (seed + category.length) % fortunes.length
  return fortunes[index]
}

// 모든 별자리의 오늘 운세 가져오기
async function fetchAllHoroscopes(): Promise<Record<string, HoroscopeData>> {
  const today = new Date().toISOString().split('T')[0]
  const results: Record<string, HoroscopeData> = {}

  // API Ninjas 사용 (무료, API 키 필요 없음 - 제한적)
  // 대안: aztro API 또는 자체 생성

  for (const sign of ZODIAC_SIGNS) {
    const cacheKey = `${sign}-${today}`
    const cached = cache.get(cacheKey)

    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      results[sign] = cached.data
      continue
    }

    try {
      // Aztro API (무료, POST 요청)
      const response = await fetch(`https://aztro.sameerkumar.website/?sign=${sign}&day=today`, {
        method: 'POST',
      })

      if (response.ok) {
        const data = await response.json()
        const horoscopeData: HoroscopeData = {
          sign,
          horoscope: data.description || '',
          date: today,
        }

        cache.set(cacheKey, { data: horoscopeData, timestamp: Date.now() })
        results[sign] = horoscopeData
      } else {
        throw new Error('API failed')
      }
    } catch {
      // API 실패 시 자체 생성 운세 사용
      results[sign] = {
        sign,
        horoscope: getSeededFortune(sign, 'general', today),
        date: today,
      }
    }

    // Rate limiting 방지
    await new Promise(resolve => setTimeout(resolve, 100))
  }

  return results
}

// 단일 별자리 운세 가져오기
async function fetchHoroscope(sign: string): Promise<HoroscopeData> {
  const today = new Date().toISOString().split('T')[0]
  const cacheKey = `${sign}-${today}`
  const cached = cache.get(cacheKey)

  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data
  }

  try {
    const response = await fetch(`https://aztro.sameerkumar.website/?sign=${sign}&day=today`, {
      method: 'POST',
    })

    if (response.ok) {
      const data = await response.json()
      const horoscopeData: HoroscopeData = {
        sign,
        horoscope: data.description || '',
        date: today,
      }

      cache.set(cacheKey, { data: horoscopeData, timestamp: Date.now() })
      return horoscopeData
    }
  } catch {
    // 실패 시 자체 생성
  }

  return {
    sign,
    horoscope: getSeededFortune(sign, 'general', today),
    date: today,
  }
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const sign = searchParams.get('sign')?.toLowerCase()
  const all = searchParams.get('all')

  try {
    if (all === 'true') {
      const horoscopes = await fetchAllHoroscopes()
      return NextResponse.json({ success: true, data: horoscopes })
    }

    if (sign && ZODIAC_SIGNS.includes(sign)) {
      const horoscope = await fetchHoroscope(sign)
      return NextResponse.json({ success: true, data: horoscope })
    }

    return NextResponse.json(
      { success: false, error: 'Invalid sign parameter' },
      { status: 400 }
    )
  } catch {
    return NextResponse.json(
      { success: false, error: 'Failed to fetch horoscope' },
      { status: 500 }
    )
  }
}

// 한국어 운세 생성 API
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { sign, birthYear, birthMonth, birthDay } = body
    const today = new Date().toISOString().split('T')[0]

    // 종합 운세 생성
    const fortune = {
      date: today,
      sign,
      general: getSeededFortune(sign, 'general', today),
      love: getSeededFortune(sign, 'love', today),
      career: getSeededFortune(sign, 'career', today),
      health: getSeededFortune(sign, 'health', today),
      // 생년월일 기반 추가 정보
      luckyTime: `${(birthDay % 12) + 6}시 ~ ${(birthDay % 12) + 8}시`,
      luckyItem: ['빨간 펜', '은반지', '작은 거울', '녹색 수첩', '동전 지갑'][(birthMonth + birthDay) % 5],
      warning: ['과식', '지각', '충동구매', '과로', '감정적 대응'][(birthYear + birthMonth) % 5] + '을 주의하세요',
    }

    return NextResponse.json({ success: true, data: fortune })
  } catch {
    return NextResponse.json(
      { success: false, error: 'Invalid request' },
      { status: 400 }
    )
  }
}
