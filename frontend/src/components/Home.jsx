import { useState, useEffect, useRef } from 'react'
import {
  getConversations,
  createConversation,
  getMessages,
  sendMessage,
  uploadDocument,
  getConversationDocuments,
  deleteConversation,
} from '../api'
import '../Home.css'

function Home({ onLogout }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [attachedDocs, setAttachedDocs] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [uploading, setUploading] = useState(false)
  const chatEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const userEmail = localStorage.getItem('userEmail') || 'user'
  const initials = userEmail.slice(0, 2).toUpperCase()

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (activeId) {
      loadMessages(activeId)
      loadDocs(activeId)
    } else {
      setMessages([])
      setAttachedDocs([])
    }
  }, [activeId])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadConversations = async () => {
    try {
      const data = await getConversations()
      setConversations(data.conversations || [])
    } catch (err) {
      console.log('failed to load conversations', err)
    }
  }

  const loadMessages = async (id) => {
    try {
      const data = await getMessages(id)
      const msgs = (data.messages || []).map((m, i) => ({
        ...m,
        role: i % 2 === 0 ? 'user' : 'assistant',
      }))
      setMessages(msgs)
    } catch (err) {
      console.log('failed to load messages', err)
    }
  }

  const loadDocs = async (id) => {
    try {
      const data = await getConversationDocuments(id)
      setAttachedDocs(data.documents || [])
    } catch (err) {
      console.log('failed to load docs', err)
    }
  }

  const handleNewChat = () => {
    setActiveId(null)
    setMessages([])
    setAttachedDocs([])
    setInput('')
  }

  const handleDeleteConversation = async (id, e) => {
    e.stopPropagation()

    try {
      await deleteConversation(id)
      setConversations((prev) => prev.filter((c) => c.id !== id))

      if (activeId === id) {
        handleNewChat()
      }
    } catch (err) {
      console.log('delete failed', err)
    }
  }

  const ensureConversation = async (title) => {
    if (activeId) return activeId

    const res = await createConversation(title)
    const convId = res.conversation.id
    setActiveId(convId)
    await loadConversations()
    return convId
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)

    try {
      let convId = activeId
      if (!convId) {
        const name = file.name.replace(/\.[^.]+$/, '')
        convId = await ensureConversation(name)
      }

      const res = await uploadDocument(file, convId)
      setAttachedDocs((prev) => [...prev, res.document])

      const statusMsg = res.indexing?.indexed
        ? `Uploaded "${res.document.file_name}" — ready for questions.`
        : `Uploaded "${res.document.file_name}" but indexing had issues.`

      setMessages((prev) => [
        ...prev,
        { content: statusMsg, role: 'assistant' },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { content: `Upload failed: ${err.message}`, role: 'assistant' },
      ])
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || sending) return

    setSending(true)
    setInput('')

    try {
      let convId = activeId

      if (!convId) {
        const title = text.length > 30 ? text.slice(0, 30) + '...' : text
        convId = await ensureConversation(title)
      }

      setMessages((prev) => [...prev, { content: text, role: 'user' }])

      const res = await sendMessage(convId, text)
      setMessages((prev) => [
        ...prev,
        { content: res.assistant_response, role: 'assistant' },
      ])
    } catch (err) {
      console.log('send failed', err)
      setMessages((prev) => [
        ...prev,
        { content: err.message || 'Failed to get a response. Try again.', role: 'assistant' },
      ])
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    onLogout()
  }

  const showGreeting = !activeId && messages.length === 0
  const hasRag = attachedDocs.length > 0

  return (
    <div className="home">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".pdf,.txt,.md,.csv"
        hidden
      />

      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-top">
          <button className="sidebar-btn" onClick={handleNewChat} title="New chat">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
          <button className="sidebar-btn" onClick={() => setSidebarOpen(!sidebarOpen)} title="Toggle sidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M9 3v18" />
            </svg>
          </button>
        </div>

        <div className="sidebar-recents">
          <p className="recents-label">Recents</p>
          <ul className="recents-list">
            {conversations.map((c) => (
              <li key={c.id} className="recents-row">
                <button
                  className={`recents-item ${activeId === c.id ? 'active' : ''}`}
                  onClick={() => setActiveId(c.id)}
                >
                  <span className="recents-title">{c.title}</span>
                  {activeId === c.id && <span className="active-dot" />}
                </button>
                <button
                  className="delete-conv-btn"
                  type="button"
                  title="Delete chat"
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="sidebar-user">
          <div className="user-avatar">{initials}</div>
          <span className="user-name">{userEmail.split('@')[0]}</span>
          <button className="sidebar-btn logout-btn" onClick={handleLogout} title="Logout">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="main-header">
          <div className="header-left">
            {!sidebarOpen && (
              <button className="sidebar-btn" onClick={() => setSidebarOpen(true)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <path d="M9 3v18" />
                </svg>
              </button>
            )}
            <span className="brand-name">nameless</span>
            {hasRag && <span className="rag-badge">RAG</span>}
            <svg className="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </div>
        </header>

        <div className="chat-body">
          {showGreeting ? (
            <div className="greeting">
              <h2>Ready when you are.</h2>
              <h4 className="greeting-hint">Attach a PDF or text file to ask questions about it</h4>
            </div>
          ) : (
            <div className="messages">
              {messages.map((msg, i) => (
                <div key={i} className={`msg ${msg.role || (i % 2 === 0 ? 'user' : 'assistant')}`}>
                  <div className="msg-bubble">{msg.content}</div>
                </div>
              ))}
              {sending && (
                <div className="msg assistant">
                  <div className="msg-bubble typing">Thinking...</div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {attachedDocs.length > 0 && (
          <div className="attached-files">
            {attachedDocs.map((doc) => (
              <span key={doc.id} className="file-chip">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <path d="M14 2v6h6" />
                </svg>
                {doc.file_name}
              </span>
            ))}
          </div>
        )}

        <div className="input-area">
          <div className="input-box">
            <button
              className="input-icon attach-btn"
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              title="Attach file"
            >
              {uploading ? (
                <span className="uploading-dot" />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                </svg>
              )}
            </button>
            <input
              type="text"
              placeholder={hasRag ? 'Ask about your file...' : 'Ask anything'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sending}
            />
            <button
              className="send-btn"
              type="button"
              onClick={handleSend}
              disabled={!input.trim() || sending}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 10.5L21 3l-6.75 16.5-2.25-7.5L3 10.5z" />
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Home
