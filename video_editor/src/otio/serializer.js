// serializer.js - conversión proyecto interno ↔ OpenTimelineIO JSON
export function toOTIO(project){
  return {
    schema_major_version: 1,
    schema_minor_version: 1,
    tracks: project.timeline.tracks.map(t=>({
      name: t.id,
      kind: t.type,
      clips: t.clips
    }))
  };
}
export function fromOTIO(otio){
  return {
    id: 'imported',
    timeline: { tracks: otio.tracks.map(t=>({id:t.name,type:t.kind,clips:t.clips})) }
  };
}
