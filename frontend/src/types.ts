// Shapes returned by the backend. Keep in sync with backend/app/*/schemas.py.

export interface TraceStep {
  step: string
  detail: string
  ms: number
  ok: boolean
}

export interface Health {
  database: string
  provider: string
  api_key: 'set' | 'missing'
  chat_model: string
  embed_model: string
  ready_documents: number
  stale_documents: number
  chunks: number
}

export interface Collection {
  id: string
  name: string
  description: string
  document_count: number
  ready_count: number
  created_at: string
}

export type DocumentStatus = 'queued' | 'processing' | 'ready' | 'failed'

export interface DocumentInfo {
  id: string
  collection_id: string
  filename: string
  status: DocumentStatus
  error: string | null
  num_chunks: number
  embed_model: string
  stale: boolean
  steps: TraceStep[]
  created_at: string
}

export interface Chunk {
  index: number
  page: number | null
  text: string
}

export interface UploadResult {
  filename: string
  status: 'queued' | 'duplicate' | 'rejected'
  id: string | null
  reason: string | null
}

export type ChatStatus = 'answered' | 'cached' | 'not_found' | 'unverified' | 'blocked'

export interface Source {
  n: number
  document_id: string
  filename: string
  page: number | null
  snippet: string
  similarity: number
}

export interface ChatResponse {
  answer: string
  status: ChatStatus
  sources: Source[]
  search_query: string | null
  trace: TraceStep[]
}

export interface Turn {
  role: 'user' | 'assistant'
  content: string
}
