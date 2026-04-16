import { useCallback, useEffect, useRef } from 'react'

function createNoiseBuffer(context: AudioContext) {
  const buffer = context.createBuffer(1, context.sampleRate * 2, context.sampleRate)
  const data = buffer.getChannelData(0)

  for (let i = 0; i < data.length; i += 1) {
    data[i] = (Math.random() * 2 - 1) * 0.18
  }

  return buffer
}

export function useAmbientSound(active: boolean) {
  const contextRef = useRef<AudioContext | null>(null)
  const gainRef = useRef<GainNode | null>(null)
  const startedRef = useRef(false)
  const nodesRef = useRef<Array<AudioNode & { stop?: (when?: number) => void }>>([])

  const unlockAudio = useCallback(async () => {
    if (typeof window === 'undefined') {
      return
    }

    if (!contextRef.current) {
      const context = new window.AudioContext()
      const masterGain = context.createGain()
      masterGain.gain.value = 0
      masterGain.connect(context.destination)

      contextRef.current = context
      gainRef.current = masterGain
    }

    if (contextRef.current.state === 'suspended') {
      await contextRef.current.resume()
    }
  }, [])

  useEffect(() => {
    const context = contextRef.current
    const masterGain = gainRef.current

    if (!context || !masterGain) {
      return
    }

    if (active && !startedRef.current) {
      startedRef.current = true

      const drone = context.createOscillator()
      drone.type = 'sine'
      drone.frequency.value = 174

      const shimmer = context.createOscillator()
      shimmer.type = 'triangle'
      shimmer.frequency.value = 261.63

      const lfo = context.createOscillator()
      lfo.type = 'sine'
      lfo.frequency.value = 0.08

      const lfoGain = context.createGain()
      lfoGain.gain.value = 18

      const droneGain = context.createGain()
      droneGain.gain.value = 0.04

      const shimmerGain = context.createGain()
      shimmerGain.gain.value = 0.02

      const noiseSource = context.createBufferSource()
      noiseSource.buffer = createNoiseBuffer(context)
      noiseSource.loop = true

      const noiseFilter = context.createBiquadFilter()
      noiseFilter.type = 'lowpass'
      noiseFilter.frequency.value = 450

      const noiseGain = context.createGain()
      noiseGain.gain.value = 0.015

      lfo.connect(lfoGain)
      lfoGain.connect(drone.frequency)

      drone.connect(droneGain)
      shimmer.connect(shimmerGain)
      noiseSource.connect(noiseFilter)
      noiseFilter.connect(noiseGain)

      droneGain.connect(masterGain)
      shimmerGain.connect(masterGain)
      noiseGain.connect(masterGain)

      drone.start()
      shimmer.start()
      noiseSource.start()
      lfo.start()

      nodesRef.current = [drone, shimmer, noiseSource, lfo]
      masterGain.gain.cancelScheduledValues(context.currentTime)
      masterGain.gain.linearRampToValueAtTime(0.12, context.currentTime + 1.2)
    }

    if (!active && startedRef.current) {
      startedRef.current = false
      masterGain.gain.cancelScheduledValues(context.currentTime)
      masterGain.gain.linearRampToValueAtTime(0, context.currentTime + 0.6)

      const timeout = window.setTimeout(() => {
        for (const node of nodesRef.current) {
          node.stop?.()
          node.disconnect()
        }

        nodesRef.current = []
      }, 700)

      return () => window.clearTimeout(timeout)
    }

    return undefined
  }, [active])

  useEffect(() => {
    return () => {
      for (const node of nodesRef.current) {
        node.stop?.()
        node.disconnect()
      }

      gainRef.current?.disconnect()
      void contextRef.current?.close()
    }
  }, [])

  return {
    unlockAudio
  }
}

