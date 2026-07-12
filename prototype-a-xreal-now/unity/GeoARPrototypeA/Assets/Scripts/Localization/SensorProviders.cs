using UnityEngine;

namespace GeoAR.Localization
{
    /// <summary>GPS/GNSS coarse-lock source.</summary>
    public interface IGpsProvider
    {
        /// <summary>Reported accuracy radius in metres; PositiveInfinity when no fix.</summary>
        float AccuracyM { get; }
        /// <summary>WGS84 position of the device, valid when AccuracyM is finite.</summary>
        Vector2 LatLon { get; }
    }

    /// <summary>Visual fine-lock source (MultiSet AI SDK or custom feature matcher).</summary>
    public interface IVisualLocalizer
    {
        /// <summary>Best current recognition confidence, 0..1.</summary>
        float Confidence { get; }
        /// <summary>World pose of the recognised target when Confidence is above cutoff.</summary>
        bool TryGetTargetPose(out Pose pose);
    }

    /// <summary>
    /// Device GPS via UnityEngine.Input.location. Requires location permission in
    /// the companion phone app; on glasses tethered to a phone, GPS comes from the
    /// phone. [Needs verification]: accuracy behaviour on the actual tether setup.
    /// </summary>
    public sealed class DeviceGpsProvider : MonoBehaviour, IGpsProvider
    {
        public float AccuracyM =>
            UnityEngine.Input.location.status == LocationServiceStatus.Running
                ? UnityEngine.Input.location.lastData.horizontalAccuracy
                : float.PositiveInfinity;

        public Vector2 LatLon =>
            new Vector2(UnityEngine.Input.location.lastData.latitude,
                        UnityEngine.Input.location.lastData.longitude);

        private void Start()
        {
            if (UnityEngine.Input.location.isEnabledByUser)
                UnityEngine.Input.location.Start(desiredAccuracyInMeters: 3f, updateDistanceInMeters: 1f);
        }
    }

    /// <summary>
    /// Scripted mock feeds for editor play-mode: drives the full fusion state
    /// machine with no hardware. Values are set from the inspector or by
    /// MockSensorScenario to replay the same scenarios as the Python test suite.
    /// </summary>
    public sealed class MockSensorProvider : MonoBehaviour, IGpsProvider, IVisualLocalizer
    {
        [Header("Mocked GPS")]
        public float mockAccuracyM = 5f;
        public Vector2 mockLatLon = new Vector2(51.5720f, -4.0130f); // Oystermouth Castle

        [Header("Mocked visual recogniser")]
        [Range(0f, 1f)] public float mockConfidence = 0.85f;
        public Pose mockTargetPose = new Pose(new Vector3(0, 0, 3f), Quaternion.identity);

        public float AccuracyM => mockAccuracyM;
        public Vector2 LatLon => mockLatLon;
        public float Confidence => mockConfidence;

        public bool TryGetTargetPose(out Pose pose)
        {
            pose = mockTargetPose;
            return true;
        }
    }
}
