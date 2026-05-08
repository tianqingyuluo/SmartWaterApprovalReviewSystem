import { ref, onUnmounted } from 'vue'

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  shouldStop: (data: T) => boolean,
  onUpdate: (data: T) => void,
) {
  const isPolling = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  function start() {
    if (isPolling.value) return
    isPolling.value = true

    const poll = async () => {
      try {
        const data = await fetcher()
        onUpdate(data)
        if (shouldStop(data)) {
          stop()
        }
      } catch {
        // polling continues on transient errors
      }
    }

    poll()
    timer = setInterval(poll, intervalMs)
  }

  function stop() {
    isPolling.value = false
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  onUnmounted(stop)

  return { isPolling, start, stop }
}
