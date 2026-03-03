import { useState, useRef, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Send, Mic, MicOff, Image, X, Loader2 } from 'lucide-react'
import clsx from 'clsx'

export default function ChatInput({ onSend, loading }) {
  const [text,        setText]        = useState('')
  const [recording,   setRecording]   = useState(false)
  const [audioBlob,   setAudioBlob]   = useState(null)
  const [inspoImage,  setInspoImage]  = useState(null)  // { file, preview }
  const mediaRef = useRef(null)
  const chunksRef = useRef([])

  /* Image drop */
  const onDrop = useCallback(accepted => {
    if (!accepted[0]) return
    setInspoImage({ file: accepted[0], preview: URL.createObjectURL(accepted[0]) })
  }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/*': [] }, maxFiles: 1, noClick: true,
  })

  const pickImage = () => document.getElementById('chat-image-input').click()

  /* Audio recording */
  const startRecording = async () => {
    chunksRef.current = []
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mr = new MediaRecorder(stream)
    mr.ondataavailable = e => chunksRef.current.push(e.data)
    mr.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
      setAudioBlob(blob)
      stream.getTracks().forEach(t => t.stop())
    }
    mr.start()
    mediaRef.current = mr
    setRecording(true)
  }

  const stopRecording = () => {
    mediaRef.current?.stop()
    setRecording(false)
  }

  /* Send */
  const handleSend = () => {
    if (!text.trim() && !audioBlob && !inspoImage) return
    onSend({ text: text.trim(), audio: audioBlob, image: inspoImage?.file })
    setText('')
    setAudioBlob(null)
    setInspoImage(null)
  }

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const canSend = (text.trim() || audioBlob || inspoImage) && !loading

  return (
    <div {...getRootProps()} className={clsx(
      'relative transition-all duration-200',
      isDragActive && 'scale-[1.01]'
    )}>
      {isDragActive && (
        <div className="absolute inset-0 rounded-2xl border-2 border-dashed border-terracotta-400/60 bg-terracotta-600/5 z-10 flex items-center justify-center pointer-events-none">
          <p className="text-terracotta-400 text-sm font-body">Drop inspo image here</p>
        </div>
      )}

      <div className="glass rounded-2xl p-3 shadow-lg shadow-ink-950/30">
        {/* Inspo image preview */}
        {inspoImage && (
          <div className="relative w-16 h-20 mb-2 ml-1">
            <img src={inspoImage.preview} alt="inspo" className="w-full h-full object-cover rounded-lg border border-ink-700" />
            <button
              onClick={() => setInspoImage(null)}
              className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-ink-900 border border-ink-600 rounded-full flex items-center justify-center hover:bg-ink-700"
            >
              <X size={10} className="text-dust" />
            </button>
            <div className="absolute bottom-0 left-0 right-0 bg-ink-950/70 rounded-b-lg px-1 py-0.5">
              <p className="text-[9px] text-ink-400 font-mono text-center">inspo</p>
            </div>
          </div>
        )}

        {/* Audio indicator */}
        {audioBlob && !recording && (
          <div className="flex items-center gap-2 mb-2 px-2 py-1.5 bg-ink-800 rounded-lg">
            <div className="flex gap-0.5 items-end h-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="w-0.5 bg-terracotta-400 rounded-full animate-pulse-soft"
                  style={{ height: `${30 + Math.sin(i * 0.8) * 40}%`, animationDelay: `${i * 0.1}s` }} />
              ))}
            </div>
            <span className="text-xs text-dust font-mono">Voice recorded</span>
            <button onClick={() => setAudioBlob(null)} className="ml-auto">
              <X size={12} className="text-ink-500 hover:text-dust" />
            </button>
          </div>
        )}

        {/* Text row */}
        <div className="flex items-end gap-2">
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKey}
            placeholder={
              inspoImage
                ? "Tell me the vibe you're going for..."
                : recording
                ? "Recording... click stop when done"
                : "Describe your mood, occasion, or style today..."
            }
            rows={1}
            disabled={recording}
            className={clsx(
              'flex-1 bg-transparent text-cream placeholder:text-ink-500 text-sm font-body resize-none',
              'focus:outline-none max-h-32 overflow-y-auto leading-relaxed',
              recording && 'opacity-50'
            )}
            style={{ minHeight: '24px' }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = e.target.scrollHeight + 'px'
            }}
          />

          <div className="flex items-center gap-1.5 shrink-0 pb-0.5">
            {/* Image button */}
            <input
              id="chat-image-input"
              type="file"
              accept="image/*"
              className="hidden"
              onChange={e => {
                const f = e.target.files[0]
                if (f) setInspoImage({ file: f, preview: URL.createObjectURL(f) })
              }}
            />
            <button
              onClick={pickImage}
              className={clsx(
                'w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200',
                inspoImage
                  ? 'bg-terracotta-600/30 text-terracotta-400'
                  : 'text-ink-500 hover:text-dust hover:bg-ink-800'
              )}
              title="Add inspiration image"
            >
              <Image size={16} />
            </button>

            {/* Mic button */}
            <button
              onClick={recording ? stopRecording : startRecording}
              className={clsx(
                'w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200',
                recording
                  ? 'bg-terracotta-500 text-white animate-pulse-soft'
                  : audioBlob
                  ? 'bg-terracotta-600/30 text-terracotta-400'
                  : 'text-ink-500 hover:text-dust hover:bg-ink-800'
              )}
              title={recording ? 'Stop recording' : 'Voice input'}
            >
              {recording ? <MicOff size={16} /> : <Mic size={16} />}
            </button>

            {/* Send */}
            <button
              onClick={handleSend}
              disabled={!canSend}
              className={clsx(
                'w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200',
                canSend
                  ? 'bg-terracotta-500 text-white hover:bg-terracotta-400 hover:scale-105'
                  : 'bg-ink-800 text-ink-600 cursor-not-allowed'
              )}
            >
              {loading
                ? <Loader2 size={15} className="animate-spin" />
                : <Send size={15} />
              }
            </button>
          </div>
        </div>
      </div>

      {/* Drag hint */}
      <p className="text-center text-ink-600 text-[10px] font-mono mt-2">
        Drop an inspo image anywhere · Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
