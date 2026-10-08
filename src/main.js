import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.22;

const scene = new THREE.Scene();
const skyColor = 0x3bb8f2;
scene.background = new THREE.Color(skyColor);
scene.fog = new THREE.Fog(skyColor, 70, 200); // fog tipis biru

const camera = new THREE.PerspectiveCamera(38, innerWidth / innerHeight, 0.1, 600);
camera.position.set(36, 27, 40);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxPolarAngle = Math.PI * 0.45;
controls.minDistance = 12;
controls.maxDistance = 110;
controls.target.set(0, 2.5, 0);

// --- CAHAYA (hemisphere langit biru + tanah hijau kekuningan, sun hangat) ---
scene.add(new THREE.AmbientLight(0xffffff, 0.35));
scene.add(new THREE.HemisphereLight(0xcfe8ff, 0xa8b06a, 0.75));
const sun = new THREE.DirectionalLight(0xffe7c4, 2.0);
sun.position.set(25, 40, -15);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -35; sun.shadow.camera.right = 35;
sun.shadow.camera.top = 35; sun.shadow.camera.bottom = -35;
sun.shadow.camera.far = 150;
sun.shadow.bias = -0.0005;
scene.add(sun);

// --- AIR ---
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(500, 500).rotateX(-Math.PI / 2),
  new THREE.MeshBasicMaterial({ color: 0x1472a1 })
);
floor.position.y = -5;
scene.add(floor);

const waterGeo = new THREE.PlaneGeometry(500, 500, 90, 90);
waterGeo.rotateX(-Math.PI / 2);
const water = new THREE.Mesh(waterGeo, new THREE.MeshPhysicalMaterial({
  color: 0x2fa9e0, transmission: 0.4, opacity: 1, transparent: true,
  roughness: 0.15, ior: 1.2,
}));
water.receiveShadow = true;
water.position.y = 0.4;
scene.add(water);
const waterBase = waterGeo.attributes.position.array.slice();

// --- PULAU V3 DARI BLENDER (vertex color, tanpa rotasi) ---
const uTime = { value: 0 };
function swayify(material, amp) {
  material.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = uTime;
    sh.vertexShader = 'uniform float uTime;\n' + sh.vertexShader.replace(
      '#include <begin_vertex>',
      `#include <begin_vertex>
      {
        vec4 wp4 = modelMatrix * vec4(position, 1.0);
        float ph = wp4.x * 1.7 + wp4.z * 2.3;
        float k = smoothstep(-1.0, 1.5, position.y);
        transformed.x += sin(uTime * 1.7 + ph) * ${amp} * k;
        transformed.z += cos(uTime * 1.3 + ph * 1.3) * ${(amp * 0.7).toFixed(3)} * k;
      }`
    );
  };
  material.customProgramCacheKey = () => 'sway' + amp;
  return material;
}

const loaderEl = document.getElementById('loader');
const islandGroup = new THREE.Group();
scene.add(islandGroup);
const boatGroup = new THREE.Group();
scene.add(boatGroup);

new GLTFLoader().load(
  `${import.meta.env.BASE_URL}sunlit_shores_v3.glb`,
  (gltf) => {
    const swayCanopy = new Map();
    const boatParts = [];
    gltf.scene.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = true;
      o.receiveShadow = true;
      const m = o.material;
      if (m) m.vertexColors = true; // warna dari Blender vertex color
      const n = o.name;
      // kelompokkan perahu (attach SETELAH traverse agar iterasi aman)
      if (n.startsWith('Boat_')) { boatParts.push(o); return; }
      // material goyang untuk tajuk/semak/bunga/layar
      let amp = 0;
      if (n.includes('_canopy')) amp = 0.09;
      else if (n === 'Bush') amp = 0.05;
      else if (n.includes('Flower')) amp = 0.04;
      if (amp > 0) {
        if (!swayCanopy.has(amp)) {
          const c = m.clone();
          c.vertexColors = true;
          swayify(c, amp);
          swayCanopy.set(amp, c);
        }
        o.material = swayCanopy.get(amp);
      }
    });
    islandGroup.add(gltf.scene);
    boatParts.forEach((o) => boatGroup.attach(o));
    if (loaderEl) loaderEl.style.display = 'none';
  },
  undefined,
  (err) => {
    console.error('GLB gagal dimuat:', err);
    if (loaderEl) loaderEl.innerHTML = '<span>Gagal memuat pulau. Jalankan npm run dev.</span>';
  }
);

// --- FOAM di tepi pulau (Blender x,y -> three x,-y) ---
const foamTexC = document.createElement('canvas');
foamTexC.width = 128; foamTexC.height = 8;
{
  const ctx = foamTexC.getContext('2d');
  ctx.clearRect(0, 0, 128, 8);
  ctx.fillStyle = '#ffffff';
  for (let i = 0; i < 16; i++) ctx.fillRect(i * 8, 0, 5, 8);
}
const foamDash = new THREE.CanvasTexture(foamTexC);
foamDash.wrapS = foamDash.wrapT = THREE.RepeatWrapping;
foamDash.repeat.set(10, 1);
const foams = [];
[
  [0, 0, 5.5], [7.5, -2, 4.2], [-6.5, 1, 4.2],
  [-1.5, 6.5, 4.5], [4.5, 5, 3.2], [-3, -5.5, 4.0],
].forEach(([x, z, r], i) => {
  const g = new THREE.Group();
  const solid = new THREE.Mesh(
    new THREE.RingGeometry(r * 0.98, r * 1.22, 48).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.28, depthWrite: false })
  );
  const dash = new THREE.Mesh(
    new THREE.RingGeometry(r * 1.0, r * 1.14, 48).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ map: foamDash.clone(), transparent: true, opacity: 0.5, depthWrite: false, side: THREE.DoubleSide })
  );
  dash.material.map.needsUpdate = true;
  g.add(solid, dash);
  g.position.set(x, 0.55, z);
  g.userData = { phase: i * 1.3, dash };
  scene.add(g);
  foams.push(g);
});

