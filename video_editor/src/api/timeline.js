export async function addClip(projectId,trackId,clip){ return {clipId:'clip-id'}; }
export async function cutClip(projectId,clipId,at){ return true; }
export async function addEffect(projectId,clipId,effectId,params){ return true; }
export async function addTransition(projectId,fromId,toId,transitionId,duration){ return true; }
