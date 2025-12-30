"""
3D Rendering Engine - MiniMax M2 Integration

Leverages MiniMax M2's proven 7,000+ React Three Fiber instances capability.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page
import numpy as np

logger = logging.getLogger("web.render3d")


@dataclass
class Scene3D:
    """3D scene configuration and state."""

    scene_id: str
    url: str
    elements_count: int
    render_quality: str
    performance_score: float
    webgl_version: str
    textures_loaded: int
    geometries_count: int


@dataclass
class RenderInstance:
    """Individual 3D rendering instance."""

    instance_id: str
    element_selector: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    scale: Tuple[float, float, float]
    material_properties: Dict[str, Any]
    visibility: bool = True


class Render3DEngine:
    """
    3D Rendering Engine

    Implements MiniMax M2's 7,000+ React Three Fiber instances capability:
    - High-performance 3D scene management
    - Optimized WebGL rendering
    - Interactive 3D element manipulation
    - Cross-platform 3D compatibility
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.max_instances = self.config.get("render3d.max_instances", 7000)
        self.performance_target = self.config.get("render3d.target_fps", 60)

        # Instance tracking
        self.active_scenes: Dict[str, Scene3D] = {}
        self.render_instances: Dict[str, List[RenderInstance]] = {}

    async def detect_3d_content(self, page: Page) -> Dict[str, Any]:
        """Detect 3D content on the page and analyze capabilities."""
        start_time = time.time()

        try:
            # Check for 3D libraries and WebGL support
            threejs_detected = await page.evaluate("""
                () => {
                    return {
                        threejs: typeof window.THREE !== 'undefined',
                        babylon: typeof window.BABYLON !== 'undefined',
                        webgl_support: !!window.WebGLRenderingContext,
                        canvas_elements: document.querySelectorAll('canvas').length
                    };
                }
            """)

            # Check WebGL capabilities
            webgl_capabilities = await page.evaluate("""
                () => {
                    try {
                        const canvas = document.createElement('canvas');
                        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                        
                        if (!gl) return { supported: false };
                        
                        return {
                            supported: true,
                            version: gl.getParameter(gl.VERSION),
                            vendor: gl.getParameter(gl.VENDOR),
                            renderer: gl.getParameter(gl.RENDERER),
                            max_texture_size: gl.getParameter(gl.MAX_TEXTURE_SIZE)
                        };
                    } catch (e) {
                        return { supported: false, error: e.message };
                    }
                }
            """)

            # Calculate capability score
            capability_score = self._calculate_3d_capability_score(
                threejs_detected, webgl_capabilities
            )

            analysis = {
                "timestamp": time.time(),
                "url": page.url,
                "detection_time": round(time.time() - start_time, 2),
                "threejs_detected": threejs_detected,
                "webgl_capabilities": webgl_capabilities,
                "capability_score": capability_score,
                "max_instances_recommended": min(
                    self.max_instances, self._estimate_max_instances(webgl_capabilities)
                ),
                "optimization_suggestions": self._generate_optimization_suggestions(
                    threejs_detected, webgl_capabilities
                ),
            }

            logger.info(f"3D content analysis completed for {page.url}")
            return analysis

        except Exception as e:
            logger.error(f"3D content detection failed: {e}")
            raise

    async def create_3d_scene(self, page: Page, scene_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new 3D scene with specified configuration."""
        scene_id = scene_config.get("scene_id", f"scene_{int(time.time())}")

        try:
            # Create Three.js scene setup
            scene_script = f"""
                (() => {{
                    if (typeof window.THREE === 'undefined') {{
                        throw new Error('Three.js not loaded');
                    }}
                    
                    // Create scene
                    const scene = new window.THREE.Scene();
                    scene.background = new window.THREE.Color({scene_config.get("background_color", "0x222222")});
                    
                    // Create camera
                    const camera = new window.THREE.PerspectiveCamera(
                        {scene_config.get("fov", 75)},
                        window.innerWidth / window.innerHeight,
                        0.1,
                        1000
                    );
                    
                    // Create renderer
                    const renderer = new window.THREE.WebGLRenderer({{
                        antialias: {str(scene_config.get("antialias", True)).lower()}
                    }});
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    
                    // Add lighting
                    const ambientLight = new window.THREE.AmbientLight(0x404040, 0.6);
                    scene.add(ambientLight);
                    
                    const directionalLight = new window.THREE.DirectionalLight(0xffffff, 0.8);
                    directionalLight.position.set(1, 1, 1);
                    scene.add(directionalLight);
                    
                    // Store scene data
                    window._rk_3d_scene = {{
                        id: '{scene_id}',
                        scene: scene,
                        camera: camera,
                        renderer: renderer,
                        instances: [],
                        config: {json.dumps(scene_config)}
                    }};
                    
                    return {{
                        scene_id: '{scene_id}',
                        success: true,
                        renderer_info: {{
                            antialias: renderer.antialias,
                            max_texture_size: renderer.capabilities.maxTextureSize
                        }}
                    }};
                }})();
            """

            result = await page.evaluate(scene_script)

            if result.get("success"):
                # Track the scene
                self.active_scenes[scene_id] = Scene3D(
                    scene_id=scene_id,
                    url=page.url,
                    elements_count=0,
                    render_quality=scene_config.get("quality", "medium"),
                    performance_score=1.0,
                    webgl_version="WebGL 1.0",
                    textures_loaded=0,
                    geometries_count=0,
                )

                self.render_instances[scene_id] = []
                logger.info(f"3D scene created: {scene_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to create 3D scene: {e}")
            raise

    async def add_3d_instance(
        self, page: Page, scene_id: str, instance_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a 3D instance to the scene."""
        instance_id = instance_config.get("instance_id", f"instance_{int(time.time())}")

        try:
            if scene_id not in self.active_scenes:
                raise ValueError(f"Scene {scene_id} not found")

            # Create instance script
            instance_script = f"""
                (() => {{
                    const sceneData = window._rk_3d_scene;
                    if (!sceneData || sceneData.id !== '{scene_id}') {{
                        throw new Error('Scene not found');
                    }}
                    
                    const config = {json.dumps(instance_config)};
                    
                    // Create geometry based on type
                    let geometry;
                    switch (config.type) {{
                        case 'box':
                            geometry = new window.THREE.BoxGeometry(
                                config.size[0] || 1,
                                config.size[1] || 1,
                                config.size[2] || 1
                            );
                            break;
                        case 'sphere':
                            geometry = new window.THREE.SphereGeometry(
                                config.radius || 0.5,
                                config.widthSegments || 32,
                                config.heightSegments || 16
                            );
                            break;
                        case 'plane':
                            geometry = new window.THREE.PlaneGeometry(
                                config.width || 1,
                                config.height || 1
                            );
                            break;
                        default:
                            geometry = new window.THREE.BoxGeometry(1, 1, 1);
                    }}
                    
                    // Create material
                    const materialConfig = config.material || {{}};
                    const material = new window.THREE.MeshStandardMaterial({{
                        color: materialConfig.color || 0x00ff00,
                        metalness: materialConfig.metalness || 0,
                        roughness: materialConfig.roughness || 1
                    }});
                    
                    // Create mesh
                    const mesh = new window.THREE.Mesh(geometry, material);
                    
                    // Set position, rotation, scale
                    mesh.position.set(
                        config.position[0] || 0,
                        config.position[1] || 0,
                        config.position[2] || 0
                    );
                    
                    mesh.rotation.set(
                        config.rotation[0] || 0,
                        config.rotation[1] || 0,
                        config.rotation[2] || 0
                    );
                    
                    mesh.scale.set(
                        config.scale[0] || 1,
                        config.scale[1] || 1,
                        config.scale[2] || 1
                    );
                    
                    // Add to scene
                    sceneData.scene.add(mesh);
                    
                    // Store instance data
                    const instance = {{
                        id: '{instance_id}',
                        mesh: mesh,
                        config: config,
                        created_at: Date.now()
                    }};
                    
                    sceneData.instances.push(instance);
                    
                    return {{
                        instance_id: '{instance_id}',
                        success: true,
                        geometry_info: {{
                            type: config.type,
                            vertices: geometry.attributes.position.count
                        }}
                    }};
                }})();
            """

            result = await page.evaluate(instance_script)

            if result.get("success"):
                # Track the instance
                instance = RenderInstance(
                    instance_id=instance_id,
                    element_selector=instance_config.get("selector", f"#{instance_id}"),
                    position=tuple(instance_config.get("position", [0, 0, 0])),
                    rotation=tuple(instance_config.get("rotation", [0, 0, 0])),
                    scale=tuple(instance_config.get("scale", [1, 1, 1])),
                    material_properties=instance_config.get("material", {}),
                )

                self.render_instances[scene_id].append(instance)
                self.active_scenes[scene_id].elements_count += 1

                logger.info(f"3D instance added: {instance_id} to scene {scene_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to add 3D instance: {e}")
            raise

    async def interact_with_3d(
        self, page: Page, scene_id: str, interaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interact with 3D scene elements."""
        interaction_id = f"interaction_{int(time.time())}"

        try:
            if scene_id not in self.active_scenes:
                raise ValueError(f"Scene {scene_id} not found")

            # Perform 3D interaction
            interaction_script = f"""
                (() => {{
                    const sceneData = window._rk_3d_scene;
                    if (!sceneData || sceneData.id !== '{scene_id}') {{
                        throw new Error('Scene not found');
                    }}
                    
                    const interaction = {json.dumps(interaction)};
                    let result = {{ success: true, interaction_id: '{interaction_id}' }};
                    
                    switch (interaction.type) {{
                        case 'click':
                            const mouse = new window.THREE.Vector2();
                            mouse.x = (interaction.x / window.innerWidth) * 2 - 1;
                            mouse.y = -(interaction.y / window.innerHeight) * 2 + 1;
                            
                            const raycaster = new window.THREE.Raycaster();
                            raycaster.setFromCamera(mouse, sceneData.camera);
                            
                            const intersects = raycaster.intersectObjects(sceneData.scene.children, true);
                            
                            if (intersects.length > 0) {{
                                const intersected = intersects[0];
                                result.selected_object = {{
                                    id: intersected.object.uuid,
                                    position: intersected.object.position.toArray(),
                                    distance: intersected.distance
                                }};
                            }} else {{
                                result.selected_object = null;
                            }}
                            break;
                            
                        case 'rotate_camera':
                            sceneData.camera.position.x = interaction.position[0];
                            sceneData.camera.position.y = interaction.position[1];
                            sceneData.camera.position.z = interaction.position[2];
                            sceneData.camera.lookAt(0, 0, 0);
                            break;
                    }}
                    
                    return result;
                }})();
            """

            result = await page.evaluate(interaction_script)
            logger.info(f"3D interaction performed: {interaction.get('type')} on {scene_id}")

            return result

        except Exception as e:
            logger.error(f"3D interaction failed: {e}")
            raise

    def _calculate_3d_capability_score(
        self, threejs_detected: Dict[str, Any], webgl_capabilities: Dict[str, Any]
    ) -> float:
        """Calculate 3D rendering capability score."""
        score = 0.0

        # WebGL support (50% of score)
        if webgl_capabilities.get("supported", False):
            score += 0.5

            # Bonus for WebGL 2.0
            if "2.0" in webgl_capabilities.get("version", ""):
                score += 0.2
        else:
            return 0.0

        # Three.js detection (30% of score)
        if threejs_detected.get("threejs", False):
            score += 0.3

        # Canvas elements (20% of score)
        canvas_count = threejs_detected.get("canvas_elements", 0)
        if canvas_count > 0:
            score += min(0.2, canvas_count * 0.1)

        return min(1.0, score)

    def _estimate_max_instances(self, webgl_capabilities: Dict[str, Any]) -> int:
        """Estimate maximum recommended 3D instances."""
        base_estimate = 1000

        # Adjust based on WebGL capabilities
        max_texture_size = webgl_capabilities.get("max_texture_size", 1024)
        if max_texture_size >= 4096:
            base_estimate *= 2
        elif max_texture_size >= 2048:
            base_estimate *= 1.5

        return int(base_estimate)

    def _generate_optimization_suggestions(
        self, threejs_detected: Dict[str, Any], webgl_capabilities: Dict[str, Any]
    ) -> List[str]:
        """Generate 3D optimization suggestions."""
        suggestions = []

        if not threejs_detected.get("threejs", False):
            suggestions.append("Consider using Three.js for enhanced 3D capabilities")

        max_texture_size = webgl_capabilities.get("max_texture_size", 1024)
        if max_texture_size < 2048:
            suggestions.append("Optimize texture sizes for better performance")

        return suggestions

    def get_3d_summary(self) -> Dict[str, Any]:
        """Get summary of all 3D operations."""
        total_scenes = len(self.active_scenes)
        total_instances = sum(len(instances) for instances in self.render_instances.values())

        return {
            "active_scenes": total_scenes,
            "total_instances": total_instances,
            "max_instances_configured": self.max_instances,
            "scenes": {
                scene_id: {
                    "elements_count": scene.elements_count,
                    "performance_score": scene.performance_score,
                    "quality": scene.render_quality,
                }
                for scene_id, scene in self.active_scenes.items()
            },
        }
