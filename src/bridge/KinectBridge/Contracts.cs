using System.Collections.Generic;
using System.Runtime.Serialization;

namespace KinectBridge;

[DataContract]
public sealed class BodyFramePacket
{
    [DataMember(Name = "frame_index")]
    public int FrameIndex { get; set; }

    [DataMember(Name = "timestamp_ms")]
    public long TimestampMs { get; set; }

    [DataMember(Name = "bodies")]
    public List<BodyPacket> Bodies { get; set; } = new();
}

[DataContract]
public sealed class BodyPacket
{
    [DataMember(Name = "tracking_id")]
    public ulong TrackingId { get; set; }

    [DataMember(Name = "hand_state_left")]
    public string HandStateLeft { get; set; } = "unknown";

    [DataMember(Name = "hand_state_right")]
    public string HandStateRight { get; set; } = "unknown";

    [DataMember(Name = "joints")]
    public Dictionary<string, JointPacket> Joints { get; set; } = new();
}

[DataContract]
public sealed class JointPacket
{
    [DataMember(Name = "x")]
    public float X { get; set; }

    [DataMember(Name = "y")]
    public float Y { get; set; }

    [DataMember(Name = "z")]
    public float Z { get; set; }

    [DataMember(Name = "tracked")]
    public bool Tracked { get; set; }
}
