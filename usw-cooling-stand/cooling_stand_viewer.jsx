import { useState, useRef, useEffect } from "react";
import * as THREE from "three";

const COLORS = {
  legs: "#4682B4",
  shelf: "#E8922A",
  posts: "#D4831F",
  cradle: "#E8922A",
  lip: "#FF6B35",
  switch: "rgba(100,200,100,0.3)",
  fan: "#333",
};

export default function CoolingStandViewer() {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const isDragging = useRef(false);
  const lastMouse = useRef({ x: 0, y: 0 });
  const rotation = useRef({ x: -0.4, y: 0.5 });
  const zoomRef = useRef(500);
  const [showSwitch, setShowSwitch] = useState(true);
  const [cableGap, setCableGap] = useState(50);
  const [lipSize, setLipSize] = useState(10);
  const [wallHeight, setWallHeight] = useState(70);

  useEffect(() => {
    const mount = mountRef.current;
    const w = mount.clientWidth;
    const h = mount.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f5f0);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, w / h, 1, 2000);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(window.devicePixelRatio);
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lights
    const amb = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(amb);
    const dir1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dir1.position.set(200, 400, 300);
    scene.add(dir1);
    const dir2 = new THREE.DirectionalLight(0xffffff, 0.3);
    dir2.position.set(-200, 200, -100);
    scene.add(dir2);

    // Grid
    const grid = new THREE.GridHelper(400, 20, 0xcccccc, 0xeeeeee);
    scene.add(grid);

    return () => {
      mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    // Clear old meshes (keep lights and grid)
    const toRemove = [];
    scene.traverse((obj) => {
      if (obj.isMesh) toRemove.push(obj);
    });
    toRemove.forEach((obj) => {
      obj.geometry.dispose();
      obj.material.dispose();
      scene.remove(obj);
    });

    // Dimensions
    const SW_W = 210.4;
    const SW_T = 43.7;
    const SW_H = 173.8;
    const FAN = 80;
    const RAIL_DEPTH = 8;
    const RAIL_OFFSET = 59;
    const PLAT_W = SW_W + 16; // 226
    const PLAT_D = FAN + 20; // 100
    const FLOOR_CLEAR = 155;
    const SHELF_Z = 165;
    const SHELF_T = 5;
    const WALL = 4;
    const CLR = 1.5;
    const SLOT_W = SW_T + CLR * 2;
    const LEG_W = 30;
    const LEG_X = PLAT_W / 2 - LEG_W / 2 - 4;

    const CRADLE_Z = SHELF_Z + SHELF_T + cableGap;

    function box(w, d, h, color, x, y, z, edges = true) {
      const geo = new THREE.BoxGeometry(w, h, d);
      const mat = new THREE.MeshPhongMaterial({
        color,
        transparent: color === "rgba(100,200,100,0.3)",
        opacity: color === "rgba(100,200,100,0.3)" ? 0.25 : 1,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, z + h / 2, y);
      scene.add(mesh);

      if (edges && color !== "rgba(100,200,100,0.3)") {
        const edgeGeo = new THREE.EdgesGeometry(geo);
        const edgeMat = new THREE.LineBasicMaterial({
          color: 0x000000,
          transparent: true,
          opacity: 0.15,
        });
        const line = new THREE.LineSegments(edgeGeo, edgeMat);
        line.position.copy(mesh.position);
        scene.add(line);
      }
      return mesh;
    }

    function cyl(r, h, color, x, y, z) {
      const geo = new THREE.CylinderGeometry(r, r, h, 32);
      const mat = new THREE.MeshPhongMaterial({ color });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, z + h / 2, y);
      scene.add(mesh);
      return mesh;
    }

    // === FLOOR RAILS ===
    for (const s of [-1, 1]) {
      box(PLAT_W, RAIL_DEPTH, 4, COLORS.legs, 0, s * RAIL_OFFSET, 0);
    }

    // === 4 LEGS ===
    for (const lx of [-LEG_X, LEG_X]) {
      for (const s of [-1, 1]) {
        box(LEG_W, RAIL_DEPTH, FLOOR_CLEAR, COLORS.legs, lx, s * RAIL_OFFSET, 0);
      }
    }

    // === BRACE ===
    const braceZ = FLOOR_CLEAR + (SHELF_Z - SHELF_T - FLOOR_CLEAR) / 2;
    for (const lx of [-LEG_X, LEG_X]) {
      box(4, RAIL_OFFSET * 2, 10, COLORS.shelf, lx, 0, braceZ);
    }

    // === FAN SHELF ===
    box(PLAT_W, PLAT_D, SHELF_T, COLORS.shelf, 0, 0, SHELF_Z - SHELF_T);

    // Fan holes (dark circles)
    const fanGap = 10;
    for (const fx of [-(FAN / 2 + fanGap / 2), FAN / 2 + fanGap / 2]) {
      cyl(FAN / 2 - 2, SHELF_T + 1, COLORS.fan, fx, 0, SHELF_Z - SHELF_T - 0.5);
    }

    // === CORNER POSTS (cable gap) ===
    const POST = 8;
    for (const dx of [-1, 1]) {
      for (const dy of [-1, 1]) {
        box(
          POST,
          POST,
          cableGap,
          COLORS.posts,
          dx * (SW_W / 2),
          dy * (SLOT_W / 2 + WALL / 2),
          SHELF_Z
        );
      }
    }

    // === CRADLE ===
    // Front wall
    box(
      SW_W + 10,
      WALL,
      wallHeight,
      COLORS.cradle,
      0,
      -(SLOT_W / 2 + WALL / 2),
      CRADLE_Z
    );
    // Back wall
    box(
      SW_W + 10,
      WALL,
      wallHeight,
      COLORS.cradle,
      0,
      SLOT_W / 2 + WALL / 2,
      CRADLE_Z
    );

    // Front lip
    box(
      SW_W + 10,
      lipSize,
      WALL,
      COLORS.lip,
      0,
      -(SLOT_W / 2 - lipSize / 2),
      CRADLE_Z
    );
    // Back lip
    box(
      SW_W + 10,
      lipSize,
      WALL,
      COLORS.lip,
      0,
      SLOT_W / 2 - lipSize / 2,
      CRADLE_Z
    );

    // End stops
    for (const dx of [-1, 1]) {
      box(
        WALL,
        SLOT_W + WALL * 2,
        8,
        COLORS.cradle,
        dx * (SW_W / 2 + CLR + WALL / 2),
        0,
        CRADLE_Z
      );
    }

    // === GHOST SWITCH ===
    if (showSwitch) {
      box(
        SW_W,
        SW_T,
        SW_H,
        COLORS.switch,
        0,
        0,
        CRADLE_Z + WALL
      );
    }

    render();
  }, [showSwitch, cableGap, lipSize, wallHeight]);

  function render() {
    const scene = sceneRef.current;
    const camera = cameraRef.current;
    const renderer = rendererRef.current;
    if (!scene || !camera || !renderer) return;

    const dist = zoomRef.current;
    camera.position.x = dist * Math.sin(rotation.current.y) * Math.cos(rotation.current.x);
    camera.position.y = dist * Math.sin(-rotation.current.x) + 150;
    camera.position.z = dist * Math.cos(rotation.current.y) * Math.cos(rotation.current.x);
    camera.lookAt(0, 150, 0);
    renderer.render(scene, camera);
  }

  function onPointerDown(e) {
    isDragging.current = true;
    lastMouse.current = { x: e.clientX, y: e.clientY };
  }
  function onPointerMove(e) {
    if (!isDragging.current) return;
    const dx = e.clientX - lastMouse.current.x;
    const dy = e.clientY - lastMouse.current.y;
    rotation.current.y += dx * 0.01;
    rotation.current.x += dy * 0.01;
    rotation.current.x = Math.max(-1.2, Math.min(1.2, rotation.current.x));
    lastMouse.current = { x: e.clientX, y: e.clientY };
    render();
  }
  function onPointerUp() {
    isDragging.current = false;
  }
  function onWheel(e) {
    zoomRef.current = Math.max(200, Math.min(1000, zoomRef.current + e.deltaY * 0.5));
    render();
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="p-3 bg-white border-b shadow-sm">
        <h1 className="text-lg font-bold text-gray-800 mb-2">
          USW-Pro-XG-8-PoE Cooling Stand
        </h1>
        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showSwitch}
              onChange={(e) => setShowSwitch(e.target.checked)}
            />
            Show switch (ghost)
          </label>
          <label className="flex items-center gap-2">
            Cable gap:
            <input
              type="range"
              min={20}
              max={80}
              value={cableGap}
              onChange={(e) => setCableGap(Number(e.target.value))}
              className="w-24"
            />
            {cableGap}mm
          </label>
          <label className="flex items-center gap-2">
            Lip size:
            <input
              type="range"
              min={5}
              max={20}
              value={lipSize}
              onChange={(e) => setLipSize(Number(e.target.value))}
              className="w-24"
            />
            {lipSize}mm
          </label>
          <label className="flex items-center gap-2">
            Wall height:
            <input
              type="range"
              min={30}
              max={120}
              value={wallHeight}
              onChange={(e) => setWallHeight(Number(e.target.value))}
              className="w-24"
            />
            {wallHeight}mm
          </label>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Drag to rotate · Scroll to zoom · Orange lips = switch rests here
        </p>
      </div>
      <div
        ref={mountRef}
        className="flex-1 cursor-grab active:cursor-grabbing"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        onWheel={onWheel}
      />
    </div>
  );
}
