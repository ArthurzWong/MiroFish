<template>
  <div class="home">
    <!-- Cinematic opening (once per session) -->
    <component :is="IntroOverlay" v-if="showIntro" @done="showIntro = false" />

    <!-- Living backdrop -->
    <div class="home__ocean" aria-hidden="true">
      <component :is="OceanScene" variant="hero" :quality="oceanQuality" />
    </div>

    <!-- Nav -->
    <header class="nav">
      <div class="nav__inner mf-shell">
        <a class="nav__brand" href="/" aria-label="MiroFish home">
          <span class="nav__mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2.5 12c3.2-4.6 7.2-6.2 10.5-4.6 3.3 1.6 5.2 3.2 8.5 4.6-3.3 1.4-5.2 3-8.5 4.6-3.3 1.6-7.3 0-10.5-4.6Z" />
              <path d="M2.5 12 5 8.6M2.5 12 5 15.4" />
              <circle cx="16.4" cy="11.2" r="0.9" fill="currentColor" stroke="none" />
            </svg>
          </span>
          <span class="nav__word">MiroFish</span>
        </a>

        <nav class="nav__links">
          <span class="nav__status">
            <i class="pulse" aria-hidden="true"></i>{{ $t('home.systemReady') }}
          </span>
          <LanguageSwitcher />
          <a class="nav__ghost" href="https://github.com/666ghj/MiroFish" target="_blank" rel="noopener">
            {{ $t('nav.visitGithub') }}
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M9 7h8v8" /></svg>
          </a>
        </nav>
      </div>
    </header>

    <main>
      <!-- Hero ------------------------------------------------------------ -->
      <section class="hero mf-shell">
        <div class="hero__copy">
          <p class="hero__eyebrow mf-eyebrow">{{ $t('home.tagline') }}</p>

          <h1 class="hero__title">
            <span class="hero__title-a">{{ $t('home.heroTitle1') }}</span>
            <span class="hero__title-b">{{ $t('home.heroTitle2') }}</span>
          </h1>

          <p class="hero__desc">
            <i18n-t keypath="home.heroDesc" tag="span">
              <template #brand><strong class="hl-brand">{{ $t('home.heroDescBrand') }}</strong></template>
              <template #agentScale><em class="hl-agent">{{ $t('home.heroDescAgentScale') }}</em></template>
              <template #optimalSolution><span class="hl-code">{{ $t('home.heroDescOptimalSolution') }}</span></template>
            </i18n-t>
          </p>

          <p class="hero__slogan">
            <span class="hero__slogan-mark" aria-hidden="true"></span>
            {{ $t('home.slogan') }}
          </p>

          <div class="hero__actions">
            <button class="mf-btn hero__cta" @click="focusConsole" :disabled="loading">
              {{ $t('home.consoleCta') }}
              <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v13M6.5 12.5 12 18l5.5-5.5" /></svg>
            </button>
            <button class="mf-btn mf-btn--ghost" @click="scrollToWorkflow">
              {{ $t('home.workflowSequence') }}
            </button>
          </div>
        </div>

        <!-- Console: the actual tool, above the fold -->
        <div class="console" ref="consoleRef">
          <div class="console__head">
            <span class="console__label">{{ $t('home.realitySeed') }}</span>
            <span class="console__meta">{{ $t('home.supportedFormats') }}</span>
          </div>

          <div
            class="drop"
            :class="{ 'is-over': isDragOver, 'has-files': files.length > 0, 'is-disabled': loading }"
            @dragover.prevent="handleDragOver"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
            @keydown.enter.prevent="triggerFileInput"
            @keydown.space.prevent="triggerFileInput"
            role="button"
            tabindex="0"
            :aria-label="$t('home.dragToUpload')"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              accept=".pdf,.md,.txt"
              @change="handleFileSelect"
              class="drop__input"
              :disabled="loading"
            />

            <template v-if="files.length === 0">
              <span class="drop__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" /><path d="M4 16.5v1.8A1.7 1.7 0 0 0 5.7 20h12.6a1.7 1.7 0 0 0 1.7-1.7v-1.8" /></svg>
              </span>
              <span class="drop__title">{{ $t('home.dragToUpload') }}</span>
              <span class="drop__hint">{{ $t('home.orBrowse') }}</span>
            </template>

            <ul v-else class="files">
              <li v-for="(file, index) in files" :key="file.name + index" class="files__row">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a1.6 1.6 0 0 0-1.6 1.6v14.8A1.6 1.6 0 0 0 7 21h10a1.6 1.6 0 0 0 1.6-1.6V7.6Z" /><path d="M14 3v4.6h4.6" /></svg>
                <span class="files__name">{{ file.name }}</span>
                <button class="files__remove" @click.stop="removeFile(index)" :aria-label="$t('common.close')">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18" /></svg>
                </button>
              </li>
            </ul>
          </div>

          <div class="console__divider">
            <span>{{ $t('home.inputParams') }}</span>
          </div>

          <div class="console__field">
            <label class="console__label console__label--prompt" for="sim-prompt">{{ $t('home.simulationPrompt') }}</label>
            <textarea
              id="sim-prompt"
              v-model="formData.simulationRequirement"
              class="console__textarea"
              :placeholder="$t('home.promptPlaceholder')"
              rows="5"
              :disabled="loading"
            ></textarea>
            <span class="console__badge">{{ $t('home.engineBadge') }}</span>
          </div>

          <button
            class="mf-btn mf-btn--primary console__start"
            @click="startSimulation"
            :disabled="!canSubmit || loading"
          >
            <span v-if="!loading">{{ $t('home.startEngine') }}</span>
            <span v-else>{{ $t('home.initializing') }}</span>
            <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h13M12.5 6l6 6-6 6" /></svg>
          </button>

          <div class="console__stats">
            <div class="stat">
              <span class="stat__value">{{ $t('home.metricLowCost') }}</span>
              <span class="stat__label">{{ $t('home.metricLowCostDesc') }}</span>
            </div>
            <span class="stat__rule" aria-hidden="true"></span>
            <div class="stat">
              <span class="stat__value">{{ $t('home.metricHighAvail') }}</span>
              <span class="stat__label">{{ $t('home.metricHighAvailDesc') }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Workflow rail ----------------------------------------------------- -->
      <section class="flow mf-shell" ref="flowRef">
        <h2 class="flow__title">{{ $t('home.workflowSequence') }}</h2>
        <ol class="flow__rail">
          <li v-for="(step, i) in steps" :key="step.title" class="flow__step">
            <span class="flow__num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="flow__body">
              <span class="flow__name">{{ step.title }}</span>
              <span class="flow__desc">{{ step.desc }}</span>
            </span>
          </li>
        </ol>
      </section>

      <!-- Prior runs -------------------------------------------------------- -->
      <section class="ledger mf-shell">
        <HistoryDatabase />
      </section>
    </main>

    <footer class="foot mf-shell">
      <span>{{ $t('home.engineBadge') }}</span>
      <span class="foot__dim">{{ $t('home.version') }}</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

// Three.js only ships when the ocean is actually used.
const OceanScene = defineAsyncComponent(() => import('../components/OceanScene.vue'))
const IntroOverlay = defineAsyncComponent(() => import('../components/IntroOverlay.vue'))

const router = useRouter()
const { t } = useI18n()

const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)
const consoleRef = ref(null)
const flowRef = ref(null)

