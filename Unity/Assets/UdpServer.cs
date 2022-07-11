using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;


public class FrameData
{

    public List<List<Vector2>> objects = new List<List<Vector2>>();
    public int version;
    public int cameraId;

    public void fromBytes(byte[] bytes)
    {
        MemoryStream stream = new MemoryStream(bytes);
        BinaryReader reader = new BinaryReader(stream);

        this.version = reader.ReadInt32();
        this.cameraId = reader.ReadInt32();
        int numObjects = reader.ReadInt32();
        for(int i = 0; i < numObjects; i++)
        {
            List<Vector2> nodes = new List<Vector2>();
            int numNodes = reader.ReadInt32();
            for(int j = 0; j < numNodes; j++)
            {
                float x = reader.ReadSingle();
                float y = reader.ReadSingle();
                nodes.Add(new Vector2(x, y));
            }
            objects.Add(nodes);
        }
    }
}
public class UdpServer : MonoBehaviour
{
    // Start is called before the first frame update
    public static FrameData frameData;
    public static FrameData secondFrameData;
    private Thread workerThread;
    void Start()
    {
        IPEndPoint ipEndpoint = new IPEndPoint(IPAddress.Any, 10001);
        UdpClient udpServer = new UdpClient(10001);
        workerThread = new Thread(() =>
        {
            while (true)
            {
                try
                {
                    byte[] data = udpServer.Receive(ref ipEndpoint);
                    FrameData fd = new FrameData();
                    fd.fromBytes(data);
                    if (fd.objects.Count > 0)
                    {
                        if (fd.cameraId == 0)
                        {
                            UdpServer.frameData = fd;
                        }
                        else if (fd.cameraId == 1)
                        {
                            UdpServer.secondFrameData = fd;
                        }
                    }
                }
                catch (Exception e)
                {
                    Debug.LogError(e);
                }
            }


        });
        workerThread.Start();
    }

    void OnDestroy()
    {
        workerThread.Abort();
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
