using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;
using GeoAR.Localization;

namespace GeoAR.Logging
{
    /// <summary>
    /// Emits one JSON session record conforming to
    /// shared-infrastructure/schemas/field_test_log.schema.json (v1) — the exact
    /// format the shared backend ingests and the self-learning loop consumes.
    /// Written as JSONL to persistentDataPath; upload to the backend is manual for
    /// the MVP (adb pull / share sheet), automatic post-MVP.
    /// </summary>
    public sealed class FieldTestLogger : MonoBehaviour
    {
        [Tooltip("'field' only for real device sessions. Editor/sim runs MUST stay 'replay'.")]
        [SerializeField] private string source = "replay";
        [SerializeField] private string deviceProfile = "xreal_current_sdk";

        private string _sessionId;
        private string _siteId;
        private DateTime _startedUtc;
        private float _startTime;
        private float _bestConfidence;
        private float _bestGpsAccuracy = float.PositiveInfinity;
        private float _timeToLock = -1f;
        private float _maxDriftM;
        private Vector3? _lastAnchorPos;
        private FusionState _finalState = FusionState.Acquiring;
        private int _relockAttempts;
        private readonly HashSet<string> _flags = new HashSet<string>();

        public void BeginSession(string siteId)
        {
            _siteId = siteId;
            _sessionId = Guid.NewGuid().ToString("N");
            _startedUtc = DateTime.UtcNow;
            _startTime = Time.realtimeSinceStartup;
        }

        public void RecordTick(SensorSnapshot snapshot, StepResult result)
        {
            _bestConfidence = Mathf.Max(_bestConfidence, snapshot.visualConfidence);
            _bestGpsAccuracy = Mathf.Min(_bestGpsAccuracy, snapshot.gpsAccuracyM);
            foreach (var f in result.Flags) _flags.Add(f);

            bool locked = result.State == FusionState.FusedLock
                       || result.State == FusionState.VisualOnly
                       || result.State == FusionState.GpsAnchorFallback;
            if (locked && _timeToLock < 0f)
                _timeToLock = Time.realtimeSinceStartup - _startTime;
            if (result.State == FusionState.Relocalizing && _finalState != FusionState.Relocalizing)
                _relockAttempts++;

            _finalState = result.State;
        }

        /// <summary>Feed anchor pose updates so drift is max observed anchor movement.</summary>
        public void RecordAnchorPose(Vector3 worldPos)
        {
            if (_lastAnchorPos.HasValue)
                _maxDriftM = Mathf.Max(_maxDriftM, Vector3.Distance(worldPos, _lastAnchorPos.Value));
            _lastAnchorPos = worldPos;
        }

        public void EndSession()
        {
            if (_sessionId == null) return;

            string outcome = _finalState switch
            {
                FusionState.FusedLock or FusionState.VisualOnly => "success",
                FusionState.GpsAnchorFallback => "degraded",
                _ => "failure",
            };

            // Manual JSON: schema v1 is flat and Unity's JsonUtility can't express
            // infinity-guards/enums the way we need. Keep field order matching the schema.
            var record =
                "{" +
                $"\"schema_version\":1," +
                $"\"session_id\":\"{_sessionId}\"," +
                $"\"site_id\":\"{_siteId}\"," +
                $"\"device_profile\":\"{deviceProfile}\"," +
                $"\"started_at\":\"{_startedUtc:yyyy-MM-ddTHH:mm:ssZ}\"," +
                $"\"ended_at\":\"{DateTime.UtcNow:yyyy-MM-ddTHH:mm:ssZ}\"," +
                $"\"gps_accuracy_m\":{Num(float.IsInfinity(_bestGpsAccuracy) ? 999f : _bestGpsAccuracy)}," +
                $"\"visual_confidence\":{Num(_bestConfidence)}," +
                $"\"time_to_lock_s\":{Num(_timeToLock < 0 ? Time.realtimeSinceStartup - _startTime : _timeToLock)}," +
                $"\"drift_m\":{Num(_maxDriftM)}," +
                $"\"lighting\":\"unknown\"," +
                $"\"final_state\":\"{StateName(_finalState)}\"," +
                $"\"outcome\":\"{outcome}\"," +
                $"\"relock_attempts\":{_relockAttempts}," +
                $"\"flags\":[{string.Join(",", FlagJson())}]," +
                $"\"source\":\"{source}\"" +
                "}";

            var path = Path.Combine(Application.persistentDataPath, "geoar_field_tests.jsonl");
            File.AppendAllText(path, record + "\n");
            Debug.Log($"[GeoAR] Field-test session logged to {path}");
            _sessionId = null;
        }

        private IEnumerable<string> FlagJson()
        {
            foreach (var f in _flags) yield return $"\"{f}\"";
        }

        private static string Num(float v) => v.ToString("0.###", CultureInfo.InvariantCulture);

        private static string StateName(FusionState s) => s switch
        {
            FusionState.FusedLock => "FUSED_LOCK",
            FusionState.VisualOnly => "VISUAL_ONLY",
            FusionState.GpsAnchorFallback => "GPS_ANCHOR_FALLBACK",
            FusionState.Relocalizing => "RELOCALIZING",
            FusionState.NoContent => "NO_CONTENT",
            _ => "ACQUIRING",
        };
    }
}
