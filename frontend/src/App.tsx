import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Sparkles, Settings, X, Menu } from 'lucide-react'

import { ActionCards } from './components/ActionCards'
import { ChatMessage } from './components/ChatMessage'
import { Header } from './components/Header'
import { MoodHistoryPanel } from './components/MoodHistoryPanel'
import { AccordionCard } from './components/AccordionCard'
import { ImmersiveBreathingModal } from './components/ImmersiveBreathingModal'
import { useAmbientSound } from './hooks/useAmbientSound'
import { useSpeechRecognition } from './hooks/useSpeechRecognition'
import type { ActionDetails, ChatMessage as ChatMessageType, ChatResponse, MoodEntry } from './types'

const apiUrl = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? window.location.origin : 'http://localhost:8787')

function sanitizeForSpeech(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/[ \t]+/g, ' ')
    .trim()
}

const initialMessages: ChatMessageType[] = [
  {
    id: crypto.randomUUID(),
    role: 'agent',
    content: 'Estoy aquí para escucharte. Cuéntame cómo te sientes y activaré el apoyo que necesites basándome en tus emociones.'
  }
]

export default function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>(initialMessages)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionDetails, setActionDetails] = useState<ActionDetails>({})
  const [moodHistory, setMoodHistory] = useState<MoodEntry[]>([])
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [breathingDismissed, setBreathingDismissed] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const workspaceRef = useRef<HTMLDivElement | null>(null)
  const chatContainerRef = useRef<HTMLDivElement | null>(null)

  const breathingActive = Boolean(actionDetails.breathing) && !breathingDismissed
  const { unlockAudio } = useAmbientSound(breathingActive)

  const handleTranscript = useCallback((transcript: string) => {
    setInput((current) => [current, transcript].filter(Boolean).join(' ').trim())
  }, [])

  const { isListening, isSupported, startListening, stopListening } = useSpeechRecognition({
    onTranscript: handleTranscript
  })

  const latestActions = useMemo(
    () =>
      Object.entries(actionDetails)
        .filter(([, value]) => Boolean(value))
        .map(([key]) => key),
    [actionDetails]
  )

  useEffect(() => {
    if (!voiceEnabled) {
      window.speechSynthesis.cancel()
    }
  }, [voiceEnabled])

  const speak = (text: string) => {
    if (!voiceEnabled || !('speechSynthesis' in window)) {
      return
    }

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(sanitizeForSpeech(text))
    utterance.lang = 'es-ES'
    utterance.rate = 0.95
    utterance.pitch = 1
    window.speechSynthesis.speak(utterance)
  }
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])
  const sendMessage = async (message: string) => {
    const trimmedMessage = message.trim()

    if (!trimmedMessage) {
      return
    }

    setIsLoading(true)
    setError(null)
    await unlockAudio()

    const userMessage: ChatMessageType = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmedMessage
    }

    setMessages((current) => [...current, userMessage])
    setInput('')

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: trimmedMessage })
      })

      const payload = (await response.json()) as ChatResponse | { error?: string; message?: string }

      if (!response.ok || !('response' in payload)) {
        const failure = payload as { error?: string; message?: string }
        throw new Error(failure.message ?? failure.error ?? 'Could not reach Breeza')
      }

      const agentMessage: ChatMessageType = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: payload.response,
        actions: payload.actions
      }

      setMessages((current) => [...current, agentMessage])
      setActionDetails(payload.actionDetails)
      setMoodHistory(payload.moodHistory)
      setBreathingDismissed(false)
      speak(payload.response)
    } catch (caughtError) {
      const messageText =
        caughtError instanceof Error ? caughtError.message : 'Ocurrió un error inesperado'
      setError(messageText)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await sendMessage(input)
  }

  const handleMicClick = async () => {
    await unlockAudio()

    if (isListening) {
      stopListening()
      return
    }

    startListening()
  }

  const scrollToWorkspace = () => {
    workspaceRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  }

  return (
    <div className={`app-layout ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      <aside className="global-sidebar">
        <div className="sidebar-header">
           <span className="sidebar-logo-icon"><Sparkles size={24} /></span>
           <img src="/src/assets/logo.png" alt="Breeza AI" className="sidebar-logo" style={{height: 24, filter: 'brightness(0) invert(1)'}} />
           <button className="icon-button close-sidebar" onClick={() => setIsSidebarOpen(!isSidebarOpen)} aria-label="Toggle">
             {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
           </button>
        </div>
        <div className="sidebar-content">
          <ActionCards actionDetails={actionDetails} />

          <MoodHistoryPanel moods={moodHistory} />

          <AccordionCard
            className="helper-card"
            icon={<Settings size={20} />}
            kicker="Estado de sesión"
            title="Señales en vivo"
            defaultExpanded={false}
          >
            <p className="muted">
              Voz: {voiceEnabled ? 'activada' : 'silenciada'} • Micrófono:{' '}
              {isSupported ? (isListening ? 'escuchando' : 'listo') : 'no soportado'}
            </p>
            <p className="muted">
              Últimas acciones: {latestActions.length > 0 ? latestActions.join(', ') : 'ninguna aún'}
            </p>
          </AccordionCard>
        </div>
      </aside>

      <main className="main-content">
        <div className="layout">
          <Header
            voiceEnabled={voiceEnabled}
            isListening={isListening}
            onStart={scrollToWorkspace}
            onToggleVoice={() => setVoiceEnabled((current) => !current)}
          />

          <section
            className="workspace-section"
            ref={workspaceRef}
          >
            <div className="workspace-heading">
              <div>
                <span className="eyebrow">Soporte en vivo</span>
                <h2>Habla con Breeza y deja que actúe por ti</h2>
              </div>
              <span className="pill neutral">
                {latestActions.length > 0 ? latestActions.join(', ') : 'esperando acciones'}
              </span>
            </div>

            <div className="workspace-grid">
              <section className="glass-card chat-panel">
                <div className="panel-header">
                  <div>
                    <span className="card-kicker">Conversación</span>
                    <h3>Tu canal de apoyo emocional</h3>
                  </div>
                  <span className="pill neutral">{messages.length} mensajes</span>
                </div>

                <div 
                  className="messages-list"
                  ref={chatContainerRef}
                >
                  {messages.map((message) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                    />
                  ))}

                  {isLoading ? <div className="thinking-state">Breeza está pensando...</div> : null}
                </div>

                <form
                  className="composer"
                  onSubmit={handleSubmit}
                >
                  <input
                    aria-label="Dile a Breeza cómo te sientes"
                    className="composer-input"
                    onChange={(event) => setInput(event.target.value)}
                    placeholder="Escribe o dicta cómo te sientes..."
                    value={input}
                  />

                  <button
                    className={`icon-button ${isListening ? 'active' : ''}`}
                    disabled={!isSupported}
                    onClick={handleMicClick}
                    type="button"
                  >
                    {isListening ? 'Escuchando...' : 'Micro'}
                  </button>

                  <button
                    className="primary-button"
                    disabled={isLoading}
                    type="submit"
                  >
                    Enviar
                  </button>
                </form>

                {error ? <p className="error-banner">{error}</p> : null}
              </section>
            </div>
          </section>
        </div>
      </main>

      <ImmersiveBreathingModal 
        active={breathingActive} 
        action={actionDetails.breathing} 
        onClose={() => setBreathingDismissed(true)} 
      />
    </div>
  )
}
