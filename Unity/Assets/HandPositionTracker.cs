using System.Collections.Generic;
using UnityEngine;

public class HandPositionTracker : MonoBehaviour
{
    public Camera camera0;
    public Camera camera1;
    public RenderTexture resolution;
    public GameObject handRoot;
    public GameObject handOffsetted;
    public GameObject handModel;

    public static float triggerAmount;
    private List<Vector3> trackedHandPositions;


    // Start is called before the first frame update
    void Start()
    {
        trackedHandPositions = new List<Vector3>();
    }

    // Update is called once per frame
    void Update()
    {
        FrameData handData0 = UdpServer.frameData;
        FrameData handData1 = UdpServer.secondFrameData;

        if (handData0.objects.Count > 0 && handData1.objects.Count > 0)
        {
            List<Vector2> handPoints0 = handData0.objects[0];
            List<Vector2> handPoints1 = handData1.objects[0];

            List<Vector3> newEstimate = new List<Vector3>();

            for(int i = 0; i < handPoints0.Count; i++)
            {
                Ray ray0 = camera0.ScreenPointToRay(convertCoordinate(handPoints0[i]));
                Ray ray1 = camera1.ScreenPointToRay(convertCoordinate(handPoints1[i]));
                Vector3 result = closestPoint2Lines(ray0.origin, ray0.direction, ray1.origin, ray1.direction);
                if (trackedHandPositions.Count > 0)
                {
                    result = Vector3.Lerp(trackedHandPositions[i], result, 0.02f);
                }
                newEstimate.Add(result);
            }
            trackedHandPositions = newEstimate;
        }
        if (trackedHandPositions.Count > 0)
        {
            handRoot.transform.position = (trackedHandPositions[0] + trackedHandPositions[17] + trackedHandPositions[5] + trackedHandPositions[9] + trackedHandPositions[13]) / 5;

            Vector3 right = trackedHandPositions[17] - trackedHandPositions[5];
            Vector3 forward = trackedHandPositions[9] - trackedHandPositions[0];
            handRoot.transform.rotation = Quaternion.LookRotation(forward, -1 * right);

            handModel.transform.position = handOffsetted.transform.position;
            handModel.transform.rotation = handOffsetted.transform.rotation;

            HandPositionTracker.triggerAmount = Mathf.Clamp01(1 - Mathf.InverseLerp(45f, 25f, Vector3.Angle(trackedHandPositions[8] - trackedHandPositions[5], trackedHandPositions[5] - trackedHandPositions[0])));
            Debug.Log(Vector3.Angle(trackedHandPositions[8] - trackedHandPositions[5], trackedHandPositions[5] - trackedHandPositions[0]));
        }
    }

    public Vector3 closestPoint2Lines(Vector3 linePoint1, Vector3 lineVec1, Vector3 linePoint2, Vector3 lineVec2)
    {

        float a = Vector3.Dot(lineVec1, lineVec1);
        float b = Vector3.Dot(lineVec1, lineVec2);
        float e = Vector3.Dot(lineVec2, lineVec2);

        float d = a * e - b * b;

        //lines are not parallel
        if (d != 0.0f)
        {

            Vector3 r = linePoint1 - linePoint2;
            float c = Vector3.Dot(lineVec1, r);
            float f = Vector3.Dot(lineVec2, r);

            float s = (b * f - c * e) / d;
            float t = (a * f - c * b) / d;

            Vector3 closestPointLine1 = linePoint1 + lineVec1 * s;
            Vector3 closestPointLine2 = linePoint2 + lineVec2 * t;

            return (closestPointLine1 + closestPointLine2) / 2;
        }

        return Vector3.zero;
    }


    private Vector2 convertCoordinate(Vector2 source)
    {
        return new Vector2(source.x, resolution.height - source.y);
    }
}
