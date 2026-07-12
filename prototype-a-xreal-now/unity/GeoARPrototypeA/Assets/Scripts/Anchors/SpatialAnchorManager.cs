using System;
using UnityEngine;

namespace GeoAR.Anchors
{
    /// <summary>
    /// Owns the single site anchor for the MVP (one site, one anchor — see MVP
    /// Boundary in the spec). Places it at the fused pose delivered by the fusion
    /// controller, persists it via the active provider, and re-resolves it on the
    /// next session so content reappears without a fresh visual lock.
    /// </summary>
    public sealed class SpatialAnchorManager : MonoBehaviour
    {
        [Tooltip("Component implementing INativeAnchorProvider (XrealAnchorProvider on device, EditorSimAnchorProvider in editor).")]
        [SerializeField] private MonoBehaviour anchorProviderBehaviour;

        public event Action<Pose> SiteAnchorAvailable;

        private INativeAnchorProvider _provider;
        private string _siteAnchorHandle;

        public bool HasResolvedAnchor { get; private set; }

        private void Awake()
        {
            _provider = anchorProviderBehaviour as INativeAnchorProvider;
            if (_provider == null)
                throw new InvalidOperationException(
                    $"{nameof(anchorProviderBehaviour)} must implement {nameof(INativeAnchorProvider)}");

            _provider.AnchorResolved += OnAnchorResolved;
            _siteAnchorHandle = PlayerPrefs.GetString(HandleKey, null);
        }

        private void Start()
        {
            if (!string.IsNullOrEmpty(_siteAnchorHandle))
                _provider.LoadPersistedAnchors();
        }

        /// <summary>
        /// Called by the fusion controller when a fine lock produces a trusted site
        /// pose. Overwriting an existing persisted anchor is an explicit operation
        /// per the spec's security checks — hence the confirmOverwrite flag.
        /// </summary>
        public void PlaceOrUpdateSiteAnchor(Pose fusedSitePose, bool confirmOverwrite = false)
        {
            if (!string.IsNullOrEmpty(_siteAnchorHandle) && !confirmOverwrite)
            {
                Debug.LogWarning("[GeoAR] Site anchor already exists; pass confirmOverwrite to replace it.");
                return;
            }

            _siteAnchorHandle = _provider.CreateAnchor(fusedSitePose);
            if (_provider.SaveAnchor(_siteAnchorHandle))
            {
                PlayerPrefs.SetString(HandleKey, _siteAnchorHandle);
                HasResolvedAnchor = true;
                SiteAnchorAvailable?.Invoke(fusedSitePose);
            }
        }

        public bool TryGetSitePose(out Pose pose)
        {
            pose = default;
            return !string.IsNullOrEmpty(_siteAnchorHandle)
                   && _provider.TryGetAnchorPose(_siteAnchorHandle, out pose);
        }

        private void OnAnchorResolved(string handle, Pose pose)
        {
            if (handle != _siteAnchorHandle) return;
            HasResolvedAnchor = true;
            SiteAnchorAvailable?.Invoke(pose);
        }

        private const string HandleKey = "geoar.site.anchor.handle";
    }
}
