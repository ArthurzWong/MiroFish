<template>
  <div
    ref="hostRef"
    class="ocean"
    :class="[`ocean--${variant}`, { 'is-ready': ready, 'is-fallback': failed }]"
    aria-hidden="true"
  >
    <div class="ocean__fallback"></div>
    <div class="ocean__caustics" v-if="!failed"></div>
  </div>
</template>

<script setup>
/**
 * OceanScene — a live deep-ocean scene, generated entirely in code.
 *
 * Signature moment for MiroFish: stylised fish gliding through a light column,
 * trailing rising bubbles, with plankton drifting past. No external 3D assets.
 *
 * Renders a single static frame for reduced-motion visitors and pauses when
 * offscreen or when the tab is hidden. Three.js is code-split by the parent.
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  /** 'hero' = ambient backdrop, 'intro' = cinematic opening */
  variant: { type: String, default: 'hero' },
  /** 0.5 = mobile/cheap, 1 = standard, 1.3 = showpiece */
  quality: { type: Number, default: 1 },
  /** pointer parallax strength */
  parallax: { type: Number, default: 1 }
})

const hostRef = ref(null)
const ready = ref(false)
const failed = ref(false)

let renderer = null
let scene = null
let camera = null
let clock = null
let rafId = null
let observer = null
let resizeObserver = null
let disposed = false
let running = false
let onscreen = true

const fishes = []
let bubbles = null
let bubblePos = null
let bubbleData = null
let plankton = null
let rays = []
let trailIdx = 0
let trailAcc = 0
const TRAIL_COUNT = 90

const pointer = { tx: 0, ty: 0, x: 0, y: 0 }
const reduceMotion =
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

/* ------------------------------------------------------------- geometry */

/** An extruded fin from a 2D profile, so fins stay readable from any angle. */
function finGeo(points, depth = 0.05) {
  const shape = new THREE.Shape()
  shape.moveTo(points[0][0], points[0][1])
  for (let i = 1; i < points.length; i++) shape.lineTo(points[i][0], points[i][1])
  shape.closePath()
  const geo = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false })
  geo.translate(0, 0, -depth / 2)
  geo.rotateY(-Math.PI / 2) // profile plane XY -> YZ (vertical fin, along the body)
  geo.computeVertexNormals()
  return geo
}

/**
 * A deliberately unambiguous stylised fish, pointing along +Z.
 * Classic silhouette: fusiform body, large forked vertical tail, dorsal +
 * pectoral fins, a clear eye, and a mouth at the snout.
 */
