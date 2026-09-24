const BASE = "";

export async function addClip(projectId, trackId, clip) {
  const r = await fetch(`${BASE}/api/timeline/clips`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ projectId, trackId, ...clip }),
  });
  return r.json();
}

export async function cutClip(projectId, clipId, atRelative) {
  const r = await fetch(`${BASE}/api/timeline/cut`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ projectId, clipId, atRelative }),
  });
  return r.json();
}

export async function addEffect(projectId, clipId, effectId, params) {
  const r = await fetch(`${BASE}/api/timeline/effects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ projectId, clipId, effectId, params }),
  });
  return r.json();
}

export async function addTransition(projectId, fromId, toId, transitionId, duration) {
  const r = await fetch(`${BASE}/api/timeline/transitions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ projectId, fromClipId: fromId, toClipId: toId, transitionId, duration }),
  });
  return r.json();
}
