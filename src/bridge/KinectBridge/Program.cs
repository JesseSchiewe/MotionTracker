using System;

namespace KinectBridge;

internal static class Program
{
    private static int Main(string[] args)
    {
        int port = 9001;
        if (args.Length > 0 && int.TryParse(args[0], out int parsedPort))
        {
            port = parsedPort;
        }

        Console.WriteLine($"Starting Kinect bridge on 127.0.0.1:{port}");
        try
        {
            using KinectBodyPublisher publisher = new(port);
            publisher.Start();
            Console.WriteLine("Bridge running. Press Enter to stop.");
            Console.ReadLine();
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }
}
