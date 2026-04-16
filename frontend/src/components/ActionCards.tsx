import type { ActionDetails } from '../types'
import { Zap, Wind, Coffee, PenLine } from 'lucide-react'
import { AccordionCard } from './AccordionCard'

type ActionCardsProps = {
  actionDetails: ActionDetails
}

function formatTime(iso: string) {
  return new Intl.DateTimeFormat('es-CL', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(iso))
}

export function ActionCards({ actionDetails }: ActionCardsProps) {
  const hasActions = Boolean(
    actionDetails.break || actionDetails.mood
  )

  return (
    <section className="actions-grid">
      {!hasActions ? (
        <AccordionCard
          className="action-card action-empty-card"
          icon={<Zap size={20} />}
          kicker="Acciones"
          title="Breeza mostrará apoyo guiado aquí"
          defaultExpanded={false}
        >
          <p className="muted">
            Las pausas automáticas y el seguimiento del ánimo aparecerán aquí cuando el agente
            detecte señales emocionales.
          </p>
        </AccordionCard>
      ) : null}

      {actionDetails.break ? (
        <AccordionCard
          className="action-card break-card"
          icon={<Coffee size={20} />}
          kicker="Pausa"
          title="Toma un descanso consciente"
          pillNode={<span className="pill success">Programada</span>}
          defaultExpanded={true}
        >
          <p>
            Toma un <strong>descanso de {actionDetails.break.breakMinutes} minutos</strong> a las{' '}
            <strong>{formatTime(actionDetails.break.breakAt)}</strong>.
          </p>
          <p className="muted">{actionDetails.break.reason}</p>
        </AccordionCard>
      ) : null}

      {actionDetails.mood ? (
        <AccordionCard
          className="action-card mood-card"
          icon={<PenLine size={20} />}
          kicker="Registro"
          title="Registro Emocional"
          defaultExpanded={true}
        >
          <p>
            Hemos detectado <strong>{actionDetails.mood.entry.mood}</strong> con una intensidad de{' '}
            <strong>{actionDetails.mood.entry.intensity}/10</strong>.
          </p>
          <p className="muted">{actionDetails.mood.entry.note || 'Registro emocional automático.'}</p>
          
          <div className="card-footer">
            <span className="pill success-soft">✓ Guardado en historial</span>
          </div>
        </AccordionCard>
      ) : null}
    </section>
  )
}
