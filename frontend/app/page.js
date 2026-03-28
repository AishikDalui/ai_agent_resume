import Script from "next/script";

import { indexMarkup } from "../app_components/legacyMarkup";

export default function HomePage() {
  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: indexMarkup }} />
      <Script
        id="three-bg-init"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{
          __html: `
(function() {
  var canvas = document.getElementById('bg-canvas');
  if (!canvas || typeof THREE === 'undefined') {
    if (canvas) canvas.style.display = 'none';
    return;
  }

  var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 30;

  var PARTICLE_COUNT = 180;
  var positions = new Float32Array(PARTICLE_COUNT * 3);
  var velocities = [];
  var SPREAD = 50;

  for (var i = 0; i < PARTICLE_COUNT; i++) {
    positions[i * 3]     = (Math.random() - 0.5) * SPREAD;
    positions[i * 3 + 1] = (Math.random() - 0.5) * SPREAD;
    positions[i * 3 + 2] = (Math.random() - 0.5) * SPREAD * 0.5;
    velocities.push({
      x: (Math.random() - 0.5) * 0.008,
      y: (Math.random() - 0.5) * 0.008,
      z: (Math.random() - 0.5) * 0.004
    });
  }

  var geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

  var material = new THREE.PointsMaterial({
    color: 0x00f0ff,
    size: 0.12,
    transparent: true,
    opacity: 0.7,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  var points = new THREE.Points(geometry, material);
  scene.add(points);

  var lineGeometry = new THREE.BufferGeometry();
  var MAX_LINES = PARTICLE_COUNT * 6;
  var linePositions = new Float32Array(MAX_LINES * 6);
  lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
  lineGeometry.setDrawRange(0, 0);

  var lineMaterial = new THREE.LineBasicMaterial({
    color: 0x00f0ff,
    transparent: true,
    opacity: 0.08,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  var lines = new THREE.LineSegments(lineGeometry, lineMaterial);
  scene.add(lines);

  var mouseX = 0, mouseY = 0;
  document.addEventListener('mousemove', function(e) {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  window.addEventListener('resize', function() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  var CONNECTION_DIST = 8;
  function animate() {
    requestAnimationFrame(animate);
    var posArr = geometry.attributes.position.array;

    for (var i = 0; i < PARTICLE_COUNT; i++) {
      posArr[i*3]   += velocities[i].x;
      posArr[i*3+1] += velocities[i].y;
      posArr[i*3+2] += velocities[i].z;
      var halfSpread = SPREAD / 2;
      if (Math.abs(posArr[i*3])     > halfSpread) velocities[i].x *= -1;
      if (Math.abs(posArr[i*3+1]) > halfSpread) velocities[i].y *= -1;
      if (Math.abs(posArr[i*3+2]) > halfSpread * 0.5) velocities[i].z *= -1;
    }
    geometry.attributes.position.needsUpdate = true;

    var lineIdx = 0;
    for (var i = 0; i < PARTICLE_COUNT && lineIdx < MAX_LINES; i++) {
      for (var j = i + 1; j < PARTICLE_COUNT && lineIdx < MAX_LINES; j++) {
        var dx = posArr[i*3] - posArr[j*3];
        var dy = posArr[i*3+1] - posArr[j*3+1];
        var dz = posArr[i*3+2] - posArr[j*3+2];
        var dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
        if (dist < CONNECTION_DIST) {
          linePositions[lineIdx*6]   = posArr[i*3];
          linePositions[lineIdx*6+1] = posArr[i*3+1];
          linePositions[lineIdx*6+2] = posArr[i*3+2];
          linePositions[lineIdx*6+3] = posArr[j*3];
          linePositions[lineIdx*6+4] = posArr[j*3+1];
          linePositions[lineIdx*6+5] = posArr[j*3+2];
          lineIdx++;
        }
      }
    }
    lineGeometry.setDrawRange(0, lineIdx * 2);
    lineGeometry.attributes.position.needsUpdate = true;

    camera.position.x += (mouseX * 3 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 3 - camera.position.y) * 0.02;
    camera.lookAt(scene.position);

    points.rotation.y += 0.0004;
    lines.rotation.y += 0.0004;

    renderer.render(scene, camera);
  }
  animate();

  /* Scroll animations */
  var animatedEls = document.querySelectorAll('.animate-on-scroll');
  if (animatedEls.length > 0 && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    animatedEls.forEach(function(el) { observer.observe(el); });
  } else {
    animatedEls.forEach(function(el) { el.classList.add('is-visible'); });
  }
})();
          `,
        }}
      />
      <Script src="/app.js" strategy="afterInteractive" />
    </>
  );
}
