<template>
  <div class="language-switcher" ref="switcherRef">
    <button class="switcher-trigger" @click="toggleDropdown">
      {{ currentLabel }}
      <span class="caret">{{ open ? '▲' : '▼' }}</span>
    </button>
    <ul v-if="open" class="switcher-dropdown">
      <li
        v-for="loc in availableLocales"
        :key="loc.key"
        class="switcher-option"
        :class="{ active: loc.key === locale }"
        @click="switchLocale(loc.key)"
      >
        {{ loc.label }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { availableLocales } from '@/i18n/index.js'

const { locale } = useI18n()
const open = ref(false)
const switcherRef = ref(null)

const currentLabel = computed(() => {
  const found = availableLocales.find(l => l.key === locale.value)
  return found ? found.label : locale.value
})

const toggleDropdown = () => {
  open.value = !open.value
}

const switchLocale = (key) => {
  locale.value = key
  localStorage.setItem('locale', key)
  document.documentElement.lang = key
  open.value = false
}

const onClickOutside = (e) => {
  if (switcherRef.value && !switcherRef.value.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  document.documentElement.lang = locale.value
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>

<style scoped>
.language-switcher {
  position: relative;
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
}

/* Dark theme (the app shell is a deep-ocean surface) */
.switcher-trigger {
  background: transparent;
  color: var(--text-dim, #a5b9d3);
  border: 1px solid var(--hairline-strong, rgba(140, 190, 255, 0.24));
  padding: 5px 12px;
  font-family: var(--font-mono, monospace);
  font-size: 0.78rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: var(--radius-pill, 999px);
  transition: border-color 0.2s, color 0.2s, background-color 0.2s;
}

.switcher-trigger:hover {
  color: var(--text, #e9f2ff);
  border-color: var(--bioluma, #34e4c9);
  background: rgba(140, 190, 255, 0.08);
}

.caret {
  font-size: 0.6rem;
}

.switcher-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 6px;
  background: #0b1626;
  border: 1px solid var(--hairline-strong, rgba(140, 190, 255, 0.24));
  list-style: none;
  padding: 5px 0;
  min-width: 100%;
  z-index: 1000;
  border-radius: var(--radius-s, 10px);
  box-shadow: 0 18px 40px -18px rgba(3, 6, 12, 0.9);
}

.switcher-option {
  padding: 7px 14px;
  font-size: 0.82rem;
  color: var(--text-dim, #a5b9d3);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.switcher-option:hover {
  background: rgba(140, 190, 255, 0.1);
  color: var(--text, #e9f2ff);
}

.switcher-option.active {
  color: var(--bioluma, #34e4c9);
}


</style>
