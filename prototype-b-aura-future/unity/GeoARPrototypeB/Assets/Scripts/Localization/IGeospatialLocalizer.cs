using UnityEngine;

namespace GeoAR.Localization
{
    /// <summary>
    /// The generalised fine-lock seam (the single cross-prototype refactor named
    /// in docs/migration_from_prototype_a.md). Prototype A's visual matcher
    /// returns poses in SESSION space; a VPS returns earth-anchored poses.
    /// Prototype A's IVisualLocalizer implementations adopt this interface with
    /// CoordinateFrame.Session — planned as a pre-Aura change in Prototype A's
    /// codebase so both generations share the seam from then on.
    /// </summary>
    public enum CoordinateFrame
    {
        /// <summary>Pose valid only within the current tracking session.</summary>
        Session,
        /// <summary>Pose anchored to earth coordinates (VPS-resolved).</summary>
        Earth,
    }

    public interface IGeospatialLocalizer
    {
        /// <summary>Best current localization confidence, 0..1 — same semantics
        /// the per-site thresholds and self-learning loop already consume.</summary>
        float Confidence { get; }

        /// <summary>Frame the returned poses are expressed in.</summary>
        CoordinateFrame Frame { get; }

        /// <summary>Pose of the recognised site/target when Confidence is above
        /// the per-site cutoff.</summary>
        bool TryGetSitePose(out Pose pose);
    }
}
