// Every backend call, in one place. Errors arrive as {"error": {"code", "message"}}.

import type { ChatResponse, Chunk, Collection, DocumentInfo, Health, Turn, UploadResult } from '../types'

export class ApiError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.code = code
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, options)
  if (res.status === 204) return undefined as T
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(body.error?.code ?? 'http_error', body.error?.message ?? `${res.status} ${res.statusText}`)
  return body as T
}

const json = (method: string, data: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})

export const api = {
  health: () => request<Health>('/api/health'),

  listCollections: () => request<Collection[]>('/api/collections'),
  createCollection: (name: string, description = '') =>
    request<Collection>('/api/collections', json('POST', { name, description })),
  deleteCollection: (id: string) => request<void>(`/api/collections/${id}`, { method: 'DELETE' }),

  listDocuments: (collectionId: string) =>
    request<DocumentInfo[]>(`/api/documents?collection_id=${encodeURIComponent(collectionId)}`),
  uploadFiles: (collectionId: string, files: File[]) => {
    const form = new FormData()
    form.append('collection_id', collectionId)
    for (const file of files) form.append('files', file)
    return request<{ results: UploadResult[] }>('/api/documents', { method: 'POST', body: form })
  },
  uploadText: (collectionId: string, title: string, text: string) =>
    request<UploadResult>('/api/documents/text', json('POST', { collection_id: collectionId, title, text })),
  listChunks: (documentId: string) => request<Chunk[]>(`/api/documents/${documentId}/chunks`),
  deleteDocument: (documentId: string) => request<void>(`/api/documents/${documentId}`, { method: 'DELETE' }),

  chat: (question: string, history: Turn[], collectionId: string | null) =>
    request<ChatResponse>('/api/chat', json('POST', { question, history, collection_id: collectionId })),
}