/* --- intro: once per session, never for reduced-motion visitors --- */
const reduced = typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
const showIntro = ref(false)
const oceanQuality = ref(1)

onMounted(() => {
  const seen = sessionStorage.getItem('mirofish.intro.seen')
  // `?nointro` lets deep links / automated checks land straight on the app
  const skipParam = new URLSearchParams(window.location.search).has('nointro')
  if (!seen && !reduced && !skipParam) {
    showIntro.value = true
    // mark immediately so in-session navigation never replays the opening
    sessionStorage.setItem('mirofish.intro.seen', '1')
  }

  // Trim the scene on small screens / low memory so it stays smooth.
  const small = window.matchMedia('(max-width: 720px)').matches
  const cores = navigator.hardwareConcurrency || 4
  oceanQuality.value = small || cores <= 4 ? 0.6 : 1
})

const steps = computed(() => [
  { title: t('home.step01Title'), desc: t('home.step01Desc') },
  { title: t('home.step02Title'), desc: t('home.step02Desc') },
  { title: t('home.step03Title'), desc: t('home.step03Desc') },
  { title: t('home.step04Title'), desc: t('home.step04Desc') },
  { title: t('home.step05Title'), desc: t('home.step05Desc') }
])

const canSubmit = computed(
  () => formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
)

const triggerFileInput = () => {
  if (!loading.value) fileInput.value?.click()
}

const handleFileSelect = (event) => {
  addFiles(Array.from(event.target.files))
}

const handleDragOver = () => {
  if (!loading.value) isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return
  addFiles(Array.from(e.dataTransfer.files))
}

const addFiles = (newFiles) => {
  const valid = newFiles.filter((file) => {
    const ext = file.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...valid)
}

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const focusConsole = () => {
  consoleRef.value?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' })
  window.setTimeout(() => fileInput.value?.click?.(), 420)
}

const scrollToWorkflow = () => {
  flowRef.value?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' })
}

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement)
    router.push({ name: 'Process', params: { projectId: 'new' } })
  })
}
</script>

