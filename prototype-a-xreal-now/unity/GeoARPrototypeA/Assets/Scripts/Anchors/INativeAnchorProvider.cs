using System;
using System.Collections.Generic;
using UnityEngine;

namespace GeoAR.Anchors
{
    /// <summary>
    /// Abstraction over the platform anchor system. Prototype A binds this to the
    /// XREAL SDK (SLAM + Spatial Anchors); Prototype B will bind it to
    /// ARCore/Android XR anchors. Keeping call sites against this interface is
    /// what makes the migration section of the Prototype B doc credible.
    /// </summary>
    public interface INativeAnchorProvider
    {
        /// <summary>True once the underlying SLAM/tracking session is running.</summary>
        bool IsTracking { get; }

        /// <summary>Create an anchor at a world pose. Returns a provider-scoped handle.</summary>
        string CreateAnchor(Pose worldPose);

        /// <summary>Persist an anchor so it can be re-localized in a later session.</summary>
        bool SaveAnchor(string anchorHandle);

        /// <summary>Begin re-localizing all persisted anchors for the current map.</summary>
        void LoadPersistedAnchors();

        /// <summary>Current world pose of an anchor, if resolved this session.</summary>
        bool TryGetAnchorPose(string anchorHandle, out Pose pose);

        /// <summary>Fired when a persisted anchor is re-localized (handle, pose).</summary>
        event Action<string, Pose> AnchorResolved;

        /// <summary>Fired when tracking is lost/regained.</summary>
        event Action<bool> TrackingStateChanged;

        IReadOnlyList<string> KnownAnchorHandles { get; }
    }
}
