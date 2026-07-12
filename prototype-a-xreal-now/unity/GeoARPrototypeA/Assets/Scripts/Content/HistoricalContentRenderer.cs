using UnityEngine;

namespace GeoAR.Content
{
    /// <summary>
    /// Renders the historical model (LOD0/1/2 from the optimisation pipeline)
    /// aligned to the site anchor pose. LOD GLBs are imported at build time via
    /// glTFast (see Packages/manifest.json) and referenced as prefabs — no
    /// runtime download in the MVP; the signed-URL delivery path from the shared
    /// backend is the post-MVP replacement for these serialized references.
    /// </summary>
    public sealed class HistoricalContentRenderer : MonoBehaviour
    {
        [Header("LOD prefabs from pipeline output (chapel_lod0/1/2.glb)")]
        [SerializeField] private GameObject lod0Prefab;
        [SerializeField] private GameObject lod1Prefab;
        [SerializeField] private GameObject lod2Prefab;

        [Header("LOD switch distances (metres from camera)")]
        [SerializeField] private float lod0MaxDistance = 8f;
        [SerializeField] private float lod1MaxDistance = 25f;

        private GameObject[] _lodInstances;
        private Transform _contentRoot;
        private Camera _arCamera;

        public bool IsVisible => _contentRoot != null && _contentRoot.gameObject.activeSelf;

        private void Awake()
        {
            _arCamera = Camera.main;
            _contentRoot = new GameObject("HistoricalContentRoot").transform;
            _contentRoot.SetParent(transform, worldPositionStays: false);

            _lodInstances = new GameObject[3];
            var prefabs = new[] { lod0Prefab, lod1Prefab, lod2Prefab };
            for (var i = 0; i < prefabs.Length; i++)
            {
                if (prefabs[i] == null) continue;
                _lodInstances[i] = Instantiate(prefabs[i], _contentRoot);
                _lodInstances[i].SetActive(false);
            }
            _contentRoot.gameObject.SetActive(false);
        }

        /// <summary>Align content to the anchor-resolved site pose and show it.</summary>
        public void ShowAt(Pose sitePose)
        {
            _contentRoot.SetPositionAndRotation(sitePose.position, sitePose.rotation);
            _contentRoot.gameObject.SetActive(true);
        }

        /// <summary>Hide content (e.g. NO_CONTENT state, or tracking lost past grace period).</summary>
        public void Hide() => _contentRoot.gameObject.SetActive(false);

        private void Update()
        {
            if (!IsVisible || _arCamera == null) return;

            var distance = Vector3.Distance(_arCamera.transform.position, _contentRoot.position);
            int active = distance <= lod0MaxDistance ? 0 : distance <= lod1MaxDistance ? 1 : 2;

            for (var i = 0; i < _lodInstances.Length; i++)
                if (_lodInstances[i] != null)
                    _lodInstances[i].SetActive(i == active);
        }
    }
}
