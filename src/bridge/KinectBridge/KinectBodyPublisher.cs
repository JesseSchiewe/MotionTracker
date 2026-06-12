using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Threading;
using Microsoft.Kinect;

namespace KinectBridge;

public sealed class KinectBodyPublisher : IDisposable
{
    private static readonly IReadOnlyDictionary<JointType, string> JointNames = new Dictionary<JointType, string>
    {
        [JointType.Head] = "head",
        [JointType.Neck] = "neck",
        [JointType.SpineShoulder] = "spine_shoulder",
        [JointType.SpineMid] = "spine_mid",
        [JointType.SpineBase] = "spine_base",
        [JointType.ShoulderLeft] = "shoulder_left",
        [JointType.ElbowLeft] = "elbow_left",
        [JointType.HandLeft] = "hand_left",
        [JointType.ShoulderRight] = "shoulder_right",
        [JointType.ElbowRight] = "elbow_right",
        [JointType.HandRight] = "hand_right",
        [JointType.HipLeft] = "hip_left",
        [JointType.KneeLeft] = "knee_left",
        [JointType.AnkleLeft] = "ankle_left",
        [JointType.FootLeft] = "foot_left",
        [JointType.HipRight] = "hip_right",
        [JointType.KneeRight] = "knee_right",
        [JointType.AnkleRight] = "ankle_right",
        [JointType.FootRight] = "foot_right",
    };

    private readonly KinectSensor _sensor;
    private readonly BodyFrameReader _reader;
    private readonly TcpListener _listener;
    private readonly ConcurrentDictionary<TcpClient, StreamWriter> _clients = new();
    private readonly DataContractJsonSerializer _serializer = new(typeof(BodyFramePacket));
    private int _frameIndex;

    public KinectBodyPublisher(int port)
    {
        _sensor = KinectSensor.GetDefault() ?? throw new InvalidOperationException("Kinect v2 sensor not found.");
        _reader = _sensor.BodyFrameSource.OpenReader() ?? throw new InvalidOperationException("Unable to open body frame reader.");
        _reader.FrameArrived += OnFrameArrived;
        _listener = new TcpListener(IPAddress.Loopback, port);
    }

    public void Start()
    {
        _sensor.Open();
        _listener.Start();
        _listener.BeginAcceptTcpClient(OnClientAccepted, null);
    }

    public void Dispose()
    {
        _reader.FrameArrived -= OnFrameArrived;
        _listener.Stop();
        foreach (var client in _clients.Keys)
        {
            client.Dispose();
        }

        _reader.Dispose();
        _sensor.Close();
    }

    private void OnClientAccepted(IAsyncResult ar)
    {
        try
        {
            TcpClient client = _listener.EndAcceptTcpClient(ar);
            var writer = new StreamWriter(client.GetStream(), new UTF8Encoding(false)) { AutoFlush = true };
            _clients[client] = writer;
        }
        catch (ObjectDisposedException)
        {
            return;
        }
        finally
        {
            if (_listener.Server.IsBound)
            {
                _listener.BeginAcceptTcpClient(OnClientAccepted, null);
            }
        }
    }

    private void OnFrameArrived(object? sender, BodyFrameArrivedEventArgs e)
    {
        using BodyFrame? frame = e.FrameReference.AcquireFrame();
        if (frame is null)
        {
            return;
        }

        Body[] bodies = new Body[frame.BodyCount];
        frame.GetAndRefreshBodyData(bodies);
        BodyFramePacket packet = new()
        {
            FrameIndex = Interlocked.Increment(ref _frameIndex),
            TimestampMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
            Bodies = BuildBodies(bodies),
        };
        string json = Serialize(packet);
        Broadcast(json);
    }

    private static List<BodyPacket> BuildBodies(IEnumerable<Body> bodies)
    {
        List<BodyPacket> packets = new();
        foreach (Body body in bodies)
        {
            if (!body.IsTracked)
            {
                continue;
            }

            Dictionary<string, JointPacket> joints = new(StringComparer.OrdinalIgnoreCase);
            foreach (var pair in body.Joints)
            {
                if (!JointNames.TryGetValue(pair.Key, out string? name))
                {
                    continue;
                }

                CameraSpacePoint point = pair.Value.Position;
                joints[name] = new JointPacket
                {
                    X = point.X,
                    Y = point.Y,
                    Z = point.Z,
                    Tracked = pair.Value.TrackingState == TrackingState.Tracked,
                };
            }

            packets.Add(new BodyPacket
            {
                TrackingId = body.TrackingId,
                HandStateLeft = body.HandLeftState.ToString().ToLowerInvariant(),
                HandStateRight = body.HandRightState.ToString().ToLowerInvariant(),
                Joints = joints,
            });
        }

        return packets;
    }

    private string Serialize(BodyFramePacket packet)
    {
        using MemoryStream stream = new();
        _serializer.WriteObject(stream, packet);
        return Encoding.UTF8.GetString(stream.ToArray());
    }

    private void Broadcast(string payload)
    {
        foreach (var pair in _clients)
        {
            try
            {
                pair.Value.WriteLine(payload);
            }
            catch (IOException)
            {
                RemoveClient(pair.Key);
            }
            catch (ObjectDisposedException)
            {
                RemoveClient(pair.Key);
            }
        }
    }

    private void RemoveClient(TcpClient client)
    {
        if (_clients.TryRemove(client, out StreamWriter? writer))
        {
            writer.Dispose();
            client.Dispose();
        }
    }
}
