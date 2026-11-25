import * as THREE from 'three'

export interface HeroScene {
  syncPalette(): void
  setReducedMotion(value: boolean): void
  setPaused(value: boolean): void
  destroy(): void
}

const FALLBACK = {
  primary: '#1467a8',
  secondary: '#2773af',
  accent: '#85b0d2',
  ink: '#cbd5e1',
  seed: '#2773af',
  line: '#1467a8',
  tone3: '#b4cee3',
} as const

function readVar(element: Element, name: string, fallback: string): string {
  return getComputedStyle(element).getPropertyValue(name).trim() || fallback
}

function resolveColor(value: string, fallback: string): THREE.Color {
  const canvas = document.createElement('canvas')
  canvas.width = 1
  canvas.height = 1
  const ctx = canvas.getContext('2d')
  if (!ctx) return new THREE.Color(fallback)
  ctx.fillStyle = '#010203'
  ctx.fillStyle = value
  if (ctx.fillStyle === '#010203') return new THREE.Color(fallback)
  ctx.fillRect(0, 0, 1, 1)
  const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data
  return new THREE.Color().setRGB(r / 255, g / 255, b / 255, THREE.SRGBColorSpace)
}

function readPalette(element: Element) {
  return {
    primary: resolveColor(readVar(element, '--surface-blue-6', FALLBACK.primary), FALLBACK.primary),
    secondary: resolveColor(readVar(element, '--ink-blue-5', FALLBACK.secondary), FALLBACK.secondary),
    accent: resolveColor(readVar(element, '--ink-blue-4', FALLBACK.accent), FALLBACK.accent),
    ink: resolveColor(readVar(element, '--ink-gray-8', FALLBACK.ink), FALLBACK.ink),
    seed: resolveColor(readVar(element, '--ink-blue-5', FALLBACK.seed), FALLBACK.seed),
    line: resolveColor(readVar(element, '--ink-blue-6', FALLBACK.line), FALLBACK.line),
    tone3: resolveColor(readVar(element, '--surface-blue-3', FALLBACK.tone3), FALLBACK.tone3),
  }
}

function makeGlowTexture(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 128
  canvas.height = 128
  const ctx = canvas.getContext('2d')!
  const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64)
  gradient.addColorStop(0, 'rgba(255,255,255,1)')
  gradient.addColorStop(0.22, 'rgba(255,255,255,0.55)')
  gradient.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, 128, 128)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}

