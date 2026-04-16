import { ReactNode, useState, useEffect } from 'react'

type AccordionCardProps = {
  className?: string
  icon: ReactNode
  kicker: string
  title: string
  pillNode?: ReactNode
  children: ReactNode
  defaultExpanded?: boolean
  forceExpand?: boolean
}

export function AccordionCard({
  className = '',
  icon,
  kicker,
  title,
  pillNode,
  children,
  defaultExpanded = false,
  forceExpand = false
}: AccordionCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  useEffect(() => {
    if (forceExpand) setIsExpanded(true)
  }, [forceExpand])

  // In sidebar-closed mode, we might want the card-header to remain clickable 
  // but the details are hidden by CSS anyway. The user clicks to expand.
  return (
    <article className={`accordion-item ${className}`}>
      <div 
        className="card-header accordion-header" 
        onClick={() => setIsExpanded(!isExpanded)} 
        style={{ cursor: 'pointer', transition: 'opacity 0.2s', margin: '4px 0' }}
        onMouseOver={(e) => (e.currentTarget.style.opacity = '0.7')}
        onMouseOut={(e) => (e.currentTarget.style.opacity = '1')}
      >
        <div className="header-title-group">
          <div className="header-icon-box">{icon}</div>
          <div className="header-text-content">
            <span className="card-kicker">{kicker}</span>
            <h3 className="accordion-title">{title}</h3>
          </div>
        </div>
        <div className="header-pill-wrapper">
          {pillNode}
        </div>
      </div>
      
      {isExpanded && (
        <div className="card-body accordion-body">
          {children}
        </div>
      )}
    </article>
  )
}
