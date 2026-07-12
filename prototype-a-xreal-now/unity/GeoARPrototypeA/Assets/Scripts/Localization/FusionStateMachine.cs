using System;
using System.Collections.Generic;

namespace GeoAR.Localization
{
    /// <summary>
    /// Pure decision core for GPS + visual + anchor fusion. No UnityEngine types:
    /// this file mirrors fusion/state_machine.py in the Python reference
    /// implementation, transition for transition, and is validated there against
    /// mocked sensor feeds. Keep the two in lockstep — same states, same rules,
    /// same threshold names as the shared backend's per-site config.
    /// </summary>
    public enum FusionState
    {
        Acquiring,
        FusedLock,
        VisualOnly,
        GpsAnchorFallback,
        Relocalizing,
        NoContent,
    }

    [Serializable]
    public struct SensorSnapshot
    {
        /// <summary>Reported GPS accuracy radius in metres; PositiveInfinity when no fix.</summary>
        public float gpsAccuracyM;
        /// <summary>A recognition target exists for the current GPS cell.</summary>
        public bool targetExistsForCell;
        /// <summary>Visual recognition confidence 0..1 (0 when recogniser idle).</summary>
        public float visualConfidence;
        /// <summary>Platform SLAM tracking is healthy.</summary>
        public bool trackingOk;
        /// <summary>A persisted Spatial Anchor has been resolved this session.</summary>
        public bool hasResolvedAnchor;
    }

    [Serializable]
    public class FusionThresholds
    {
        /// <summary>GPS accuracy radius at or under which GPS is trusted for fusion (metres).</summary>
        public float gpsAccuracyGoodM = 10.0f;
        /// <summary>Per-site visual confidence cutoff — tuned by the self-learning loop.</summary>
        public float visualConfidenceMin = 0.70f;
    }

    public sealed class StepResult
    {
        public FusionState State;
        public readonly List<string> Flags = new List<string>();
    }

    public sealed class FusionStateMachine
    {
        public FusionState State { get; private set; } = FusionState.Acquiring;
        public FusionThresholds Thresholds { get; }

        public FusionStateMachine(FusionThresholds thresholds = null)
        {
            Thresholds = thresholds ?? new FusionThresholds();
        }

        /// <summary>
        /// Advance the machine one tick. Rules, in spec order
        /// (docs/geoAR_prototype_A_xreal_now.md, "Localization Decision Logic"):
        ///  1. No target for this GPS cell        -> NoContent (explicit, never silent).
        ///  2. Tracking lost mid-session          -> Relocalizing (anchor first, not full re-lock).
        ///  3. GPS good AND visual recognised     -> FusedLock.
        ///  4. GPS poor but visual recognised     -> VisualOnly.
        ///  5. Visual low, anchor available       -> GpsAnchorFallback + flag rescan_recommended.
        ///  6. Otherwise                          -> keep Acquiring.
        /// </summary>
        public StepResult Step(SensorSnapshot s)
        {
            var result = new StepResult();

            if (!s.targetExistsForCell)
            {
                result.State = FusionState.NoContent;
            }
            else if (!s.trackingOk)
            {
                result.State = FusionState.Relocalizing;
                result.Flags.Add("tracking_lost");
            }
            else
            {
                bool gpsGood = s.gpsAccuracyM <= Thresholds.gpsAccuracyGoodM;
                bool visualOk = s.visualConfidence >= Thresholds.visualConfidenceMin;

                if (visualOk)
                {
                    result.State = gpsGood ? FusionState.FusedLock : FusionState.VisualOnly;
                }
                else if (s.hasResolvedAnchor)
                {
                    result.State = FusionState.GpsAnchorFallback;
                    result.Flags.Add("rescan_recommended");
                }
                else
                {
                    result.State = FusionState.Acquiring;
                }
            }

            State = result.State;
            return result;
        }

        public bool IsLocked =>
            State == FusionState.FusedLock ||
            State == FusionState.VisualOnly ||
            State == FusionState.GpsAnchorFallback;
    }
}
