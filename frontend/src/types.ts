export type ActionKind = 'breathing' | 'break' | 'mood'

export type ChatMessage = {
  id: string
  role: 'user' | 'agent'
  content: string
  actions?: ActionKind[]
}

export type BreathingAction = {
  action: 'breathing'
  pattern: string
  cycles: number
  secondsPerPhase: number
  guidance: string
  emotion: string
}

export type BreakAction = {
  action: 'break'
  breakAt: string
  breakMinutes: number
  reason: string
}

export type MoodEntry = {
  id: string
  mood: string
  intensity: number
  note: string
  capturedText: string
  timestamp: string
}

export type MoodAction = {
  action: 'mood'
  saved: true
  entry: MoodEntry
}

export type ActionDetails = {
  breathing?: BreathingAction
  break?: BreakAction
  mood?: MoodAction
}

export type ChatResponse = {
  response: string
  actions: ActionKind[]
  actionDetails: ActionDetails
  moodHistory: MoodEntry[]
}
