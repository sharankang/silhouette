import { useState, useRef, useEffect } from 'react'
import { MessageSquare, Sparkles, Shirt } from 'lucide-react'
import ChatInput from '../components/Chat/ChatInput'
import ChatMessage from '../components/Chat/ChatMessage'
import { EmptyState } from '../components/UI'
import api from '../services/api'

const SUGGESTIONS = [
  "I want something casual for a coffee date ☕",
  "Help me build a smart casual work look",
  "I'm feeling bold today — surprise me",
  "Something cozy and warm for a lazy day",
]

export default function ChatPage() {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('silhouette_chat')
      return saved ? JSON.parse(saved) : []
    } catch { return [] }
  })
  const [loading,  setLoading]  = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    const toSave = messages.filter(m => !m.loading)
    try { localStorage.setItem('silhouette_chat', JSON.stringify(toSave)) } catch {}
  }, [messages])

  const clearChat = () => {
    setMessages([])
    localStorage.removeItem('silhouette_chat')
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async ({ text, audio, image }) => {
    // Build user message for display
    const userMsg = {
      id:           Date.now(),
      role:         'user',
      text:         text || (audio ? null : null),
      hasAudio:     !!audio,
      imagePreview: image ? URL.createObjectURL(image) : null,
    }

    // Add placeholder loading message
    const loadingMsg = { id: Date.now() + 1, role: 'assistant', loading: true }
    setMessages(prev => [...prev, userMsg, loadingMsg])
    setLoading(true)

    try {
      const formData = new FormData()
      if (text)  formData.append('text', text)
      if (audio) formData.append('audio', audio, 'recording.webm')
      if (image) formData.append('image', image)

      const recentHistory = messages
        .filter(m => !m.loading && (m.role === 'user' || m.role === 'assistant') && m.text)
        .slice(-6)
        .map(m => ({ role: m.role, text: m.text }))
      if (recentHistory.length > 0) {
        formData.append('history', JSON.stringify(recentHistory))
      }

      const response = await api.sendMessage(formData)

      setMessages(prev => prev.map(m =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, text: response.message, outfit: response.outfit }
          : m
      ))
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, text: "Request timed out — Ollama can be slow on the first few runs. Try again and it should be faster now that the model is warmed up." }
          : m
      ))
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestion = (suggestion) => {
    sendMessage({ text: suggestion, audio: null, image: null })
  }

  const handleRateOutfit = async (outfitId, rating) => {
    try {
      await api.rateOutfit(outfitId, rating)
      setMessages(prev => prev.map(m =>
        m.outfit?.id === outfitId
          ? { ...m, outfit: { ...m.outfit, rating } }
          : m
      ))
    } catch {
      setMessages(prev => prev.map(m =>
        m.outfit?.id === outfitId
          ? { ...m, outfit: { ...m.outfit, rating } }
          : m
      ))
    }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="px-8 pt-8 pb-4 border-b border-ink-800/60 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-terracotta-600/20 border border-terracotta-500/30 flex items-center justify-center">
              <Sparkles size={16} className="text-terracotta-400" />
            </div>
            <div>
              <h2 className="font-display text-xl text-cream">Style Chat</h2>
              <p className="text-ink-400 text-xs font-mono">Multimodal · Text, voice, and inspiration images</p>
            </div>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-xs text-ink-500 hover:text-terracotta-400 transition-colors px-3 py-1.5 rounded-lg border border-ink-800 hover:border-terracotta-500/30"
            >
              Clear chat
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-8">
            {/* Intro */}
            <div className="text-center max-w-sm">
              <div className="w-16 h-16 rounded-2xl bg-terracotta-600/20 border border-terracotta-500/30 flex items-center justify-center mx-auto mb-4">
                <Sparkles size={28} className="text-terracotta-400" />
              </div>
              <h3 className="font-display text-2xl text-cream mb-2">What are we wearing today?</h3>
              <p className="text-dust text-sm leading-relaxed">
                Describe your mood, drop an inspo image, or record a voice note.
                Silhouette will build an outfit from your actual closet.
              </p>
            </div>

            {/* Suggestions */}
            <div className="grid grid-cols-2 gap-2 w-full max-w-lg">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => handleSuggestion(s)}
                  className="glass-light rounded-xl px-4 py-3 text-sm text-dust hover:text-cream text-left transition-all duration-200 hover:border-ink-600/60 hover:bg-ink-800/50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} onRateOutfit={handleRateOutfit} />
            ))}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-8 pb-8 pt-4 shrink-0">
        <ChatInput onSend={sendMessage} loading={loading} />
      </div>
    </div>
  )
}