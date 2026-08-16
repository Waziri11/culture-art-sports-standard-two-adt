(function () {
  "use strict";

  if (window.__adtAccessibleMediaSync) return;

  const NativeAudio = window.Audio;
  const mediaPrototype = window.HTMLMediaElement.prototype;
  const nativePlay = mediaPrototype.play;
  const nativePause = mediaPrototype.pause;
  const nativeLoad = mediaPrototype.load;
  const state = {
    video: null,
    audio: null,
    plan: null,
    planPromise: null,
    planSignature: null,
    syncRequested: false,
    transitioning: false,
    correcting: false,
    settingRates: false,
  };

  const EASY_READ_EXCLUDED =
    ".word-card, [data-activity-item], nav, .nav__list, button, input, textarea, select, option";

  function storedBoolean(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      if (raw === null) return fallback;
      const value = JSON.parse(raw);
      return typeof value === "boolean" ? value : raw === "true";
    } catch (_error) {
      return fallback;
    }
  }

  function storedNumber(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      if (raw === null) return fallback;
      const value = Number(JSON.parse(raw));
      return Number.isFinite(value) && value > 0 ? value : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function filenameFromUrl(value) {
    if (!value) return "";
    try {
      return decodeURIComponent(new URL(value, document.baseURI).pathname.split("/").pop() || "");
    } catch (_error) {
      return value.split("/").pop() || "";
    }
  }

  function isSignVideo(media) {
    return (
      media instanceof HTMLVideoElement &&
      /\/content\/i18n\/[^/]+\/video\//.test(media.currentSrc || media.src || "")
    );
  }

  function isBookAudio(media) {
    return (
      media instanceof HTMLAudioElement &&
      /\/content\/i18n\/[^/]+\/audio\//.test(media.currentSrc || media.src || "")
    );
  }

  function language() {
    return document.documentElement.lang || "en";
  }

  function currentPlanSignature() {
    return JSON.stringify({
      language: language(),
      easyRead: storedBoolean("easyReadMode", false),
      describeImages: storedBoolean("describeImagesMode", false),
    });
  }

  async function buildPlan() {
    const lang = language();
    const base = `./content/i18n/${lang}`;
    const [audioResponse, textResponse, syncResponse] = await Promise.all([
      fetch(`${base}/audios.json`),
      fetch(`${base}/texts.json`),
      fetch(`${base}/media-sync.json`),
    ]);
    if (!audioResponse.ok || !textResponse.ok || !syncResponse.ok) {
      throw new Error("Unable to load synchronized-media metadata");
    }

    const [audioFiles, texts, sync] = await Promise.all([
      audioResponse.json(),
      textResponse.json(),
      syncResponse.json(),
    ]);
    const easyRead = storedBoolean("easyReadMode", false);
    const describeImages = storedBoolean("describeImagesMode", false);
    const tracks = [];

    document.querySelectorAll("#content [data-id]").forEach((element) => {
      if (!describeImages && element.tagName.toLowerCase() === "img") return;
      const id = element.getAttribute("data-id");
      if (!id) return;

      let filename = audioFiles[id];
      if (easyRead) {
        const isHeader = /^h[1-6]$/i.test(element.tagName);
        const excluded = element.closest(EASY_READ_EXCLUDED) !== null;
        const easyId = `${id}_easy_read`;
        if (!isHeader && !excluded && texts[easyId] !== undefined && audioFiles[easyId]) {
          filename = audioFiles[easyId];
        }
      }

      const duration = sync.audioDurations[filename];
      if (!filename || !Number.isFinite(duration) || duration <= 0) return;
      tracks.push({ filename, duration });
    });

    let offset = 0;
    const byFilename = new Map();
    tracks.forEach((track) => {
      if (!byFilename.has(track.filename)) {
        byFilename.set(track.filename, { offset, duration: track.duration });
      }
      offset += track.duration;
    });

    return { tracks, byFilename, totalDuration: offset };
  }

  function ensurePlan() {
    const signature = currentPlanSignature();
    if (state.planSignature !== signature) {
      state.plan = null;
      state.planPromise = null;
      state.planSignature = signature;
    }
    if (state.plan) return Promise.resolve(state.plan);
    if (!state.planPromise) {
      state.planPromise = buildPlan()
        .then((plan) => {
          state.plan = plan;
          return plan;
        })
        .catch((error) => {
          console.warn("[adt-media-sync]", error);
          return null;
        });
    }
    return state.planPromise;
  }

  function targetFor(audio, video, plan) {
    if (!audio || !video || !plan || plan.totalDuration <= 0 || !video.duration) return null;
    const track = plan.byFilename.get(filenameFromUrl(audio.currentSrc || audio.src));
    if (!track) return null;
    const pageTime = Math.min(plan.totalDuration, track.offset + audio.currentTime);
    return (pageTime / plan.totalDuration) * video.duration;
  }

  function baseVideoRate(audio, video, plan) {
    if (!audio || !video || !plan || plan.totalDuration <= 0 || !video.duration) return 1;
    return Math.max(0.25, Math.min(4, (video.duration / plan.totalDuration) * audio.playbackRate));
  }

  function synchronizeRates() {
    const audio = state.audio;
    const video = state.video;
    const plan = state.plan;
    if (!audio || !video || !plan || plan.totalDuration <= 0 || !video.duration) return;
    const requestedSpeed = Math.max(0.25, Math.min(4, storedNumber("audioSpeed", 1)));
    const audioRate = Math.max(
      0.25,
      Math.min(4, (plan.totalDuration / video.duration) * requestedSpeed),
    );
    state.settingRates = true;
    try {
      if (Math.abs(audio.playbackRate - audioRate) > 0.005) audio.playbackRate = audioRate;
      if (Math.abs(video.playbackRate - requestedSpeed) > 0.005) {
        video.playbackRate = requestedSpeed;
      }
    } finally {
      state.settingRates = false;
    }
  }

  function correctDrift() {
    const audio = state.audio;
    const video = state.video;
    const plan = state.plan;
    if (!audio || !video || !plan || audio.paused || video.readyState < 1) return;
    const target = targetFor(audio, video, plan);
    if (target === null) return;
    const drift = target - video.currentTime;
    const baseRate = baseVideoRate(audio, video, plan);
    if (Math.abs(drift) > 0.8) {
      state.correcting = true;
      try {
        video.currentTime = Math.max(0, Math.min(video.duration, target));
      } finally {
        state.correcting = false;
      }
      video.playbackRate = baseRate;
    } else {
      video.playbackRate = Math.max(0.25, Math.min(4, baseRate + drift * 0.04));
    }
  }

  function pauseVideo() {
    const video = state.video;
    if (video && !video.paused) nativePause.call(video);
  }

  function playVideoFromAudio() {
    const video = state.video;
    const audio = state.audio;
    if (!video || !audio || audio.paused) return;
    video.muted = true;
    video.controls = false;
    ensurePlan().then((plan) => {
      const filename = filenameFromUrl(audio.currentSrc || audio.src);
      if (!plan || !plan.byFilename.has(filename)) return;
      synchronizeRates();
      correctDrift();
      if (video.paused) nativePlay.call(video).catch(() => {});
    });
  }

  function registerAudio(audio) {
    if (audio.__adtSyncRegistered) return audio;
    Object.defineProperty(audio, "__adtSyncRegistered", { value: true });

    audio.addEventListener("play", () => {
      if (!isBookAudio(audio)) return;
      state.audio = audio;
      state.transitioning = false;
      if (state.video || state.syncRequested) playVideoFromAudio();
    });
    audio.addEventListener("playing", () => {
      if (!isBookAudio(audio)) return;
      state.audio = audio;
      state.transitioning = false;
      playVideoFromAudio();
    });
    audio.addEventListener("timeupdate", correctDrift);
    audio.addEventListener("ratechange", () => {
      if (state.settingRates) return;
      setTimeout(() => {
        synchronizeRates();
        correctDrift();
      }, 0);
    });
    audio.addEventListener("ended", () => {
      if (!isBookAudio(audio)) return;
      const plan = state.plan;
      const track = plan && plan.byFilename.get(filenameFromUrl(audio.currentSrc || audio.src));
      const finalTrack = track && track.offset + track.duration >= plan.totalDuration - 0.05;
      if (finalTrack && state.video) {
        state.correcting = true;
        try {
          state.video.currentTime = state.video.duration || state.video.currentTime;
        } finally {
          state.correcting = false;
        }
        pauseVideo();
      } else {
        state.transitioning = true;
        setTimeout(() => {
          if (state.audio === audio && audio.paused) pauseVideo();
          state.transitioning = false;
        }, 350);
      }
    });
    audio.addEventListener("pause", () => {
      if (!isBookAudio(audio) || audio.ended || state.transitioning) return;
      setTimeout(() => {
        if (state.audio === audio && audio.paused && !state.transitioning) pauseVideo();
      }, 120);
    });
    return audio;
  }

  function SyncedAudio(source) {
    return registerAudio(new NativeAudio(source));
  }
  SyncedAudio.prototype = NativeAudio.prototype;
  Object.setPrototypeOf(SyncedAudio, NativeAudio);
  window.Audio = SyncedAudio;

  mediaPrototype.pause = function () {
    if (
      isSignVideo(this) &&
      state.syncRequested &&
      state.audio &&
      !state.audio.paused
    ) {
      return;
    }
    return nativePause.call(this);
  };

  function startNarration() {
    if (state.audio && !state.audio.paused) return;
    const playButton = document.querySelector('button[aria-label="Play"]');
    if (playButton) {
      playButton.click();
      return;
    }
    const activateButton = Array.from(document.querySelectorAll("button")).find((button) =>
      /^(Activate|Deactivate) text to speech$/i.test(button.getAttribute("aria-label") || ""),
    );
    activateButton?.click();
  }

  window.addEventListener(
    "play",
    (event) => {
      const media = event.target;
      if (!isSignVideo(media)) return;
      event.stopImmediatePropagation();
      state.video = media;
      state.syncRequested = true;
      media.muted = true;
      media.controls = false;
      ensurePlan();
      setTimeout(startNarration, 0);
    },
    true,
  );

  window.addEventListener(
    "pause",
    (event) => {
      const media = event.target;
      if (!isSignVideo(media) || state.correcting) return;
      if (state.audio && !state.audio.paused) {
        setTimeout(playVideoFromAudio, 0);
      }
    },
    true,
  );

  const observer = new MutationObserver(() => {
    const video = Array.from(document.querySelectorAll("video")).find(isSignVideo) || null;
    if (video) {
      state.video = video;
      state.syncRequested = true;
      video.muted = true;
      video.controls = false;
    } else if (state.video && !document.contains(state.video)) {
      state.video = null;
      state.syncRequested = false;
    }
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  const correctionTimer = setInterval(correctDrift, 250);
  window.addEventListener(
    "beforeunload",
    () => {
      clearInterval(correctionTimer);
      observer.disconnect();
      mediaPrototype.pause = nativePause;
      window.Audio = NativeAudio;
    },
    { once: true },
  );

  window.__adtAccessibleMediaSync = {
    version: 1,
    state,
    nativePlay,
    nativePause,
    nativeLoad,
  };
})();
