import { init, i, id, InstaQLEntity } from "@instantdb/core";
import Fuse from "fuse.js";

// Instant app
const APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d";

// Schema Definition
const schema = i.schema({
  entities: {
    videos: i.entity({
      title: i.string().optional(),
      original_url: i.string().optional(),
      platform: i.string().optional(),
      external_id: i.string().unique().optional(),
      duration: i.number().optional(),
      upload_date: i.string().optional(),
      channel: i.string().optional(),
      created_at: i.string().indexed().optional(),
      audio_path: i.string().optional(),
    }),
    jobs: i.entity({
      type: i.string().optional(),
      progress: i.string().optional(),
      error: i.any().optional(),
      created_at: i.string().indexed().optional(),
    }),
    logs: i.entity({
      level: i.string(),
      message: i.string(),
      created_at: i.string().indexed(),
      job_id: i.string().optional(),
    }),
    transcriptions: i.entity({
      path: i.string(),
      created_at: i.string(),
      model: i.string().optional(),
      tool: i.string().optional(),
    }),
  },
  links: {
    jobsVideo: {
      forward: { on: "jobs", has: "many", label: "video" },
      reverse: { on: "videos", has: "many", label: "jobs" },
    },
    videosTranscriptions: {
      forward: { on: "videos", has: "many", label: "transcriptions" },
      reverse: { on: "transcriptions", has: "one", label: "video" },
    },
    jobsLogs: {
      forward: { on: "jobs", has: "many", label: "logs" },
      reverse: { on: "logs", has: "one", label: "job" },
    },
  },
});

type Video = InstaQLEntity<typeof schema, "videos">;
type Job = InstaQLEntity<typeof schema, "jobs">;
type Log = InstaQLEntity<typeof schema, "logs">;

// Initialize the database
const db = init({ appId: APP_ID, schema });

// State
let currentVideoId: string | null = null;
let player: any = null;
let fuse: any = null;
let activeSegmentIndex = -1;
let userScrolled = false;
let isAutoScrolling = false;
let segments: any[] = [];

// Styles
const styles = {
  container: `
    box-sizing: border-box;
    background-color: #fafafa;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    min-height: 100vh;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  `,
  header: `
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  `,
  section: `
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  `,
  input: `
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    margin-right: 1rem;
    font-size: 1rem;
  `,
  button: `
    background-color: #2563eb;
    color: white;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-weight: 600;
    cursor: pointer;
  `,
  videoList: `
    display: flex;
    flex-direction: column;
    gap: 1rem;
  `,
  videoItem: `
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
  `,
  videoTitle: `
    font-weight: 600;
    color: #2563eb;
    text-decoration: none;
    font-size: 1.1rem;
  `,
  meta: `
    color: #6b7280;
    font-size: 0.875rem;
    margin-top: 0.5rem;
  `,
  logContainer: `
    background: #1f2937;
    color: #e5e7eb;
    padding: 1rem;
    border-radius: 6px;
    font-family: monospace;
    height: 300px;
    overflow-y: auto;
    font-size: 0.875rem;
  `,
  logEntry: `
    margin-bottom: 0.25rem;
    border-bottom: 1px solid #374151;
    padding-bottom: 0.25rem;
  `,
  badge: `
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
  `,
  playerContainer: `
    display: flex;
    height: 80vh;
    gap: 2rem;
  `,
  videoFrame: `
    flex: 1;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
  `,
  transcriptContainer: `
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    height: 100%;
  `,
  segment: `
    margin-bottom: 1rem;
    padding: 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;
  `,
  timestamp: `
    font-weight: bold;
    color: #2563eb;
    margin-right: 0.5rem;
    font-size: 0.9rem;
  `,
  text: `
    line-height: 1.6;
  `,
  backButton: `
    background: none;
    border: none;
    color: #2563eb;
    cursor: pointer;
    font-size: 1rem;
    text-decoration: underline;
  `,
};

// Render
const app = document.getElementById("app")!;
app.style.cssText = styles.container;

