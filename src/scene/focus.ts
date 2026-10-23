import { Vector3 } from 'three'

/** World position the camera can follow: the falling mug (centroid of the five main shards). */
export const cupFocus = new Vector3()

/** Where the camera is looking this frame (CameraRig writes it; depth of field focuses on it). */
export const cameraTarget = new Vector3() // kept for effects that focus on the subject
