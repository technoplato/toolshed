// Docs: https://www.instantdb.com/docs/modeling-data

import { i } from "@instantdb/core";

const _schema = i.schema({
  // We inferred 15 attributes!
  // Take a look at this schema, and if everything looks good,
  // run `push schema` again to enforce the types.
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
    goals: i.entity({
      is_meta: i.boolean().optional(),
      recursion_level: i.string().optional(),
      rogue: i.string().optional(),
      self_referential: i.boolean().optional(),
      title: i.string().optional(),
    }),
    jobs: i.entity({
      created_at: i.string().indexed().optional(),
      error: i.any().optional(),
      progress: i.string().optional(),
      type: i.string().optional(),
    }),
    videos: i.entity({
      channel: i.string().optional(),
      created_at: i.string().indexed().optional(),
      duration: i.number().optional(),
      original_url: i.string().optional(),
      platform: i.string().optional(),
      title: i.string().optional(),
      upload_date: i.string().optional(),
      external_id: i.string().unique().optional(),
      audio_path: i.string().optional(),
    }),
    transcriptions: i.entity({
      path: i.string(),
      created_at: i.string(),
      model: i.string().optional(),
      tool: i.string().optional(),
    }),
    logs: i.entity({
      created_at: i.string().indexed(),
      level: i.string(),
      message: i.string(),
      job_id: i.string().optional(),
    }),
    todos: i.entity({
      title: i.string().optional(),
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
    goalsTodos: {
      forward: {
        on: "goals",
        has: "many",
        label: "todos",
      },
      reverse: {
        on: "todos",
        has: "many",
        label: "goals",
      },
    },
    videosTranscriptions: {
      forward: {
        on: "videos",
        has: "many",
        label: "transcriptions",
      },
      reverse: {
        on: "transcriptions",
        has: "one",
        label: "video",
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
  },
  rooms: {},
});

// This helps Typescript display nicer intellisense
type _AppSchema = typeof _schema;
interface AppSchema extends _AppSchema {}
const schema: AppSchema = _schema;

export type { AppSchema };
export default schema;
