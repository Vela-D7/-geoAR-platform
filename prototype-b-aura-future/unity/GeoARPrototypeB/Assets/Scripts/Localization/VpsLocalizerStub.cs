using UnityEngine;

namespace GeoAR.Localization
{
    /// <summary>
    /// Seam for the VPS partner SDK (Niantic Spatial primary path, MultiSet AI
    /// fallback — decision checklist in docs/vps_comparison.md). Compiles today;
    /// localizes nothing by design.
    ///
    /// Security posture (fixed at design time, per spec): VPS credentials are
    /// SERVER-SIDE ONLY. The device authenticates to our shared backend, which
    /// issues short-lived VPS session tokens; no partner API key ever ships in
    /// the app. [Needs verification]: whether the chosen partner's SDK supports
    /// token-based session auth in this shape.
    /// </summary>
    public sealed class VpsLocalizerStub : MonoBehaviour, IGeospatialLocalizer
    {
        public float Confidence => 0f;                       // never claims a lock
        public CoordinateFrame Frame => CoordinateFrame.Earth;

        public bool TryGetSitePose(out Pose pose)
        {
            pose = default;
            return false; // fusion state machine correctly stays in ACQUIRING
        }
    }
}
