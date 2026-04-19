export type AnalystRole = 'user' | 'assistant'

export type AnalystMessage = {
  id: string
  role: AnalystRole
  text: string
  sql?: string
  rows?: Array<Record<string, unknown>>
}

export type AnalystResponse = {
  answer: string
  sql?: string
  rows?: Array<Record<string, unknown>>
}