<style scoped>
.home {
  position: relative;
  min-height: 100dvh;
  isolation: isolate;
}

.home__ocean {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}

/* ---------------------------------------------------------------- nav */
.nav {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(18px) saturate(130%);
  -webkit-backdrop-filter: blur(18px) saturate(130%);
  background: rgba(3, 6, 12, 0.62);
  border-bottom: 1px solid var(--hairline);
}
.nav__inner {
  height: var(--nav-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.nav__brand {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--text);
}
.nav__mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-s);
  color: var(--bioluma);
  background: var(--bioluma-soft);
  border: 1px solid rgba(52, 228, 201, 0.28);
}
.nav__word {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.12rem;
  letter-spacing: -0.01em;
}
.nav__links {
  display: flex;
  align-items: center;
  gap: clamp(0.5rem, 1.6vw, 1.4rem);
  white-space: nowrap;
}
.nav__status {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
}
.pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--bioluma);
  box-shadow: 0 0 0 0 rgba(52, 228, 201, 0.6);
  animation: pulse 2.6s var(--ease-out) infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(52, 228, 201, 0.55); }
  70% { box-shadow: 0 0 0 10px rgba(52, 228, 201, 0); }
  100% { box-shadow: 0 0 0 0 rgba(52, 228, 201, 0); }
}
.nav__ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--text-dim);
}
.nav__ghost:hover { color: var(--text); }

/* --------------------------------------------------------------- hero */
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  align-items: center;
  gap: clamp(2rem, 5vw, 4.5rem);
  padding-block: clamp(3.5rem, 9vh, 7rem) clamp(3rem, 7vh, 6rem);
  min-height: calc(100dvh - var(--nav-h));
}
.hero__copy {
  position: relative;
  max-width: 40rem;
  align-self: center;
}
/* contrast scrim so the headline stays legible over the moving scene */
.hero__copy::before {
  content: '';
  position: absolute;
  inset: -14% -22% -14% -18%;
  z-index: -1;
  pointer-events: none;
  background: radial-gradient(64% 60% at 34% 52%, rgba(3, 6, 12, 0.9), rgba(3, 6, 12, 0) 74%);
}

.hero__eyebrow { margin: 0 0 1.1rem; color: rgba(172, 194, 220, 0.92); }

.hero__title {
  font-size: clamp(2.6rem, 5.6vw, 4.6rem);
  margin: 0 0 1.35rem;
}
.hero__title-a { display: block; color: var(--text); }
.hero__title-b {
  display: block;
  background: linear-gradient(100deg, #34e4c9 0%, #7ff0dd 36%, #ffd9a8 72%, #ff7a59 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  padding-bottom: 0.08em;
}

.hero__desc {
  max-width: 46ch;
  font-size: clamp(1rem, 1.15vw, 1.1rem);
  line-height: 1.68;
  color: var(--text-dim);
}
.hl-brand { color: var(--text); font-weight: 600; }
.hl-agent { color: var(--bioluma); font-style: normal; font-weight: 600; }
.hl-code { font-family: var(--font-mono); font-size: 0.92em; color: var(--amber); }

.hero__slogan {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-top: 1.4rem;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  letter-spacing: 0.02em;
  color: var(--text-faint);
}
.hero__slogan-mark {
  width: 26px;
  height: 1px;
  background: linear-gradient(90deg, var(--bioluma), transparent);
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 2rem;
}

.hero__cta {
  background: linear-gradient(180deg, rgba(52, 228, 201, 0.22), rgba(52, 228, 201, 0.1));
  border-color: rgba(52, 228, 201, 0.55);
  color: #d8fff7;
  box-shadow: inset 0 1px 0 rgba(200, 255, 245, 0.18);
}
.hero__cta:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(52, 228, 201, 0.32), rgba(52, 228, 201, 0.16));
}

/* ------------------------------------------------------------ console */
.console {
  position: relative;
  padding: clamp(1.15rem, 2.4vw, 1.7rem);
  border-radius: var(--radius-l);
  background: linear-gradient(180deg, rgba(16, 30, 52, 0.82), rgba(8, 16, 30, 0.88));
  border: 1px solid var(--hairline-strong);
  box-shadow: var(--shadow-2), inset 0 1px 0 rgba(180, 225, 255, 0.07);
  backdrop-filter: blur(16px) saturate(125%);
  -webkit-backdrop-filter: blur(16px) saturate(125%);
}
.console__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.9rem;
}
.console__label {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: var(--text-dim);
}
.console__meta { font-size: 0.8rem; color: var(--text-dim); }