function makeFish(palette, scale) {
  const g = new THREE.Group()

  const bodyMat = new THREE.MeshStandardMaterial({
    color: palette.body,
    roughness: 0.42,
    metalness: 0.04,
    emissive: new THREE.Color(palette.glow),
    emissiveIntensity: 0.55
  })
  const finMat = new THREE.MeshStandardMaterial({
    color: palette.fin,
    roughness: 0.5,
    metalness: 0.02,
    emissive: new THREE.Color(palette.glow),
    emissiveIntensity: 0.45,
    transparent: true,
    opacity: 0.96,
    side: THREE.DoubleSide
  })

  // --- body: tapered ellipsoid, flattened on X for a fish profile
  const bodyGeo = new THREE.SphereGeometry(1, 40, 26)
  const bp = bodyGeo.attributes.position
  const bv = new THREE.Vector3()
  for (let i = 0; i < bp.count; i++) {
    bv.fromBufferAttribute(bp, i)
    const tt = (bv.z + 1) / 2 // 0 at tail, 1 at head
    const taper = 0.46 + 0.54 * Math.pow(tt, 0.65)
    bp.setXYZ(i, bv.x * taper, bv.y * taper, bv.z)
  }
  bodyGeo.computeVertexNormals()
  const body = new THREE.Mesh(bodyGeo, bodyMat)
  body.scale.set(0.52, 0.8, 1.28)
  g.add(body)

  // --- tail: a large FORKED vertical fin, hinged at the peduncle
  const tail = new THREE.Mesh(
    finGeo([[0, 0.12], [-1.05, 0.55], [-0.34, 0], [-1.05, -0.55], [0, -0.12]], 0.06),
    finMat
  )
  tail.position.z = -1.1
  g.add(tail)

  // --- dorsal fin: vertical triangle on the spine
  const dorsal = new THREE.Mesh(
    finGeo([[0.3, 0.5], [-0.2, 1.04], [-0.66, 0.44]], 0.05),
    finMat
  )
  g.add(dorsal)

  // --- pectoral fins: cone-based so they keep volume from every angle
  const pectGeo = new THREE.ConeGeometry(0.28, 0.6, 3)
  pectGeo.rotateZ(Math.PI / 2)
  pectGeo.translate(0.3, 0, 0)
  const pectR = new THREE.Mesh(pectGeo, finMat)
  pectR.position.set(0.28, -0.14, 0.26)
  pectR.scale.set(1, 0.5, 0.32)
  pectR.rotation.z = -0.4
  g.add(pectR)
  const pectL = pectR.clone()
  pectL.scale.set(-1, 0.5, 0.32)
  pectL.position.x = -0.28
  pectL.rotation.z = 0.4
  g.add(pectL)

  // --- eye: white sclera + dark pupil, protruding from the head
  const white = new THREE.Mesh(
    new THREE.SphereGeometry(0.15, 16, 14),
    new THREE.MeshStandardMaterial({ color: 0xf8fcff, roughness: 0.2 })
  )
  white.position.set(0.36, 0.2, 0.66)
  g.add(white)
  const pupil = new THREE.Mesh(
    new THREE.SphereGeometry(0.085, 14, 12),
    new THREE.MeshStandardMaterial({ color: 0x050d16, roughness: 0.12, metalness: 0.4 })
  )
  pupil.position.set(0.42, 0.2, 0.72)
  g.add(pupil)

  // --- mouth at the snout
  const mouth = new THREE.Mesh(
    new THREE.SphereGeometry(0.12, 12, 10),
    new THREE.MeshStandardMaterial({ color: 0x2a1008, roughness: 0.6 })
  )
  mouth.scale.set(0.9, 0.45, 0.6)
  mouth.position.set(0, -0.12, 1.12)
  g.add(mouth)

  g.scale.setScalar(scale)
  g.userData = { tail, pectR, pectL, dorsal, phase: Math.random() * Math.PI * 2 }
  return g
}

function makeRayTexture() {
  const c = document.createElement('canvas')
  c.width = 64
  c.height = 256
  const ctx = c.getContext('2d')
  const grad = ctx.createLinearGradient(0, 0, 0, 256)
  grad.addColorStop(0, 'rgba(150,240,255,0.6)')
  grad.addColorStop(0.45, 'rgba(120,220,255,0.18)')
  grad.addColorStop(1, 'rgba(120,220,255,0)')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, 64, 256)
  const tex = new THREE.CanvasTexture(c)
  tex.needsUpdate = true
  return tex
}

/** A bubble sprite: bright rim, soft interior, specular glint. */
function makeBubbleTexture() {
  const s = 64
  const c = document.createElement('canvas')
  c.width = s
  c.height = s
  const ctx = c.getContext('2d')
  const grad = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2)
  grad.addColorStop(0, 'rgba(205,245,255,0.10)')
  grad.addColorStop(0.58, 'rgba(190,240,255,0.14)')
  grad.addColorStop(0.78, 'rgba(215,250,255,0.95)')
  grad.addColorStop(0.9, 'rgba(235,253,255,0.45)')
  grad.addColorStop(1, 'rgba(205,245,255,0)')
  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.arc(s / 2, s / 2, s / 2, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = 'rgba(255,255,255,0.95)'
  ctx.beginPath()
  ctx.arc(s * 0.35, s * 0.32, s * 0.07, 0, Math.PI * 2)
  ctx.fill()
  const tex = new THREE.CanvasTexture(c)
  tex.needsUpdate = true
  return tex
}

/* ---------------------------------------------------------------- build */

