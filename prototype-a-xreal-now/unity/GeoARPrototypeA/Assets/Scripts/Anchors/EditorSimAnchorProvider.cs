using System;
using System.Collections.Generic;
using UnityEngine;

namespace GeoAR.Anchors
{
    /// <summary>
    /// In-editor simulation of the anchor system so the full scene — fusion state
    /// machine, anchor manager, content renderer, field-test logger — runs in play
    /// mode with no glasses attached. Anchors persist to PlayerPrefs-backed JSON
    /// between play sessions to exercise the re-localization path.
    ///
    /// This is a simulation aid, never a demo stand-in: the field-test logger tags
    /// sessions from this provider as source="replay", not "field".
    /// </summary>
    public sealed class EditorSimAnchorProvider : MonoBehaviour, INativeAnchorProvider
    {
        [Tooltip("Simulated seconds before persisted anchors resolve after LoadPersistedAnchors().")]
        [SerializeField] private float simulatedResolveDelay = 1.5f;

        public event Action<string, Pose> AnchorResolved;
        public event Action<bool> TrackingStateChanged;

        private readonly Dictionary<string, Pose> _anchors = new Dictionary<string, Pose>();
        private readonly List<string> _handles = new List<string>();
        private bool _isTracking = true;

        public bool IsTracking => _isTracking;
        public IReadOnlyList<string> KnownAnchorHandles => _handles;

        public string CreateAnchor(Pose worldPose)
        {
            var handle = Guid.NewGuid().ToString("N");
            _anchors[handle] = worldPose;
            _handles.Add(handle);
            return handle;
        }

        public bool SaveAnchor(string anchorHandle)
        {
            if (!_anchors.TryGetValue(anchorHandle, out var pose)) return false;
            PlayerPrefs.SetString(PrefKey(anchorHandle), JsonUtility.ToJson(new PoseDto(pose)));
            PlayerPrefs.SetString(IndexKey, string.Join(",", PersistedHandles(anchorHandle)));
            return true;
        }

        public void LoadPersistedAnchors()
        {
            StartCoroutine(ResolveAfterDelay());
        }

        public bool TryGetAnchorPose(string anchorHandle, out Pose pose) =>
            _anchors.TryGetValue(anchorHandle, out pose);

        /// <summary>Test hook: simulate tracking loss/recovery from an editor button or test.</summary>
        public void SimulateTrackingState(bool tracking)
        {
            _isTracking = tracking;
            TrackingStateChanged?.Invoke(tracking);
        }

        private System.Collections.IEnumerator ResolveAfterDelay()
        {
            yield return new WaitForSeconds(simulatedResolveDelay);
            foreach (var handle in PersistedHandles())
            {
                var json = PlayerPrefs.GetString(PrefKey(handle), null);
                if (string.IsNullOrEmpty(json)) continue;
                var pose = JsonUtility.FromJson<PoseDto>(json).ToPose();
                _anchors[handle] = pose;
                if (!_handles.Contains(handle)) _handles.Add(handle);
                AnchorResolved?.Invoke(handle, pose);
            }
        }

        private const string IndexKey = "geoar.sim.anchors";
        private static string PrefKey(string handle) => $"geoar.sim.anchor.{handle}";

        private IEnumerable<string> PersistedHandles(string extra = null)
        {
            var existing = PlayerPrefs.GetString(IndexKey, "");
            var set = new HashSet<string>(existing.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries));
            if (extra != null) set.Add(extra);
            return set;
        }

        [Serializable]
        private struct PoseDto
        {
            public Vector3 p; public Quaternion r;
            public PoseDto(Pose pose) { p = pose.position; r = pose.rotation; }
            public Pose ToPose() => new Pose(p, r);
        }
    }
}
