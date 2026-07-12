using System;
using System.Collections.Generic;
using UnityEngine;

namespace GeoAR.Anchors
{
    /// <summary>
    /// Planned ARCore/Android XR binding for the same INativeAnchorProvider
    /// interface Prototype A binds to the XREAL SDK (see
    /// prototype-a-xreal-now/unity/.../Anchors/INativeAnchorProvider.cs — the
    /// interface ports to this project unchanged; it is not duplicated here to
    /// avoid a fork).
    ///
    /// EVERYTHING below is design-time stub. [Needs verification] once Android
    /// XR dev-kit tooling is public: anchor persistence semantics on Aura
    /// (ARCore cloud anchors vs local map recall vs VPS-native persistence),
    /// tracking-state callbacks, and handle lifetime rules.
    /// </summary>
    public sealed class ArCoreAnchorProvider : MonoBehaviour
    {
        public event Action<string, Pose> AnchorResolved;
        public event Action<bool> TrackingStateChanged;

        private readonly List<string> _handles = new List<string>();
        public IReadOnlyList<string> KnownAnchorHandles => _handles;

#if ANDROID_XR_PRESENT
        // Real ARCore/Android XR calls land here once the dev kit is available.
        // Deliberately unwritten — see [Needs verification] above.
        public bool IsTracking => throw new NotImplementedException("Bind to ARCore tracking state.");
        public string CreateAnchor(Pose worldPose) => throw new NotImplementedException();
        public bool SaveAnchor(string anchorHandle) => throw new NotImplementedException();
        public void LoadPersistedAnchors() => throw new NotImplementedException();
        public bool TryGetAnchorPose(string anchorHandle, out Pose pose) => throw new NotImplementedException();
#else
        private const string NotPresent =
            "Android XR SDK not present (ANDROID_XR_PRESENT undefined). This scaffold has no " +
            "runnable anchor path by design — Prototype B is architecture-only until dev kits ship.";

        public bool IsTracking => throw new InvalidOperationException(NotPresent);
        public string CreateAnchor(Pose worldPose) => throw new InvalidOperationException(NotPresent);
        public bool SaveAnchor(string anchorHandle) => throw new InvalidOperationException(NotPresent);
        public void LoadPersistedAnchors() => throw new InvalidOperationException(NotPresent);
        public bool TryGetAnchorPose(string anchorHandle, out Pose pose) => throw new InvalidOperationException(NotPresent);
#endif
    }
}
