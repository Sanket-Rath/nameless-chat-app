const BASE = import.meta.env.VITE_API_URL || '/api'

function getToken() {
  return localStorage.getItem('token')
}

async function request(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }

  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE}${url}`, { ...options, headers })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    let msg = 'Something went wrong'
    if (typeof err.detail === 'string') msg = err.detail
    throw new Error(msg)
  }

  return res.json()
}

export function register(username, email, password) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  })
}

export function login(email, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getConversations() {
  return request('/conversations')
}

export function createConversation(title) {
  return request('/conversations', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

export function getMessages(conversationId) {
  return request(`/conversations/${conversationId}/messages`)
}

export function sendMessage(conversationId, message) {
  return request(`/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export function deleteConversation(id) {
  return request(`/conversations/${id}`, { method: 'DELETE' })
}

export function uploadDocument(file, conversationId) {
  const formData = new FormData()
  formData.append('file', file)
  if (conversationId) {
    formData.append('conversation_id', conversationId)
  }

  const token = getToken()
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  return fetch(`${BASE}/documents/upload`, {
    method: 'POST',
    headers,
    body: formData,
  }).then(async (res) => {
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Upload failed')
    }
    return res.json()
  })
}

export function getConversationDocuments(conversationId) {
  return request(`/conversations/${conversationId}/documents`)
}
