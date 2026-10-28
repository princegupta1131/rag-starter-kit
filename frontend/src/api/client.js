// Every call the UI makes to the backend, in one place.
// Paths match backend/app/ingestion_service/api.py and retrieval_service/api.py.

async function request(path, options = {}) {
  const res = await fetch(path, options)
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(body.detail || `${res.status} ${res.statusText}`)
  return body
}

const json = (method, data) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})

export const api = {
  health: () => request('/api/health'),

  // ingestion_service
  listDocuments: () => request('/api/documents'),
  uploadFiles: (files) => {
    const form = new FormData()
    for (const file of files) form.append('files', file)
    return request('/api/documents', { method: 'POST', body: form })
  },
  uploadText: (title, text) => request('/api/documents/text', json('POST', { title, text })),
  listChunks: (id) => request(`/api/documents/${id}/chunks`),
  deleteDocument: (id) => request(`/api/documents/${id}`, { method: 'DELETE' }),

  // retrieval_service
  chat: (question, history) => request('/api/chat', json('POST', { question, history })),
}
