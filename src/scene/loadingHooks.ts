import { DefaultLoadingManager } from 'three'
import { loadState } from '../loader/loadState'

/**
 * Real loading progress for scene 0: the 3D chunk arriving counts as the first 15%, the GLBs and the
 * Draco decoder (all go through three's DefaultLoadingManager) the rest. Imported before any GLB
 * preload so no item is missed.
 */
const CHUNK_SHARE = 15

loadState.set({ progress: CHUNK_SHARE })

DefaultLoadingManager.onProgress = (_url, loaded, total) => {
  loadState.set({ progress: CHUNK_SHARE + ((100 - CHUNK_SHARE) * loaded) / Math.max(total, 1) })
}
