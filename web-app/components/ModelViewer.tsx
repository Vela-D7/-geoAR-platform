"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

/** Three.js GLB viewer for the optimised site model (spec: inspect the asset
 *  without opening Unity). Orbit + zoom; auto-frames the model bounds. */
export default function ModelViewer({ url }: { url: string }) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [detail, setDetail] = useState("");

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a);
    const camera = new THREE.PerspectiveCamera(50, mount.clientWidth / mount.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 1.2));
    const sun = new THREE.DirectionalLight(0xffffff, 1.5);
    sun.position.set(10, 20, 10);
    scene.add(sun);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    let disposed = false;
    new GLTFLoader().load(
      url,
      (gltf) => {
        if (disposed) return;
        const model = gltf.scene;
        // Pipeline exports are Z-up (scan convention); three.js is Y-up.
        model.rotation.x = -Math.PI / 2;
        scene.add(model);

        const box = new THREE.Box3().setFromObject(model);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        const radius = Math.max(size.x, size.y, size.z);
        camera.position.set(center.x + radius, center.y + radius * 0.7, center.z + radius);
        controls.target.copy(center);

        let tris = 0;
        model.traverse((o) => {
          if (o instanceof THREE.Mesh) {
            const geom = o.geometry as THREE.BufferGeometry;
            tris += (geom.index ? geom.index.count : geom.attributes.position.count) / 3;
            (o.material as THREE.MeshStandardMaterial).wireframe = false;
          }
        });
        setDetail(`${Math.round(tris).toLocaleString()} triangles · ${size.x.toFixed(1)}×${size.y.toFixed(1)}×${size.z.toFixed(1)} m`);
        setStatus("ready");
      },
      undefined,
      (err) => {
        setDetail(String(err));
        setStatus("error");
      }
    );

    let raf = 0;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener("resize", onResize);

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [url]);

  return (
    <div>
      <div ref={mountRef} className="h-[420px] w-full rounded-lg border border-slate-800" />
      <p className="mt-2 text-xs text-slate-500">
        {status === "loading" && "Loading model…"}
        {status === "ready" && detail}
        {status === "error" && <span className="text-red-400">Failed to load model: {detail}</span>}
      </p>
    </div>
  );
}
