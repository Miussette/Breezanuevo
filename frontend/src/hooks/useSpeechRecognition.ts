import { useEffect, useRef, useState } from 'react'

type Options = {
  lang?: string
  onTranscript: (transcript: string) => void
}

export function useSpeechRecognition({ lang = 'es-ES', onTranscript }: Options) {
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  const [isSupported, setIsSupported] = useState(false)
  const [isListening, setIsListening] = useState(false)

  useEffect(() => {
    const SpeechRecognitionConstructor =
      window.SpeechRecognition ?? window.webkitSpeechRecognition

    if (!SpeechRecognitionConstructor) {
      setIsSupported(false)
      return
    }

    setIsSupported(true)

    const recognition = new SpeechRecognitionConstructor()
    recognition.lang = lang
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onresult = (event) => {
      const results = Array.from(event.results)
      const transcript = results
        .map((result) => result[0].transcript)
        .join(' ')
        .trim()

      if (transcript) {
        onTranscript(transcript)
      }
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.onerror = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition

    return () => {
      recognition.stop()
    }
  }, [lang, onTranscript])

  const startListening = () => {
    recognitionRef.current?.start()
    setIsListening(true)
  }

  const stopListening = () => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }

  return {
    isListening,
    isSupported,
    startListening,
    stopListening
  }
}

