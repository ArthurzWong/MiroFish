<template>
  <transition name="intro-fade">
    <div
      v-if="visible"
      class="intro"
      role="dialog"
      aria-modal="true"
      aria-label="MiroFish intro"
      @click="dismiss"
    >
      <OceanScene variant="intro" :quality="1.3" :parallax="0.6" />

      <div class="intro__vignette"></div>

      <div class="intro__content" @click.stop>
        <p class="intro__eyebrow">{{ $t('home.tagline') }}</p>

        <h1 class="intro__wordmark" aria-label="MiroFish">
          <span
            v-for="(ch, i) in letters"
            :key="i"
            class="intro__letter"
            :style="{ animationDelay: `${120 + i * 70}ms` }"
            aria-hidden="true"
          >{{ ch }}</span>
        </h1>

        <p class="intro__slogan" :style="{ animationDelay: `${120 + letters.length * 70 + 160}ms` }">
          {{ $t('home.slogan') }}
        </p>

        <div class="intro__actions" :style="{ animationDelay: `${120 + letters.length * 70 + 380}ms` }">
          <button class="mf-btn mf-btn--primary intro__enter" @click="dismiss">
            {{ $t('home.enter') }}
          </button>
          <button class="intro__skip" @click="dismiss">{{ $t('home.skipIntro') }}</button>
        </div>
      </div>

      <div class="intro__timer"><span :style="{ width: progress + '%' }"></span></div>
    </div>
  </transition>
</template>

<script setup>
/**
 * IntroOverlay — the "awe" opening pass.
 *
 * Water floods in, a fish glides through the light column, the wordmark rises
 * letter by letter, then the curtain lifts into the app. Shown once per
 * browser session; skipped entirely for reduced-motion visitors.
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import OceanScene from './OceanScene.vue'

const emit = defineEmits(['done'])

const visible = ref(true)
const progress = ref(0)
const letters = 'MIROFISH'.split('')

const DURATION = 8200
let startedAt = 0
let tick = null
let autoTimer = null

function dismiss() {
  if (!visible.value) return
  visible.value = false
  cleanup()
  window.setTimeout(() => emit('done'), 620)
}

function cleanup() {
  if (tick) clearInterval(tick)
  if (autoTimer) clearTimeout(autoTimer)
  tick = null
  autoTimer = null
}

function onKey(e) {
  if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    dismiss()
  }
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
  startedAt = performance.now()
  tick = window.setInterval(() => {
    progress.value = Math.min(100, ((performance.now() - startedAt) / DURATION) * 100)
  }, 60)
  autoTimer = window.setTimeout(dismiss, DURATION)
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  cleanup()
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.intro {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: #02040a;
}

.intro__vignette {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(90% 70% at 50% 45%, transparent 32%, rgba(2, 4, 10, 0.72) 100%),
    linear-gradient(180deg, rgba(2, 4, 10, 0.5) 0%, transparent 26%, transparent 70%, rgba(2, 4, 10, 0.85) 100%);
}

.intro__content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.35rem;
  padding: 2rem;
  text-align: center;
}

.intro__eyebrow {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(233, 242, 255, 0.66);
  animation: intro-rise 900ms var(--ease-out) both;
}

.intro__wordmark {
  display: flex;
  gap: 0.02em;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(3.4rem, 13vw, 9rem);
  line-height: 0.94;
  letter-spacing: -0.03em;
  margin: 0;
}

.intro__letter {
  display: inline-block;
  background: linear-gradient(180deg, #ffffff 18%, #8ff6e6 62%, #34e4c9 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 0 60px rgba(52, 228, 201, 0.28);
  animation: intro-letter 1000ms var(--ease-out) both, intro-bob 6s ease-in-out infinite 1.4s;
}

.intro__slogan {
  max-width: 34ch;
  font-size: clamp(0.95rem, 1.5vw, 1.15rem);
  color: rgba(233, 242, 255, 0.74);
  animation: intro-rise 900ms var(--ease-out) both;
}

.intro__actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
  animation: intro-rise 900ms var(--ease-out) both;
}

.intro__enter {
  min-width: 200px;
}

.intro__skip {
  background: none;
  border: none;
  padding: 0.35rem 0.5rem;
  font-size: 0.82rem;
  color: rgba(233, 242, 255, 0.5);
  cursor: pointer;
  transition: color var(--dur-fast) var(--ease-out);
}
.intro__skip:hover { color: rgba(233, 242, 255, 0.9); }

.intro__timer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: rgba(140, 190, 255, 0.12);
}
.intro__timer span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--bioluma), var(--coral));
  transition: width 120ms linear;
}

@keyframes intro-letter {
  from { opacity: 0; transform: translateY(0.4em) scale(1.08); filter: blur(10px); }
  to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}
@keyframes intro-rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes intro-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.intro-fade-leave-active { transition: opacity 620ms var(--ease-out), transform 620ms var(--ease-out); }
.intro-fade-leave-to { opacity: 0; transform: scale(1.03); }

@media (max-width: 640px) {
  .intro__content { gap: 1rem; padding: 1.25rem; }
  .intro__enter { min-width: 0; width: 100%; max-width: 280px; }
}
</style>
