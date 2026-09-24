/** OpenTimelineIO-compatible JSON export */
import { basename } from "path";

export function projectToOTIO(proj) {
  const rate = 30;
  const tracks = (proj.timeline?.tracks || []).map((track) => {
    const children = [...(track.clips || [])]
      .sort((a, b) => a.start - b.start)
      .map((clip) => {
        const dur = clip.duration || 0;
        return {
          OTIO_SCHEMA: "Clip.2",
          name: clip.filename || clip.id,
          source_range: {
            OTIO_SCHEMA: "TimeRange.1",
            start_time: { OTIO_SCHEMA: "RationalTime.1", rate, value: Math.round((clip.inPoint || 0) * rate) },
            duration: { OTIO_SCHEMA: "RationalTime.1", rate, value: Math.round(dur * rate) },
          },
          media_reference: {
            OTIO_SCHEMA: "ExternalReference.1",
            target_url: clip.sourcePath ? `file://${clip.sourcePath}` : "",
            available_range: null,
            metadata: { mediaId: clip.mediaId, effects: clip.effects || [] },
          },
          metadata: { gremlin_start_seconds: clip.start || 0, gremlin_clip_id: clip.id },
        };
      });
    return {
      OTIO_SCHEMA: "Track.2",
      name: track.id,
      kind: track.type === "audio" ? "Audio" : "Video",
      children,
      metadata: {},
    };
  });
  const transitions = (proj.timeline?.transitions || []).map((tr) => ({
    OTIO_SCHEMA: "Transition.1",
    name: tr.transitionId,
    transition_type: tr.transitionId,
    in_offset: { OTIO_SCHEMA: "RationalTime.1", rate, value: 0 },
    out_offset: { OTIO_SCHEMA: "RationalTime.1", rate, value: Math.round((tr.duration || 1) * rate) },
    metadata: { fromClipId: tr.fromClipId, toClipId: tr.toClipId, gremlin_id: tr.id },
  }));
  return {
    OTIO_SCHEMA: "Timeline.1",
    name: proj.name || proj.id,
    global_start_time: { OTIO_SCHEMA: "RationalTime.1", rate, value: 0 },
    tracks: { OTIO_SCHEMA: "Stack.1", name: "tracks", children: tracks },
    metadata: {
      gremlin_project_id: proj.id,
      gremlin_transitions: transitions,
      exporter: "ContentGremlin video_editor",
      media_library: (proj.media || []).map((m) => ({ id: m.id, filename: m.filename, path: m.path, duration: m.duration })),
    },
  };
}
