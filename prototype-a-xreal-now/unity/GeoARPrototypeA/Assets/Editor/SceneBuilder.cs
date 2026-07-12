using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using GeoAR.Anchors;
using GeoAR.Content;
using GeoAR.Localization;
using GeoAR.Logging;

namespace GeoAR.EditorTools
{
    /// <summary>
    /// One-click scene assembly so the scene is reproducible from code review
    /// rather than living only as opaque serialized state. Builds the editor-sim
    /// variant by default; swap EditorSimAnchorProvider + MockSensorProvider for
    /// XrealAnchorProvider + device providers for the glasses build.
    /// </summary>
    public static class SceneBuilder
    {
        [MenuItem("GeoAR/Build Prototype A Scene (Editor Sim)")]
        public static void BuildSimScene()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            var root = new GameObject("GeoAR");

            var anchorProvider = root.AddComponent<EditorSimAnchorProvider>();
            var sensors = root.AddComponent<MockSensorProvider>();
            var logger = root.AddComponent<FieldTestLogger>();
            var anchorManager = root.AddComponent<SpatialAnchorManager>();
            var content = root.AddComponent<HistoricalContentRenderer>();
            var fusion = root.AddComponent<GeoFusionController>();

            Wire(anchorManager, "anchorProviderBehaviour", anchorProvider);
            Wire(fusion, "gpsProviderBehaviour", sensors);
            Wire(fusion, "visualLocalizerBehaviour", sensors);
            Wire(fusion, "anchorManager", anchorManager);
            Wire(fusion, "contentRenderer", content);
            Wire(fusion, "fieldTestLogger", logger);

            // LOD prefabs: imported by glTFast from pipeline output. Assign after
            // copying chapel_lod{0,1,2}.glb into Assets/Models/ (see SceneSetup.md).
            foreach (var (field, path) in new[] {
                ("lod0Prefab", "Assets/Models/chapel_lod0.glb"),
                ("lod1Prefab", "Assets/Models/chapel_lod1.glb"),
                ("lod2Prefab", "Assets/Models/chapel_lod2.glb") })
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefab != null) Wire(content, field, prefab);
                else Debug.LogWarning($"[GeoAR] {path} not found — run the optimisation pipeline and copy LODs into Assets/Models/.");
            }

            EditorSceneManager.SaveScene(scene, "Assets/GeoARPrototypeA_Sim.unity");
            Debug.Log("[GeoAR] Scene built: Assets/GeoARPrototypeA_Sim.unity");
        }

        private static void Wire(Object target, string fieldName, Object value)
        {
            var so = new SerializedObject(target);
            so.FindProperty(fieldName).objectReferenceValue = value;
            so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
