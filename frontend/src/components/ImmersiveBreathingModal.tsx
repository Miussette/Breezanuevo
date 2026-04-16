import { useEffect } from 'react'
import type { BreathingAction } from '../types'
import { Wind, X } from 'lucide-react'

type ImmersiveBreathingModalProps = {
  active: boolean
  action?: BreathingAction
  onClose: () => void
}

export function ImmersiveBreathingModal({ active, action, onClose }: ImmersiveBreathingModalProps) {
  // Manejamos el bloqueo del scroll del body cuando el modal está activo
  useEffect(() => {
    if (active) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [active])

  if (!active || !action) return null

  return (
    <div className={`immersive-modal-overlay ${active ? 'visible' : ''}`}>
      <div className="immersive-modal-content glass-card">
        <button 
          className="icon-button close-modal" 
          onClick={onClose} 
          aria-label="Cerrar apoyo guiado"
        >
          <X size={28} />
        </button>
        
        <div className="modal-header">
           <span className="modal-hero-icon-wrapper"><Wind size={42} /></span>
           <h2 className="modal-title">Baja tu ritmo</h2>
           <p className="modal-guidance">{action.guidance}</p>
        </div>

        <div className="hero-breathing-wrapper">
          <div className="hero-breathing-circle animate">
            <span>{action.pattern}</span>
          </div>
        </div>

        <div className="modal-footer">
           <p className="modal-kicker">
             {action.cycles} ciclos sugeridos • Contrarrestando: {action.emotion}
           </p>
           <button className="primary-button modal-hero-button" onClick={onClose}>
              Me siento mejor
           </button>
        </div>
      </div>
    </div>
  )
}
