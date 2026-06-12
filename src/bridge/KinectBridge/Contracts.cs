using System.Collections.Generic;
using System.Runtime.Serialization;

namespace KinectBridge;

[DataContract]
public sealed class BodyFramePacket
{
    [DataMember(Name = "frame_index")]
    public int FrameIndex { get; init; }

    [DataMember(Name = "timestamp_ms")]
    public long TimestampMs { get; init; }

    [DataMember(Name = "bodies")]
    public List<BodyPacket> Bodies { get; init; } = new();
}

[DataContract]
public sealed class BodyPacket
{
    [DataMember(Name = "tracking_id")]
    public ulong TrackingId { get; init; }

    [DataMember(Name = "hand_state_left")]
    public string HandStateLeft { get; init; } = "unknown";

    [DataMember(Name = "hand_state_right")]
    public string HandStateRight { get; init; } = "unknown";

    [DataMember(Name = "joints")]
    public Dictionary<string, JointPacket> Joints { get; init; } = new();
}

[DataContract]
public sealed class JointPacket
{
    [DataMember(Name = "x")]
    public float X { get; init; }

    [DataMember(Name = "y")]
    public float Y { get; init; }

    [DataMember(Name = "z")]
    public float Z { get; init; }

    [DataMember(Name = "tracked")]
    public bool Tracked { get; init; }
}
