using System;
using System.Collections.Generic;
using UnityEngine;

namespace GeoAR.Anchors
{
    /// <summary>
    /// XREAL SDK (NRSDK) adapter for <see cref="INativeAnchorProvider"/>.
    ///
    /// The SDK is imported separately on the dev machine (see SceneSetup.md) and is
    /// NOT vendored in this repo, so all NRSDK calls live behind XREAL_SDK_PRESENT.
    /// Without the define this class still compiles and throws loudly if used —
    /// the editor-sim provider is the no-hardware path, never this one silently.
    ///
    /// [Needs verification]: exact NRSDK mapping/anchor API names against the SDK
    /// version installed on the dev machine before the 24 July build. The mapping
    /// below follows the NRSDK anchor sample (NRWorldAnchorStore pattern).
    /// </summary>
    public sealed class XrealAnchorProvider : MonoBehaviour, INativeAnchorProvider
    {
        public event Action<string, Pose> AnchorResolved;
        public event Action<bool> TrackingStateChanged;

        private readonly List<string> _handles = new List<string>();
        public IReadOnlyList<string> KnownAnchorHandles => _handles;

#if XREAL_SDK_PRESENT
        // Real NRSDK-backed implementation goes here, following the
        // NRWorldAnchorStore sample: create NRAnchor at pose, Save(key),
        // store.GetAllIds() + Load(key) on session start, subscribe to
        // NRHMDPoseTracker tracking-state callbacks.
        // Kept intentionally unwritten until the SDK version on the dev
        // machine is pinned — see [Needs verification] above.
        public bool IsTracking => throw new NotImplementedException("Bind to NRSDK tracking state.");
        public string CreateAnchor(Pose worldPose) => throw new NotImplementedException();
        public bool SaveAnchor(string anchorHandle) => throw new NotImplementedException();
        public void LoadPersistedAnchors() => throw new NotImplementedException();
        public bool TryGetAnchorPose(string anchorHandle, out Pose pose) => throw new NotImplementedException();
#else
        private const string NotPresent =
            "XREAL SDK not imported (XREAL_SDK_PRESENT undefined). " +
            "Use EditorSimAnchorProvider for play-mode work, or import the SDK per SceneSetup.md.";

        public bool IsTracking => throw new InvalidOperationException(NotPresent);
        public string CreateAnchor(Pose worldPose) => throw new InvalidOperationException(NotPresent);
        public bool SaveAnchor(string anchorHandle) => throw new InvalidOperationException(NotPresent);
        public void LoadPersistedAnchors() => throw new InvalidOperationException(NotPresent);
        public bool TryGetAnchorPose(string anchorHandle, out Pose pose) => throw new InvalidOperationException(NotPresent);
#endif
    }
}