function build() {
  const host = hostRef.value
  const w = host.clientWidth || 1
  const h = host.clientHeight || 1

  renderer = new THREE.WebGLRenderer({
    antialias: props.quality >= 1,
    alpha: true,
    powerPreference: 'high-performance'
  })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2) * Math.min(props.quality, 1))
  renderer.setSize(w, h, false)
  // Linear tone mapping keeps the coral/teal saturated (ACES washed it to brown)
  renderer.toneMapping = THREE.LinearToneMapping
  renderer.toneMappingExposure = 1.0
  renderer.domElement.style.cssText = 'width:100%;height:100%;display:block'
  host.appendChild(renderer.domElement)

  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x03060c, 0.026)

  camera = new THREE.PerspectiveCamera(46, w / h, 0.1, 120)
  camera.position.set(0, 0.4, 9)

  clock = new THREE.Clock()

  /* light ----------------------------------------------------------------- */
  scene.add(new THREE.AmbientLight(0x24425c, 0.85))
  scene.add(new THREE.HemisphereLight(0x5ff2dc, 0x071a2a, 0.6))

  const key = new THREE.DirectionalLight(0xf2feff, 2.7)
  key.position.set(4, 7, 6)
  scene.add(key)

  const fill = new THREE.DirectionalLight(0x9fe6ff, 0.75)
  fill.position.set(-6, 1, 5)
  scene.add(fill)

  // cool rim from behind gives the body a readable light-to-dark falloff
  const rim = new THREE.DirectionalLight(0x7ff0dd, 0.85)
  rim.position.set(-3, -4, -6)
  scene.add(rim)

  const surface = new THREE.PointLight(0x5ff2dc, 55, 40, 2)
  surface.position.set(0, 8, 4)
  scene.add(surface)

  /* god rays -------------------------------------------------------------- */
  const rayTex = makeRayTexture()
  const rayCount = props.quality >= 1 ? 6 : 3
  for (let i = 0; i < rayCount; i++) {
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(1.7 + Math.random() * 1.5, 20),
      new THREE.MeshBasicMaterial({
        map: rayTex,
        transparent: true,
        opacity: 0.12,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide
      })
    )
    mesh.position.set(-9 + i * 3.4 + Math.random(), 5, -5 - Math.random() * 4)
    mesh.rotation.z = (Math.random() - 0.5) * 0.3
    mesh.userData = { base: mesh.rotation.z, seed: Math.random() * 6.28 }
    scene.add(mesh)
    rays.push(mesh)
  }

  /* plankton -------------------------------------------------------------- */
  const pCount = Math.round(320 * props.quality)
  const pArr = new Float32Array(pCount * 3)
  for (let i = 0; i < pCount; i++) {
    pArr[i * 3] = (Math.random() - 0.5) * 26
    pArr[i * 3 + 1] = (Math.random() - 0.5) * 14
    pArr[i * 3 + 2] = (Math.random() - 0.5) * 16 - 5
  }
  const pGeo = new THREE.BufferGeometry()
  pGeo.setAttribute('position', new THREE.BufferAttribute(pArr, 3))
  plankton = new THREE.Points(
    pGeo,
    new THREE.PointsMaterial({
      color: 0xa9e3ff,
      size: 0.028,
      transparent: true,
      opacity: 0.3,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    })
  )
  scene.add(plankton)

  /* bubbles — foreground sprites; the first TRAIL_COUNT form the fish trail - */
  const bCount = Math.round((props.variant === 'intro' ? 300 : 230) * props.quality)
  bubblePos = new Float32Array(bCount * 3)
  bubbleData = []
  for (let i = 0; i < bCount; i++) {
    const d = {
      x: (Math.random() - 0.5) * 20,
      y: -6 - Math.random() * 14,
      z: -3 + Math.random() * 7,
      vy: 1.0 + Math.random() * 1.8,
      wobble: Math.random() * 6.28,
      wobbleSpeed: 0.5 + Math.random() * 1.2,
      trail: i < TRAIL_COUNT
    }
    bubbleData.push(d)
    bubblePos[i * 3] = d.x
    bubblePos[i * 3 + 1] = d.y
    bubblePos[i * 3 + 2] = d.z
  }
  const bGeo = new THREE.BufferGeometry()
  bGeo.setAttribute('position', new THREE.BufferAttribute(bubblePos, 3))
  bubbles = new THREE.Points(
    bGeo,
    new THREE.PointsMaterial({
      map: makeBubbleTexture(),
      size: props.variant === 'intro' ? 0.78 : 0.68,
      transparent: true,
      opacity: 1,
      depthWrite: false,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending
    })
  )
  scene.add(bubbles)

  /* the fish -------------------------------------------------------------- */
  const palettes = [
    { body: 0xff8557, fin: 0xffc4a6, glow: 0x54200c }, // coral
    { body: 0x2fe6cb, fin: 0xa6fbef, glow: 0x0a4a41 }, // bioluminescent teal
    { body: 0xffc46b, fin: 0xffe7b8, glow: 0x4d3404 }  // amber
  ]
  const specs =
    props.variant === 'intro'
      ? [
          { p: 0, scale: 1.5, R: 6.2, tilt: 0.72, yAmp: 0.9, zAmp: 2.4, speed: 0.3, y: 0.3, ox: 0 },
          { p: 1, scale: 0.62, R: 7.0, tilt: 0.5, yAmp: 1.5, zAmp: 2.6, speed: 0.22, y: -2.0, ox: 1.5 },
          { p: 2, scale: 0.5, R: 8.0, tilt: 0.9, yAmp: 1.1, zAmp: 1.8, speed: 0.17, y: 2.1, ox: -1.5 }
        ]
      : [
          // hero backdrop: one fish in the open lower-left, one small and distant
          { p: 0, scale: 1.05, R: 4.0, tilt: 0.7, yAmp: 0.4, zAmp: 1.5, speed: 0.22, y: -2.9, ox: -3.4 },
          { p: 1, scale: 0.42, R: 7.4, tilt: 0.55, yAmp: 0.7, zAmp: 1.4, speed: 0.15, y: 2.7, ox: 3.6 }
        ]
  for (const s of specs) {
    const f = makeFish(palettes[s.p], s.scale)
    f.userData.spec = s
    scene.add(f)
    fishes.push(f)
  }

  ready.value = true
}

