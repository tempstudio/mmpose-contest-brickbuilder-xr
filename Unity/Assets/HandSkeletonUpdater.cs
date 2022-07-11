using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Valve.VR;

public class HandSkeletonUpdater : MonoBehaviour
{
    public SteamVR_Skeleton_Poser poser;
    public SteamVR_Behaviour_Skeleton handSkeleton;
    // Start is called before the first frame update
    void Start()
    {
        handSkeleton.BlendToPoser(poser);
    }

    // Update is called once per frame
    void Update()
    {
        poser.SetBlendingBehaviourValue("Trigger", HandPositionTracker.triggerAmount);
    }

    void LateUpdate()
    {
        handSkeleton.fillBlendPoser();
        handSkeleton.UpdateSkeletonTransforms();
    }
}