// --- AWAN ---
const clouds = new THREE.Group();
const matCloud = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, emissive: 0xffffff, emissiveIntensity: 0.35 });
for (let i = 0; i < 10; i++) {
  const c = new THREE.Group();
  for (let j = 0; j < 5; j++) {
    const puff = new THREE.Mesh(new THREE.SphereGeometry(1.5 + Math.random() * 1.5, 14, 14), matCloud);
    puff.position.set((Math.random() - 0.5) * 4, (Math.random() - 0.5) * 1.5, (Math.random() - 0.5) * 4);
    puff.castShadow = true;
    c.add(puff);
  }
  c.position.set((Math.random() - 0.5) * 130, 22 + Math.random() * 10, (Math.random() - 0.5) * 130);
  c.userData = { speed: 0.3 + Math.random() * 0.5 };
  clouds.add(c);
}
scene.add(clouds);

// --- PARTIKEL ---
const particleGeo = new THREE.BufferGeometry();
const pCount = 180;
const pPos = new Float32Array(pCount * 3);
const pSpeed = new Float32Array(pCount);
for (let i = 0; i < pCount; i++) {
  pPos[i * 3] = (Math.random() - 0.5) * 55;
  pPos[i * 3 + 1] = Math.random() * 20;
  pPos[i * 3 + 2] = (Math.random() - 0.5) * 55;
  pSpeed[i] = 0.2 + Math.random() * 0.8;
}
particleGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
particleGeo.setAttribute('speed', new THREE.BufferAttribute(pSpeed, 1));
const pCanvas = document.createElement('canvas'); pCanvas.width = 64; pCanvas.height = 64;
{
  const ctx = pCanvas.getContext('2d');
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.25, 'rgba(255,240,150,0.8)');
  g.addColorStop(1, 'rgba(255,240,150,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 64, 64);
}
scene.add(new THREE.Points(particleGeo, new THREE.PointsMaterial({
  size: 1.0, map: new THREE.CanvasTexture(pCanvas), transparent: true,
  depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.65,
})));

// --- POST-PROCESSING: SSAO + Bloom halus + grading hangat ---
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const ssao = new SSAOPass(scene, camera, innerWidth / 2, innerHeight / 2);
ssao.kernelRadius = 8;
ssao.minDistance = 0.01;
ssao.maxDistance = 0.35;
composer.addPass(ssao);
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.28, 0.55, 0.85);
composer.addPass(bloom);
const GradeShader = {
  uniforms: { tDiffuse: { value: null }, uWarm: { value: 0.10 }, uSat: { value: 1.07 }, uVig: { value: 0.16 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float uWarm, uSat, uVig; varying vec2 vUv;
    void main(){
      vec4 c = texture2D(tDiffuse, vUv);
      float l = dot(c.rgb, vec3(0.299, 0.587, 0.114));
      c.rgb = mix(vec3(l), c.rgb, uSat);
      c.rgb *= vec3(1.0 + uWarm, 1.0 + uWarm * 0.4, 1.0 - uWarm * 0.6);
      float d = distance(vUv, vec2(0.5));
      c.rgb *= 1.0 - uVig * smoothstep(0.45, 0.9, d);
      gl_FragColor = c;
    }`,
};
composer.addPass(new ShaderPass(GradeShader));
composer.addPass(new OutputPass());

// --- LOOP ---
const clock = new THREE.Clock();
const ease = (s) => s * s * (3 - 2 * s);
function animate() {
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  const dt = Math.min(clock.getDelta(), 0.05);
  uTime.value = t;

  const pos = waterGeo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = waterBase[i * 3], y = waterBase[i * 3 + 1];
    pos.setZ(i, Math.sin(x * 0.35 + t * 1.2) * 0.35 + Math.cos(y * 0.35 + t * 0.9) * 0.35);
  }
  pos.needsUpdate = true;
  waterGeo.computeVertexNormals();

  islandGroup.position.y = Math.sin(t * 0.6) * 0.12;

  // perahu naik-turun dengan easing + oleng lembut
  const b = ease(0.5 + 0.5 * Math.sin(t * 1.1));
  boatGroup.position.y = (b - 0.5) * 0.5;
  boatGroup.rotation.z = Math.sin(t * 0.9) * 0.05;
  boatGroup.rotation.x = Math.cos(t * 0.7) * 0.04;

  // foam berdenyut + garis putus berputar
  foams.forEach((f) => {
    f.children[0].material.opacity = 0.22 + 0.12 * Math.sin(t * 1.4 + f.userData.phase);
    f.userData.dash.material.map.offset.x -= dt * 0.06;
    f.userData.dash.material.opacity = 0.4 + 0.2 * Math.sin(t * 1.4 + f.userData.phase + 1);
  });

  const pp = particleGeo.attributes.position;
  const speeds = particleGeo.attributes.speed.array;
  for (let i = 0; i < pCount; i++) {
    pp.array[i * 3 + 1] += speeds[i] * dt;
    pp.array[i * 3] += Math.sin(t + i) * 0.01;
    pp.array[i * 3 + 2] += Math.cos(t + i) * 0.01;
    if (pp.array[i * 3 + 1] > 25) pp.array[i * 3 + 1] = 0;
  }
  pp.needsUpdate = true;

  clouds.children.forEach((c) => {
    c.position.x += c.userData.speed * dt;
    if (c.position.x > 85) c.position.x = -85;
  });

  controls.update();
  composer.render();
}
animate();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
});