/* -------------------------------------------------------------- animate */

function placeFish(f, t) {
  const s = f.userData.spec
  const a = t * s.speed + f.userData.phase
  f.position.set(
    Math.sin(a) * s.R + (s.ox || 0),
    Math.sin(a * 1.6) * s.yAmp + s.y,
    Math.cos(a * s.tilt) * s.zAmp - 1.0
  )
  f.rotation.y = Math.atan2(Math.cos(a) * s.R, -Math.sin(a * s.tilt) * s.tilt * s.zAmp)
  f.rotation.z = -Math.sin(a * 1.6) * 0.1
  f.rotation.x = -Math.cos(a * 1.6) * 0.07
}

function frame() {
  rafId = requestAnimationFrame(frame)
  const t = clock.getElapsedTime()

  pointer.x += (pointer.tx - pointer.x) * 0.05
  pointer.y += (pointer.ty - pointer.y) * 0.05

  for (const f of fishes) {
    const p = f.userData.phase
    placeFish(f, t)
    f.userData.tail.rotation.y = Math.sin(t * 7.4 + p) * 0.55
    f.userData.pectR.rotation.z = -0.2 + Math.sin(t * 5.6 + p) * 0.35
    f.userData.pectL.rotation.z = 0.2 - Math.sin(t * 5.6 + p + 0.4) * 0.35
    f.userData.dorsal.rotation.y = Math.sin(t * 4.4 + p) * 0.14
  }

  /* feed the trail from the hero fish's mouth — the cinematic variant only,
     so the ambient hero backdrop stays quiet behind the UI */
  if (props.variant === 'intro' && fishes[0]) {
    trailAcc += 0.016
    while (trailAcc > 0.045) {
      trailAcc -= 0.045
      const b = bubbleData[trailIdx % TRAIL_COUNT]
      const f = fishes[0]
      b.x = f.position.x + Math.sin(f.rotation.y) * 1.0
      b.z = f.position.z + Math.cos(f.rotation.y) * 1.0
      b.y = f.position.y
      b.vy = 0.9 + Math.random() * 1.1
      b.wobble = Math.random() * 6.28
      b.wobbleSpeed = 0.7 + Math.random() * 0.9
      trailIdx++
    }
  }

  if (bubbles) {
    for (let i = 0; i < bubbleData.length; i++) {
      const b = bubbleData[i]
      b.y += b.vy * 0.016
      if (b.y > 9.5) {
        b.y = -8 - Math.random() * 8
        b.x = (Math.random() - 0.5) * 20
        b.z = -3 + Math.random() * 7
      }
      bubblePos[i * 3] = b.x + Math.sin(t * b.wobbleSpeed + b.wobble) * 0.32
      bubblePos[i * 3 + 1] = b.y
      bubblePos[i * 3 + 2] = b.z
    }
    bubbles.geometry.attributes.position.needsUpdate = true
  }

  if (plankton) {
    plankton.rotation.y = t * 0.012
    plankton.position.y = Math.sin(t * 0.18) * 0.3
  }

  for (const r of rays) {
    r.rotation.z = r.userData.base + Math.sin(t * 0.22 + r.userData.seed) * 0.05
    r.material.opacity = 0.09 + Math.sin(t * 0.35 + r.userData.seed) * 0.04
  }

  const px = props.parallax * 0.8
  camera.position.x += pointer.x * px - camera.position.x * 0.04
  camera.position.y += 0.4 + pointer.y * 0.45 * props.parallax - camera.position.y * 0.04
  camera.lookAt(0, 0.1, 0)

  renderer.render(scene, camera)
}

