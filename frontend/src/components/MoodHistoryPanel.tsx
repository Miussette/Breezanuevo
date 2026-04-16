import type { MoodEntry } from '../types'
import { BookOpen } from 'lucide-react'
import { AccordionCard } from './AccordionCard'

type MoodHistoryPanelProps = {
  moods: MoodEntry[]
}

function formatStamp(iso: string) {
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(new Date(iso))
}

export function MoodHistoryPanel({ moods }: MoodHistoryPanelProps) {
  return (
    <AccordionCard
      className="history-panel"
      icon={<BookOpen size={20} />}
      kicker="Historial Emocional"
      title="Notas recientes"
      pillNode={<span className="pill neutral">{moods.length}</span>}
      defaultExpanded={false}
    >
      {moods.length === 0 ? (
        <p className="muted">Todavía no hay registros en esta sesión.</p>
      ) : (
        <div className="history-list">
          {moods.map((entry) => (
            <article
              className="history-item"
              key={entry.id}
            >
              <div className="history-headline">
                <strong>{entry.mood}</strong>
                <span>{entry.intensity}/10</span>
              </div>
              <p>{entry.note || entry.capturedText}</p>
              <small>{formatStamp(entry.timestamp)}</small>
            </article>
          ))}
          <div className="card-footer" style={{ marginTop: '12px' }}>
             <span className="pill success-soft">✓ Sincronizado con diario</span>
          </div>
        </div>
      )}
    </AccordionCard>
  )
}
