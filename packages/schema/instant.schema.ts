// Docs: https://www.instantdb.com/docs/modeling-data

import { i } from "@instantdb/core";

const _schema = i.schema({
  // We are going to comprehensively model and map this domain.
  entities: {
    $files: i.entity({
      path: i.string().unique().indexed(),
      url: i.string(),
    }),
    $users: i.entity({
      email: i.string().unique().indexed().optional(),
      imageURL: i.string().optional(),
      type: i.string().optional(),
    }),
    jobs: i.entity({
      created_at: i.string().indexed().optional(),
      error: i.any().optional(),
      progress: i.string().optional(),
      type: i.string().optional(),
    }),
    channels: i.entity({
      name: i.string(),
      platform: i.string(),
      external_id: i.string().unique(),
      url: i.string().optional(),
      description: i.string().optional(),
      thumbnail_url: i.string().optional(),
    }),
    videos: i.entity({
      title: i.string(),
      original_url: i.string().unique(),
      platform: i.string(),
      upload_date: i.string().optional(),
      external_id: i.string().unique().optional(),
      duration: i.number().optional(),
      created_at: i.string().indexed().optional(),
      // Metadata
      view_count: i.number().optional(),
      like_count: i.number().optional(),
      description: i.string().optional(),
      thumbnail_url: i.string().optional(),
    }),
    transcriptions: i.entity({
      created_at: i.string(),
      model: i.string().optional(),
      tool: i.string().optional(),
      language: i.string().optional(),
    }),
    transcriptionSegments: i.entity({
      start: i.number(),
      end: i.number(),
      text: i.string(),
      // Words are stored as a JSON blob for simplicity and performance
      // Structure: Array<{ word: string, start: number, end: number }>
      words: i.json().optional(),
      index: i.number().indexed(), // To order segments
    }),
    speakers: i.entity({
      name: i.string(),
      is_generated: i.boolean().optional(), // True if computer generated
      voice_id: i.string().optional(), // For 11labs or similar
      metadata: i.json().optional(),
    }),
    logs: i.entity({
      created_at: i.string().indexed(),
      level: i.string(),
      message: i.string(),
      job_id: i.string().optional(),
    }),
  },
  links: {
    $usersLinkedPrimaryUser: {
      forward: {
        on: "$users",
        has: "one",
        label: "linkedPrimaryUser",
        onDelete: "cascade",
      },
      reverse: {
        on: "$users",
        has: "many",
        label: "linkedGuestUsers",
      },
    },
    jobsVideo: {
      forward: {
        on: "jobs",
        has: "many",
        label: "video",
      },
      reverse: {
        on: "videos",
        has: "many",
        label: "jobs",
      },
    },
    jobsLogs: {
      forward: {
        on: "jobs",
        has: "many",
        label: "logs",
      },
      reverse: {
        on: "logs",
        has: "one",
        label: "job",
      },
    },
    // Domain Links
    channelsVideos: {
      forward: {
        on: "channels",
        has: "many",
        label: "videos",
      },
      reverse: {
        on: "videos",
        has: "one",
        label: "channel",
      },
    },
    videosTranscriptions: {
      forward: {
        on: "videos",
        has: "many", // Allowing multiple versions/models
        label: "transcriptions",
      },
      reverse: {
        on: "transcriptions",
        has: "one",
        label: "video",
      },
    },
    transcriptionsSegments: {
      forward: {
        on: "transcriptions",
        has: "many",
        label: "segments",
      },
      reverse: {
        on: "transcriptionSegments",
        has: "one",
        label: "transcription",
      },
    },
    segmentsSpeakers: {
      forward: {
        on: "transcriptionSegments",
        has: "one",
        label: "speaker",
      },
      reverse: {
        on: "speakers",
        has: "many",
        label: "segments",
      },
    },
  },
  rooms: {},
});

// This helps Typescript display nicer intellisense
type _AppSchema = typeof _schema;
interface AppSchema extends _AppSchema {}
const schema: AppSchema = _schema;

export type { AppSchema };
export default schema;