function render(data: { videos?: Video[]; jobs?: Job[]; logs?: Log[] }) {
  const { videos = [], jobs = [], logs = [] } = data;

  if (currentVideoId) {
    const video = videos.find(v => v.id === currentVideoId);
    if (video) {
      renderPlayer(video);
      return;
    }
  }

  // Dashboard View
  app.innerHTML = "";

  // Filter Jobs
  const activeJobs = jobs.filter(job => 
    !job.error && job.progress !== "Completed" && job.progress !== "Finished"
  );

  // Filter Videos
  const validVideos = videos.filter(video => 
    video.external_id && video.title !== "Pending..." && video.platform !== "unknown"
  ).sort((a, b) => 
    new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  );

  // Sort logs
  const sortedLogs = [...logs].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const html = `
    <div style="${styles.header}">Transcribed Videos</div>
    
    <div style="${styles.section}">
      <h3 style="margin-top: 0; margin-bottom: 1rem;">Add New Video</h3>
      <form id="add-video-form" style="display: flex;">
        <input type="text" style="${styles.input}" placeholder="Paste YouTube URL here..." required>
        <button type="submit" style="${styles.button}">Transcribe</button>
      </form>
    </div>

    <div style="${styles.section}">
      <h3 style="margin-top: 0; margin-bottom: 1rem;">Active Jobs</h3>
      ${JobsList(activeJobs)}
    </div>

    <div style="${styles.section}">
      <h3 style="margin-top: 0; margin-bottom: 1rem;">Recent Videos</h3>
      ${VideoList(validVideos)}
    </div>

    <div style="${styles.section}">
      <h3 style="margin-top: 0; margin-bottom: 1rem;">Live Logs 📜</h3>
      <div style="${styles.logContainer}">
        ${sortedLogs.map(LogEntry).join("")}
      </div>
    </div>
  `;

  app.innerHTML = html;

  // Event Listeners
  document.getElementById("add-video-form")?.addEventListener("submit", handleSubmit);
  
  // Attach click handlers for videos
  validVideos.forEach(video => {
    document.getElementById(`video-${video.id}`)?.addEventListener("click", () => {
      currentVideoId = video.id;
      // Re-render handled by subscription update or manual trigger?
      // Since we are inside render, we need to trigger a re-render.
      // But we are inside the subscription callback usually.
      // Let's force a re-render by calling render with current data?
      // Or better, just let the next update handle it? 
      // Actually, we need to fetch the transcription data for the player.
      // Let's just set the ID and let the subscription handle it if we change the query.
      // But we are using a single query for everything right now.
      // So we can just call render again.
      render(data);
    });
  });
}

function JobsList(jobs: Job[]) {
  if (jobs.length === 0) return `<div style="color: #6b7280;">No active jobs</div>`;
  
  return jobs.map(job => {
    let badgeColor = "#3b82f6"; // blue
    if (job.error) badgeColor = "#ef4444"; // red
    else if (job.progress === "Completed") badgeColor = "#10b981"; // green

    return `
      <div style="${styles.videoItem}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 600;">${job.type}</span>
          <span style="${styles.badge}; background-color: ${badgeColor}; color: white;">
            ${job.error ? "Error" : job.progress || "Pending"}
          </span>
        </div>
        <div style="${styles.meta}">ID: ${job.id} | Created: ${new Date(job.created_at || "").toLocaleString()}</div>
        ${job.error ? `<div style="color: #ef4444; margin-top: 0.5rem; font-size: 0.875rem;">${JSON.stringify(job.error)}</div>` : ""}
      </div>
    `;
  }).join("");
}

