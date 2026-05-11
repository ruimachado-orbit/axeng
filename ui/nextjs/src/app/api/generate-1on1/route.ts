import { NextRequest, NextResponse } from 'next/server'

const API_BASE = process.env.AXENG_API_BASE || 'http://localhost:3457'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { person } = body

    if (!person) {
      return NextResponse.json(
        { ok: false, error: 'Person name is required' },
        { status: 400 }
      )
    }

    const response = await fetch(`${API_BASE}/api/generate-1on1?person=${encodeURIComponent(person)}`, {
      method: 'POST',
    })

    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { ok: false, error: String(error) },
      { status: 500 }
    )
  }
}