function start() {
  if (running || disposed || reduceMotion) return
  running = true
  clock.start()
  frame()
}

function stop() {
  if (!running) return
  running = false
  if (rafId) cancelAnimationFrame(rafId)
  rafId = null
}

function renderOnce() {
  if (!renderer) return
  clock.start()
  for (const f of fishes) placeFish(f, 0)
  renderer.render(scene, camera)
}

/* --------------------------------------------------------------- events */

function onResize() {
  const host = hostRef.value
  if (!host || !renderer || !camera) return
  const w = host.clientWidth || 1
  const h = host.clientHeight || 1
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

function onPointerMove(e) {
  pointer.tx = (e.clientX / window.innerWidth) * 2 - 1
  pointer.ty = -((e.clientY / window.innerHeight) * 2 - 1)
}

function onVisibility() {
  if (document.hidden) stop()
  else if (onscreen) start()
}

/* ---------------------------------------------------------- lifecycle */

onMounted(() => {
  try {
    build()
  } catch (err) {
    console.warn('[OceanScene] WebGL unavailable, using gradient fallback.', err)
    failed.value = true
    return
  }

  onResize()

  if (reduceMotion) {
    renderOnce()
    return
  }

  start()

  window.addEventListener('pointermove', onPointerMove, { passive: true })
  window.addEventListener('resize', onResize)
  document.addEventListener('visibilitychange', onVisibility)

  if ('ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(onResize)
    resizeObserver.observe(hostRef.value)
  }
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      (entries) => {
        onscreen = entries[0].isIntersecting
        if (onscreen && !document.hidden) start()
        else stop()
      },
      { threshold: 0.01 }
    )
    observer.observe(hostRef.value)
  }
})

onBeforeUnmount(() => {
  disposed = true
  stop()
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('resize', onResize)
  document.removeEventListener('visibilitychange', onVisibility)
  observer?.disconnect()
  resizeObserver?.disconnect()

  scene?.traverse((obj) => {
    if (obj.geometry) obj.geometry.dispose()
    if (obj.material) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material]
      mats.forEach((m) => {
        if (m.map) m.map.dispose()
        m.dispose()
      })
    }
  })
  renderer?.dispose()
  const el = renderer?.domElement
  if (el?.parentNode) el.parentNode.removeChild(el)
})
</script>

<style scoped>
.ocean {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(120% 90% at 50% -18%, rgba(52, 228, 201, 0.2), transparent 60%),
    radial-gradient(80% 60% at 10% 6%, rgba(255, 122, 89, 0.13), transparent 58%),
    linear-gradient(180deg, #0a1a33 0%, #050c1a 46%, #02040a 100%);
}

.ocean__fallback {
  position: absolute;
  inset: 0;
  opacity: 0;
  background:
    radial-gradient(60% 40% at 50% 28%, rgba(52, 228, 201, 0.22), transparent 70%),
    linear-gradient(180deg, #0a1a33, #02040a);
  transition: opacity 600ms var(--ease-out);
}
.ocean.is-fallback .ocean__fallback { opacity: 1; }

.ocean__caustics {
  position: absolute;
  inset: -20%;
  pointer-events: none;
  opacity: 0.14;
  background-image:
    repeating-linear-gradient(115deg, rgba(120, 240, 220, 0.1) 0 2px, transparent 2px 26px),
    repeating-linear-gradient(65deg, rgba(120, 240, 220, 0.07) 0 2px, transparent 2px 34px);
  mix-blend-mode: screen;
  animation: caustics-drift 18s linear infinite;
}

@keyframes caustics-drift {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-3%, -2%, 0); }
}

@media (prefers-reduced-motion: reduce) {
  .ocean__caustics { animation: none; }
}
</style>
