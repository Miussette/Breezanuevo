import type { ChatMessage as ChatMessageType } from '../types'

type ChatMessageProps = {
  message: ChatMessageType
}

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <article className={`message-bubble ${message.role === 'user' ? 'user' : 'agent'}`}>
      <span className="message-role">{message.role === 'user' ? 'Tú' : 'Breeza'}</span>
      <p>{message.content}</p>

      {message.actions?.length ? (
        <div className="message-actions">
          {message.actions.map((action) => (
            <span
              className="message-action-tag"
              key={`${message.id}-${action}`}
            >
              {action}
            </span>
          ))}
        </div>
      ) : null}
    </article>
  )
}