.drop {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  min-height: 132px;
  padding: 1.1rem;
  border-radius: var(--radius-m);
  border: 1.5px dashed rgba(140, 190, 255, 0.45);
  background: rgba(6, 14, 26, 0.55);
  cursor: pointer;
  text-align: center;
  transition: border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out);
}
.drop:hover,
.drop.is-over {
  border-color: var(--bioluma);
  background: rgba(52, 228, 201, 0.07);
}
.drop.has-files { justify-content: flex-start; align-items: stretch; }
.drop.is-disabled { opacity: 0.55; pointer-events: none; }
.drop__input { display: none; }
.drop__icon { color: var(--bioluma); }
.drop__title { font-weight: 600; color: var(--text); }
.drop__hint { font-size: 0.86rem; color: var(--text-dim); }

.files { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.45rem; }
.files__row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.5rem 0.7rem;
  border-radius: var(--radius-s);
  background: rgba(140, 190, 255, 0.07);
  color: var(--text-dim);
}
.files__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.87rem;
  color: var(--text);
}
.files__remove {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-xs);
  background: transparent;
  border: none;
  color: var(--text-faint);
  cursor: pointer;
}
.files__remove:hover { color: var(--danger); background: rgba(255, 107, 107, 0.12); }

.console__divider {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin: 1.15rem 0;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-faint);
}
.console__divider::before,
.console__divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--hairline);
}

.console__field { position: relative; display: grid; gap: 0.5rem; }
.console__label--prompt { color: var(--bioluma); }
.console__textarea {
  width: 100%;
  resize: vertical;
  min-height: 104px;
  padding: 0.85rem 0.95rem;
  border-radius: var(--radius-s);
  border: 1px solid var(--hairline);
  background: rgba(4, 10, 20, 0.72);
  color: var(--text);
  font-size: 0.93rem;
  line-height: 1.6;
  transition: border-color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}
.console__textarea::placeholder { color: rgba(180, 199, 222, 0.82); }
.console__textarea:focus {
  outline: none;
  border-color: var(--bioluma);
  box-shadow: 0 0 0 3px rgba(52, 228, 201, 0.14);
}
.console__badge {
  justify-self: end;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-dim);
}

.console__start {
  width: 100%;
  margin-top: 1.15rem;
}

.console__stats {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1.15rem;
  padding-top: 1.05rem;
  border-top: 1px solid var(--hairline);
}
.stat { display: grid; gap: 0.1rem; }
.stat__value { font-family: var(--font-display); font-weight: 600; font-size: 1.02rem; }
.stat__label { font-size: 0.8rem; color: var(--text-dim); }
.stat__rule { width: 1px; height: 26px; background: var(--hairline); }

/* --------------------------------------------------------------- flow */
.flow {
  padding-block: clamp(3rem, 7vh, 5rem);
  border-top: 1px solid var(--hairline);
}
.flow__title {
  font-size: clamp(1.5rem, 2.6vw, 2.1rem);
  margin-bottom: 1.8rem;
}
.flow__rail {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1px;
  margin: 0;
  padding: 0;
  list-style: none;
  border: 1px solid var(--hairline);
  border-radius: var(--radius-m);
  overflow: hidden;
  background: var(--hairline);
}
.flow__step {
  display: grid;
  gap: 0.6rem;
  padding: 1.35rem 1.2rem 1.5rem;
  background: rgba(8, 16, 30, 0.72);
  transition: background var(--dur-fast) var(--ease-out);
}
.flow__step:hover { background: rgba(18, 34, 56, 0.8); }
.flow__num {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--bioluma);
  letter-spacing: 0.1em;
}
.flow__body { display: grid; gap: 0.35rem; }
.flow__name { font-family: var(--font-display); font-weight: 600; font-size: 1.02rem; }
.flow__desc { font-size: 0.86rem; line-height: 1.55; color: var(--text-faint); }

/* ------------------------------------------------------------- ledger */
.ledger { padding-block: clamp(2rem, 5vh, 3.5rem); }

/* --------------------------------------------------------------- foot */
.foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 2rem 2.75rem;
  border-top: 1px solid var(--hairline);
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text-dim);
}
.foot__dim { color: rgba(165, 185, 211, 0.75); }

/* ---------------------------------------------------------- responsive */
@media (max-width: 1024px) {
  .hero {
    grid-template-columns: 1fr;
    gap: 2.25rem;
    min-height: 0;
    padding-block: clamp(2.5rem, 6vh, 4rem);
  }
  .hero__copy { max-width: none; }
  .flow__rail { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 640px) {
  .nav__status { display: none; }
  .nav__inner { gap: 0.5rem; }
  .hero__title { font-size: clamp(2.1rem, 9vw, 2.9rem); }
  .hero__actions { flex-direction: column; align-items: stretch; }
  .hero__actions .mf-btn { width: 100%; }
  .flow__rail { grid-template-columns: 1fr; }
  .console__stats { flex-wrap: wrap; }
  .stat__rule { display: none; }
}
</style>