function VideoList(videos: Video[]) {
  if (videos.length === 0) return `<div style="color: #6b7280;">No videos found</div>`;

  return `
    <div style="${styles.videoList}">
      ${videos.map(video => `
        <div id="video-${video.id}" style="${styles.videoItem}">
          <div style="${styles.videoTitle}">${video.title || "Untitled"}</div>
          <div style="${styles.meta}">
            Platform: ${video.platform} | ID: ${video.external_id} | Uploaded: ${video.upload_date || "Unknown"}
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function LogEntry(log: Log) {
  const color = log.level === "error" ? "#ef4444" : log.level === "warn" ? "#f59e0b" : "#9ca3af";
  return `
    <div style="${styles.logEntry}">
      <span style="color: ${color}; margin-right: 0.5rem;">[${new Date(log.created_at).toLocaleTimeString()}]</span>
      <span style="color: ${color}; font-weight: bold; margin-right: 0.5rem;">${log.level.toUpperCase()}:</span>
      ${log.message}
    </div>
  `;
}

function handleSubmit(e: Event) {
  e.preventDefault();
  const input = (e.target as HTMLFormElement).querySelector("input");
  if (!input || !input.value.trim()) return;

  const url = input.value.trim();
  const videoId = id();
  const jobId = id();
  
  db.transact([
    db.tx.videos[videoId].update({
      original_url: url,
      created_at: new Date().toISOString(),
      title: "Pending...",
      platform: "unknown",
    }),
    db.tx.jobs[jobId].update({
      type: "video_download",
      progress: "Queued",
      created_at: new Date().toISOString(),
    }),
    db.tx.jobs[jobId].link({ video: videoId }),
  ]);

  input.value = "";
}

// Player Logic
function renderPlayer(video: Video) {
  // Fetch transcriptions for this video
  // We need to query specifically for this video's transcriptions
  // Since we can't easily do async fetch inside render, we should rely on the main subscription
  // to fetch *all* transcriptions or fetch them on demand.
  // Fetching all might be heavy.
  // Let's use a separate query for the player?
  // But db.subscribeQuery is global.
  // For now, let's assume we have the transcriptions linked in the video object if we query with relations.
  
  // Wait, the initial query `videos: {}` doesn't fetch relations unless specified.
  // We need to update the subscription query when `currentVideoId` changes.
  
  // Let's handle this in the subscription logic below.
  
  // For now, render the skeleton.
  app.innerHTML = `
    <div style="${styles.header}">
      <button id="back-button" style="${styles.backButton}">← Back</button>
      <span style="flex:1; margin-left: 1rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${video.title}</span>
      <input type="text" id="searchInput" placeholder="Search transcript..." style="${styles.input}; width: 300px;">
    </div>
    
    <div style="${styles.playerContainer}">
      <div style="${styles.videoFrame}">
        <div id="player"></div>
      </div>
      <div id="transcript" style="${styles.transcriptContainer}">
        Loading transcript...
      </div>
    </div>
  `;

  document.getElementById("back-button")?.addEventListener("click", () => {
    currentVideoId = null;
    // Trigger update
    updateSubscription();
  });
  
  document.getElementById("searchInput")?.addEventListener("input", (e) => {
    const query = (e.target as HTMLInputElement).value;
    if (!query) {
      renderSegments(segments);
      return;
    }
    const results = fuse.search(query);
    renderSegments(results.map((r: any) => r.item));
  });

  // Initialize YouTube Player
  if (video.platform === 'youtube' && video.external_id) {
    initYouTubePlayer(video.external_id);
  } else {
    document.getElementById('player')!.innerHTML = '<div style="color:white;">Player not supported for this platform</div>';
  }
}

function renderSegments(segmentsToRender: any[]) {
  const transcriptEl = document.getElementById('transcript');
  if (!transcriptEl) return;
  
  transcriptEl.innerHTML = '';
  
  if (segmentsToRender.length === 0) {
    transcriptEl.innerHTML = '<div style="color:#666;">No matches found.</div>';
    return;
  }

  function formatTime(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  segmentsToRender.forEach((seg) => {
    const div = document.createElement('div');
    // We need to map back to original index for ID
    const originalIndex = segments.indexOf(seg);
    
    div.style.cssText = styles.segment;
    div.id = `seg-${originalIndex}`;
    div.onclick = () => seekTo(seg.start);
    
    // Highlight active
    if (originalIndex === activeSegmentIndex) {
      div.style.backgroundColor = "#e6f7ff";
      div.style.borderLeft = "4px solid #1890ff";
    }
    
    div.innerHTML = `
      <span style="${styles.timestamp}">${formatTime(seg.start)}</span>
      <span style="${styles.text}">${seg.text}</span>
    `;
    transcriptEl.appendChild(div);
  });
}

function initYouTubePlayer(videoId: string) {
  if ((window as any).YT) {
    createPlayer(videoId);
  } else {
    const tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag);
    (window as any).onYouTubeIframeAPIReady = () => createPlayer(videoId);
  }
}

function createPlayer(videoId: string) {
  player = new (window as any).YT.Player('player', {
    height: '100%',
    width: '100%',
    videoId: videoId,
    events: {
      'onReady': onPlayerReady
    }
  });
}

function onPlayerReady() {
  startSyncLoop();
}

function seekTo(seconds: number) {
  if (player && player.seekTo) {
    player.seekTo(seconds, true);
    player.playVideo();
    userScrolled = false;
  }
}

function startSyncLoop() {
  setInterval(() => {
    if (!player || !player.getCurrentTime) return;
    
    const time = player.getCurrentTime();
    
    let currentIdx = -1;
    for (let i = 0; i < segments.length; i++) {
      if (time >= segments[i].start && time < segments[i].end) {
        currentIdx = i;
        break;
      }
      if (time >= segments[i].start) {
        currentIdx = i;
      }
    }
    
    if (currentIdx !== -1 && currentIdx !== activeSegmentIndex) {
      // Update UI
      const prev = document.getElementById(`seg-${activeSegmentIndex}`);
      if (prev) {
        prev.style.backgroundColor = "";
        prev.style.borderLeft = "";
      }
      
      const activeEl = document.getElementById(`seg-${currentIdx}`);
      if (activeEl) {
        activeEl.style.backgroundColor = "#e6f7ff";
        activeEl.style.borderLeft = "4px solid #1890ff";
        
        if (!userScrolled && !(document.getElementById('searchInput') as HTMLInputElement)?.value) {
          isAutoScrolling = true;
          activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          setTimeout(() => { isAutoScrolling = false; }, 500);
        }
      }
      activeSegmentIndex = currentIdx;
    }
    
  }, 200);
}

document.addEventListener('scroll', (e) => {
  if ((e.target as HTMLElement).id === 'transcript' && !isAutoScrolling) {
    userScrolled = true;
  }
}, true);


// Subscription Management
let unsubscribe: (() => void) | null = null;

function updateSubscription() {
  if (unsubscribe) unsubscribe();

  const query: any = {
    jobs: { $: { limit: 50, order: { created_at: "desc" } } },
    logs: { $: { limit: 50, order: { created_at: "desc" } } }
  };

  if (currentVideoId) {
    // Fetch specific video with transcriptions
    query.videos = { 
      $: { where: { id: currentVideoId } },
      transcriptions: {} 
    };
  } else {
    // Fetch all videos for dashboard
    query.videos = { $: { limit: 50, order: { created_at: "desc" } } };
  }

  // @ts-ignore
  unsubscribe = db.subscribeQuery(query, (resp: any) => {
    if (resp.error) {
      console.error(resp.error);
      return;
    }
    if (resp.data) {
      if (currentVideoId && resp.data.videos && resp.data.videos.length > 0) {
        const video = resp.data.videos[0];
        console.log("Video data:", video);
        // Check if we have transcriptions
        if (video.transcriptions && video.transcriptions.length > 0) {
           const trans = video.transcriptions[0];
           console.log("Fetching transcript from:", trans.path);
           
           if (segments.length === 0) {
             fetch(trans.path).then(r => {
               console.log("Fetch response:", r.status, r.statusText);
               return r.json();
             }).then(data => {
               segments = data;
               fuse = new Fuse(segments, {
                 keys: ['text'],
                 includeMatches: true,
                 threshold: 0.2,
                 ignoreLocation: true,
                 minMatchCharLength: 3
               });
               renderSegments(segments);
             }).catch(e => {
               console.error("Failed to load transcript", e);
               document.getElementById('transcript')!.innerHTML = "Failed to load transcript file. Is it served?";
             });
           }
        }
      }
      
      render(resp.data);
    }
  });
}

// Initial Subscription
updateSubscription();
