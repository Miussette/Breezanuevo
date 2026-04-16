import logo from '../assets/logo.png'

type HeaderProps = {
  voiceEnabled: boolean
  isListening: boolean
  onStart: () => void
  onToggleVoice: () => void
}



export function Header({ voiceEnabled, isListening, onStart, onToggleVoice }: HeaderProps) {
  return (
    <>
      <header className="top-nav">
        <div className="top-nav-brand">
          <img
            src={logo}
            alt="Breeza AI"
            className="top-nav-logo"
          />
        </div>
        <div className="top-nav-status">
          <span className="status-pill">Voz {voiceEnabled ? 'activa' : 'silenciada'}</span>
          <span className="status-pill">{isListening ? 'Micrófono escuchando' : 'Micrófono listo'}</span>
        </div>
      </header>

      <section className="hero-section">
        <div className="hero-content">
          <h1>Tu amigo personal de IA para el bienestar mental.</h1>
          <p className="hero-subtitle">
            Breeza te ayuda a relajarte, cuidarte y responde en el
            momento con apoyo de respiración, pausas conscientes y seguimiento de ánimo.
          </p>

          <div className="hero-actions">
            <button
              className="primary-button hero-cta"
              type="button"
              onClick={onStart}
            >
              Comenzar Ahora
            </button>

            <button
              className="ghost-button"
              type="button"
              onClick={onToggleVoice}
            >
              {voiceEnabled ? 'Silenciar voz' : 'Activar voz'}
            </button>
          </div>
        </div>
      </section>
    </>
  )
}
