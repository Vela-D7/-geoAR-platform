using UnityEngine;
using GeoAR.Anchors;
using GeoAR.Content;
using GeoAR.Logging;

namespace GeoAR.Localization
{
    /// <summary>
    /// Scene orchestrator: samples sensor providers each tick, advances the
    /// FusionStateMachine, and drives anchor placement, content visibility and
    /// field-test logging off the resulting state.
    /// </summary>
    public sealed class GeoFusionController : MonoBehaviour
    {
        [Header("Wiring (set by SceneBuilder or by hand)")]
        [SerializeField] private MonoBehaviour gpsProviderBehaviour;      // IGpsProvider
        [SerializeField] private MonoBehaviour visualLocalizerBehaviour;  // IVisualLocalizer
        [SerializeField] private SpatialAnchorManager anchorManager;
        [SerializeField] private HistoricalContentRenderer contentRenderer;
        [SerializeField] private FieldTestLogger fieldTestLogger;

        [Header("Site")]
        [SerializeField] private string siteId = "oystermouth-chapel";
        [Tooltip("MVP: single-site build, so target existence is a flag. Multi-site GPS-cell lookup lives in the shared backend post-MVP.")]
        [SerializeField] private bool targetExistsForCell = true;

        [Header("Thresholds (synced from backend per-site config; self-learning loop tunes these)")]
        [SerializeField] private FusionThresholds thresholds = new FusionThresholds();

        [SerializeField] private float ticksPerSecond = 4f;

        private IGpsProvider _gps;
        private IVisualLocalizer _visual;
        private FusionStateMachine _machine;
        private bool _trackingOk = true;
        private float _nextTick;

        public FusionState CurrentState => _machine?.State ?? FusionState.Acquiring;

        private void Awake()
        {
            _gps = gpsProviderBehaviour as IGpsProvider;
            _visual = visualLocalizerBehaviour as IVisualLocalizer;
            _machine = new FusionStateMachine(thresholds);

            if (anchorManager != null)
            {
                anchorManager.SiteAnchorAvailable += pose => contentRenderer.ShowAt(pose);
                var provider = anchorManager.GetComponent<INativeAnchorProvider>();
                if (provider != null)
                    provider.TrackingStateChanged += ok => _trackingOk = ok;
            }

            fieldTestLogger?.BeginSession(siteId);
        }

        private void Update()
        {
            if (Time.time < _nextTick) return;
            _nextTick = Time.time + 1f / ticksPerSecond;

            var snapshot = new SensorSnapshot
            {
                gpsAccuracyM = _gps?.AccuracyM ?? float.PositiveInfinity,
                targetExistsForCell = targetExistsForCell,
                visualConfidence = _visual?.Confidence ?? 0f,
                trackingOk = _trackingOk,
                hasResolvedAnchor = anchorManager != null && anchorManager.HasResolvedAnchor,
            };

            var result = _machine.Step(snapshot);
            fieldTestLogger?.RecordTick(snapshot, result);

            switch (result.State)
            {
                case FusionState.FusedLock:
                case FusionState.VisualOnly:
                    if (_visual != null && _visual.TryGetTargetPose(out var targetPose))
                    {
                        if (!anchorManager.HasResolvedAnchor)
                            anchorManager.PlaceOrUpdateSiteAnchor(targetPose);
                        contentRenderer.ShowAt(targetPose);
                    }
                    break;

                case FusionState.GpsAnchorFallback:
                case FusionState.Relocalizing:
                    // Anchor path: show at last resolved anchor pose if we have one,
                    // otherwise keep waiting — never render unanchored content.
                    if (anchorManager.TryGetSitePose(out var anchorPose))
                        contentRenderer.ShowAt(anchorPose);
                    break;

                case FusionState.NoContent:
                    contentRenderer.Hide();
                    break;

                case FusionState.Acquiring:
                    break; // keep last visual state during acquisition
            }
        }

        private void OnDestroy() => fieldTestLogger?.EndSession();
    }
}