export function createHeroScene(container: HTMLElement): HeroScene {
  const disposables: Array<{ dispose(): void }> = []
  const own = <T extends { dispose(): void }>(item: T): T => {
    disposables.push(item)
    return item
  }

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100)
  camera.position.set(0, 0.4, 7.4)

  const renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance',
  })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setClearColor(0x000000, 0)
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.domElement.style.display = 'block'
  renderer.domElement.style.width = '100%'
  renderer.domElement.style.height = '100%'
  container.appendChild(renderer.domElement)

  let palette = readPalette(container)
  const group = new THREE.Group()
  scene.add(group)

  const glowTexture = own(makeGlowTexture())
  const coreMaterial = own(
    new THREE.MeshBasicMaterial({ color: palette.primary, wireframe: true, transparent: true, opacity: 0.6 }),
  )
  const coreMesh = new THREE.Mesh(own(new THREE.IcosahedronGeometry(0.66, 1)), coreMaterial)
  const seedMaterial = own(new THREE.MeshBasicMaterial({ color: palette.seed, transparent: true, opacity: 0.92 }))
  const seedMesh = new THREE.Mesh(own(new THREE.IcosahedronGeometry(0.38, 1)), seedMaterial)
  const shellMaterial = own(
    new THREE.MeshBasicMaterial({ color: palette.primary, wireframe: true, transparent: true, opacity: 0.18 }),
  )
  const shellMesh = new THREE.Mesh(own(new THREE.IcosahedronGeometry(1.08, 1)), shellMaterial)

  const coreGlowMaterial = own(
    new THREE.SpriteMaterial({
      map: glowTexture,
      color: palette.primary,
      transparent: true,
      opacity: 0.42,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  )
  const coreGlow = new THREE.Sprite(coreGlowMaterial)
  coreGlow.scale.setScalar(4.2)
  group.add(coreGlow, shellMesh, coreMesh, seedMesh)

  const loop = new THREE.CatmullRomCurve3(
    [
      new THREE.Vector3(2.34, 0.12, 0.0),
      new THREE.Vector3(1.62, 0.92, -1.52),
      new THREE.Vector3(0.0, 1.18, -2.36),
      new THREE.Vector3(-1.7, 0.58, -1.48),
      new THREE.Vector3(-2.38, -0.18, 0.22),
      new THREE.Vector3(-1.3, -0.94, 1.78),
      new THREE.Vector3(0.62, -1.12, 2.3),
      new THREE.Vector3(1.92, -0.52, 1.42),
    ],
    true,
    'catmullrom',
    0.5,
  )

  const loopMaterial = own(new THREE.LineBasicMaterial({ color: palette.line, transparent: true, opacity: 0.42 }))
  const loopLine = new THREE.Line(own(new THREE.BufferGeometry().setFromPoints(loop.getPoints(400))), loopMaterial)
  group.add(loopLine)

  const ringMaterial = own(
    new THREE.MeshBasicMaterial({ color: palette.secondary, transparent: true, opacity: 0.14 }),
  )
  const ring = new THREE.Mesh(own(new THREE.TorusGeometry(2.86, 0.006, 4, 200)), ringMaterial)
  ring.rotation.set(0.9, 0.3, 0.4)
  const ring2Material = own(
    new THREE.MeshBasicMaterial({ color: palette.tone3, transparent: true, opacity: 0.12 }),
  )
  const ring2 = new THREE.Mesh(own(new THREE.TorusGeometry(2.04, 0.004, 4, 180)), ring2Material)
  ring2.rotation.set(-0.5, 1.1, 0.2)
  group.add(ring, ring2)

  const nodeColors = [palette.primary, palette.secondary, palette.accent]
  const nodeMaterials = nodeColors.map(
    (color) => own(new THREE.MeshBasicMaterial({ color })) as THREE.MeshBasicMaterial,
  )
  const nodeGlowMaterials = nodeColors.map(
    (color) =>
      own(
        new THREE.SpriteMaterial({
          map: glowTexture,
          color,
          transparent: true,
          opacity: 0.8,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        }),
      ) as THREE.SpriteMaterial,
  )
  const nodeGeometry = own(new THREE.SphereGeometry(0.13, 20, 20))
  const nodes = nodeMaterials.map((material) => new THREE.Mesh(nodeGeometry, material))
  const nodeGlows = nodeGlowMaterials.map((material) => {
    const sprite = new THREE.Sprite(material)
    sprite.scale.setScalar(1.6)
    return sprite
  })
  group.add(...nodes, ...nodeGlows)

  const samples = loop.getSpacedPoints(900)
  const flowCount = 460
  const flowPositions = new Float32Array(flowCount * 3)
  const flowColors = new Float32Array(flowCount * 3)
  const flowGeometry = own(new THREE.BufferGeometry())
  flowGeometry.setAttribute('position', new THREE.BufferAttribute(flowPositions, 3))
  flowGeometry.setAttribute('color', new THREE.BufferAttribute(flowColors, 3))
  const flowMaterial = own(
    new THREE.PointsMaterial({
      size: 0.055,
      sizeAttenuation: true,
      vertexColors: true,
      transparent: true,
      opacity: 1,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  )
  const flow = new THREE.Points(flowGeometry, flowMaterial)
  group.add(flow)

  const starCount = 280
  const starPositions = new Float32Array(starCount * 3)
  for (let i = 0; i < starCount; i++) {
    starPositions[i * 3] = (Math.random() - 0.5) * 13
    starPositions[i * 3 + 1] = (Math.random() - 0.5) * 9
    starPositions[i * 3 + 2] = -3 - Math.random() * 5
  }
  const starGeometry = own(new THREE.BufferGeometry())
  starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3))
  const starMaterial = own(
    new THREE.PointsMaterial({
      color: palette.ink,
      size: 0.025,
      transparent: true,
      opacity: 0.32,
      depthWrite: false,
    }),
  )
  const stars = new THREE.Points(starGeometry, starMaterial)
  scene.add(stars)

  function paintFlow() {
    const colors = [palette.primary, palette.secondary, palette.accent]
    for (let i = 0; i < flowCount; i++) {
      const color = colors[i % colors.length]
      flowColors[i * 3] = color.r
      flowColors[i * 3 + 1] = color.g
      flowColors[i * 3 + 2] = color.b
    }
    flowGeometry.getAttribute('color').needsUpdate = true
  }

  function placeFlow(phase: number) {
    for (let i = 0; i < flowCount; i++) {
      const index =
        ((Math.floor((i / flowCount) * samples.length) + Math.floor(phase)) % samples.length +
          samples.length) %
        samples.length
      const point = samples[index]
      flowPositions[i * 3] = point.x
      flowPositions[i * 3 + 1] = point.y
      flowPositions[i * 3 + 2] = point.z
    }
    flowGeometry.getAttribute('position').needsUpdate = true
  }

  function placeNodes(phase: number) {
    for (let i = 0; i < nodes.length; i++) {
      const point = loop.getPointAt((phase + i / nodes.length) % 1)
      nodes[i].position.copy(point)
      nodeGlows[i].position.copy(point)
    }
  }

  paintFlow()
  placeFlow(0)
  placeNodes(0)

  let raf = 0
  let paused = false
  let reduced = false
  let elapsed = 0
  let flowPhase = 0
  let last = performance.now()
  const pointer = { x: 0, y: 0 }
  const eased = { x: 0, y: 0 }

  function update(dt: number) {
    elapsed += dt
    group.rotation.y += dt * 0.06
    group.rotation.z = Math.sin(elapsed * 0.12) * 0.05
    coreMesh.rotation.x += dt * 0.12
    coreMesh.rotation.y += dt * 0.18
    shellMesh.rotation.y -= dt * 0.08
    ring.rotation.z += dt * 0.03
    ring2.rotation.y -= dt * 0.02
    stars.rotation.y += dt * 0.008
    flowPhase += dt * 22
    placeFlow(flowPhase)
    placeNodes((elapsed * 0.035) % 1)

    eased.x += (pointer.x - eased.x) * Math.min(1, dt * 3)
    eased.y += (pointer.y - eased.y) * Math.min(1, dt * 3)
    camera.position.x = eased.x * 0.85
    camera.position.y = 0.4 + eased.y * 0.5
    camera.lookAt(0, 0, 0)
  }

  function frame(now: number) {
    const dt = Math.min(Math.max((now - last) / 1000, 0), 0.05)
    last = now
    update(dt)
    renderer.render(scene, camera)
    raf = requestAnimationFrame(frame)
  }

  function stop() {
    if (raf) cancelAnimationFrame(raf)
    raf = 0
  }

  function start() {
    if (raf || paused || reduced) return
    last = performance.now()
    raf = requestAnimationFrame(frame)
  }

  function renderOnce() {
    renderer.render(scene, camera)
  }

  function resize() {
    const width = container.clientWidth
    const height = container.clientHeight
    if (!width || !height) return
    renderer.setSize(width, height, false)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    group.scale.setScalar(Math.min(1.25, Math.max(0.78, width / 620)))
    group.position.x = width > 900 ? 1.8 : width > 640 ? 0.7 : 0
    renderOnce()
  }

  function onPointerMove(event: PointerEvent) {
    const rect = container.getBoundingClientRect()
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    pointer.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1)
  }

  function onPointerLeave() {
    pointer.x = 0
    pointer.y = 0
  }

  const resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(container)
  container.addEventListener('pointermove', onPointerMove)
  container.addEventListener('pointerleave', onPointerLeave)
  resize()
  start()

  return {
    syncPalette() {
      palette = readPalette(container)
      coreMaterial.color.copy(palette.primary)
      shellMaterial.color.copy(palette.primary)
      coreGlowMaterial.color.copy(palette.primary)
      seedMaterial.color.copy(palette.seed)
      loopMaterial.color.copy(palette.line)
      ringMaterial.color.copy(palette.secondary)
      ring2Material.color.copy(palette.tone3)
      starMaterial.color.copy(palette.ink)
      const next = [palette.primary, palette.secondary, palette.accent]
      nodeMaterials.forEach((material, i) => material.color.copy(next[i]))
      nodeGlowMaterials.forEach((material, i) => material.color.copy(next[i]))
      paintFlow()
      if (paused || reduced) renderOnce()
    },
    setReducedMotion(value: boolean) {
      reduced = value
      if (reduced) {
        stop()
        group.rotation.set(0, 0, 0)
        camera.position.set(0, 0.4, 7.4)
        camera.lookAt(0, 0, 0)
        placeFlow(0)
        placeNodes(0)
        renderOnce()
      } else {
        start()
      }
    },
    setPaused(value: boolean) {
      paused = value
      if (paused) stop()
      else start()
    },
    destroy() {
      stop()
      resizeObserver.disconnect()
      container.removeEventListener('pointermove', onPointerMove)
      container.removeEventListener('pointerleave', onPointerLeave)
      disposables.forEach((item) => item.dispose())
      renderer.dispose()
      renderer.forceContextLoss()
      renderer.domElement.remove()
    },
  }
}
