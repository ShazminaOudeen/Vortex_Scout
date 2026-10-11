// Sensory feedback: Web Audio synthesis + Haptic vibration (Feature D2)

let audioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!audioCtx) {
    const AudioContextClass =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume().catch(() => {});
  }
  return audioCtx;
}

export function isSoundEnabled(): boolean {
  if (typeof window === "undefined") return true;
  const stored = localStorage.getItem("scout_sound_enabled");
  return stored === null ? true : stored === "true";
}

export function setSoundEnabled(enabled: boolean): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("scout_sound_enabled", String(enabled));
}

export function toggleSound(): boolean {
  const current = isSoundEnabled();
  setSoundEnabled(!current);
  return !current;
}

export function triggerHaptic(type: "tap" | "success" | "warning" = "tap"): void {
  if (typeof window === "undefined" || !("vibrate" in navigator)) return;
  try {
    if (type === "tap") {
      navigator.vibrate(30);
    } else if (type === "success") {
      navigator.vibrate([40, 30, 50, 30, 120]);
    } else if (type === "warning") {
      navigator.vibrate([60, 40, 60]);
    }
  } catch {
    // Vibration blocked or unsupported
  }
}

export function playChime(
  type: "restocked" | "damaged" | "false_alarm" | "complete" | "undo"
): void {
  if (!isSoundEnabled()) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  const now = ctx.currentTime;

  if (type === "restocked") {
    // Upbeat rising chime (C5 -> G5)
    playTone(ctx, 523.25, now, 0.12, 0.15); // C5
    playTone(ctx, 783.99, now + 0.08, 0.22, 0.18); // G5
  } else if (type === "damaged") {
    // Warm confirmation tone (A4 -> F4)
    playTone(ctx, 440.0, now, 0.12, 0.12);
    playTone(ctx, 349.23, now + 0.09, 0.2, 0.12);
  } else if (type === "false_alarm") {
    // Subtle wooden transient / click
    playTone(ctx, 587.33, now, 0.08, 0.1);
  } else if (type === "complete") {
    // Festive 4-note celebration chime (C5 -> E5 -> G5 -> C6)
    playTone(ctx, 523.25, now, 0.15, 0.15);
    playTone(ctx, 659.25, now + 0.1, 0.18, 0.18);
    playTone(ctx, 783.99, now + 0.2, 0.22, 0.2);
    playTone(ctx, 1046.5, now + 0.32, 0.45, 0.22);
  } else if (type === "undo") {
    // Descending soft pop
    playTone(ctx, 493.88, now, 0.08, 0.12);
    playTone(ctx, 369.99, now + 0.07, 0.15, 0.12);
  }
}

function playTone(
  ctx: AudioContext,
  freq: number,
  startTime: number,
  duration: number,
  volume: number
): void {
  try {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, startTime);

    gain.gain.setValueAtTime(volume, startTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(startTime);
    osc.stop(startTime + duration);
  } catch {
    // Ignore audio glitches
  }
}
