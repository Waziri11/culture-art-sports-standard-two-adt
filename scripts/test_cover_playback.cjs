// Run with: node --test scripts/test_cover_playback.cjs
// Exercise the actual media coordinator with the published page/audio metadata.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/sign-language-sync.js'), 'utf8');
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
const clips = read('cover-audio-report.json').clips;

async function reader(href, videoDuration, describeImages = false) {
  const html = fs.readFileSync(path.join(root, href), 'utf8');
  const nodes = [...html.matchAll(/<(\w+)\b[^>]*\bdata-id="([^"]+)"[^>]*>/g)].map((match) => ({
    tagName: match[1].toUpperCase(),
    getAttribute: (name) => name === 'data-id' ? match[2] : null,
    closest: () => null,
  }));
  const cover = /data-section-type="(?:front_cover|back_cover)"/.test(html);
  const storage = new Map([['audioSpeed', '1'], ['describeImagesMode', JSON.stringify(describeImages)]]);
  const timers = [];
  class Events {
    constructor() { this.handlers = new Map(); }
    addEventListener(name, callback) {
      if (!this.handlers.has(name)) this.handlers.set(name, []);
      this.handlers.get(name).push(callback);
    }
    emit(name, target = this) {
      for (const callback of this.handlers.get(name) || []) {
        callback({ target, stopImmediatePropagation() {} });
      }
    }
  }
  let window;
  class Media extends Events {
    constructor(src = '') {
      super();
      this.src = src; this.currentTime = 0; this.duration = 1;
      this.readyState = 4; this.paused = true; this.ended = false;
      this.rate = 1; this.playCount = 0;
    }
    get playbackRate() { return this.rate; }
    set playbackRate(value) { this.rate = value; this.emit('ratechange'); }
    play() {
      this.playCount++; this.paused = false; this.ended = false;
      window.emit('play', this); this.emit('play'); this.emit('playing');
      return Promise.resolve();
    }
    pause() { this.paused = true; this.emit('pause'); }
    load() {}
  }
  class Audio extends Media {}
  class Video extends Media {}
  window = new Events();
  Object.assign(window, { Audio, HTMLMediaElement: Media });
  const document = {
    baseURI: `http://localhost/${href}`,
    documentElement: { lang: 'en' },
    querySelectorAll: (selector) => selector === '#content [data-id]' ? nodes : [],
    querySelector: (selector) => selector.includes('data-section-type=') && cover ? {} : null,
    contains: () => true,
  };
  const context = vm.createContext({
    window, document, HTMLVideoElement: Video, HTMLAudioElement: Audio, URL, console,
    localStorage: { getItem: (key) => storage.get(key) ?? null },
    MutationObserver: class { observe() {} disconnect() {} },
    fetch: async (url) => ({ ok: true, json: async () => read(url.split('?')[0]) }),
    setTimeout: (fn) => { timers.push(fn); },
    setInterval: () => 1, clearInterval() {},
  });
  vm.runInContext(source, context);
  const coordinator = window.__adtAccessibleMediaSync;
  const audio = new window.Audio();
  const video = new Video('./content/i18n/en/video/page_1.mp4');
  video.duration = videoDuration;
  const audios = read('content/i18n/en/audios.json');
  audio.src = `./content/i18n/en/audio/${audios[nodes[0].getAttribute('data-id')]}`;
  const settle = async () => {
    // Flush metadata promises and the coordinator's queued rate-change handler.
    for (let i = 0; i < 12; i++) {
      await Promise.resolve();
      for (const timer of timers.splice(0)) timer();
    }
  };
  await video.play();
  await audio.play();
  await settle();
  assert.ok(coordinator.state.plan?.totalDuration > 0);
  return {
    audio, video, settle, coordinator,
    async speed(value) {
      storage.set('audioSpeed', JSON.stringify(value));
      audio.playbackRate = value; // What the reader's speed selector does.
      await settle();
    },
  };
}

for (const [href, duration, prefix] of [
  ['index.html', 16.68, 'page_1_'],
  ['pg073_sec001.html', 9.88, 'page_116_'],
]) {
  for (const descriptions of [false, true]) {
    test(`${href}: selected narration speed is exact; image descriptions ${descriptions}`, async () => {
      const book = await reader(href, duration, descriptions);
      for (const speed of [1, 0.5, 1.5, 2, 1]) {
        await book.speed(speed);
        assert.equal(book.audio.playbackRate, speed, 'Video length must not multiply narration speed');
        assert.equal(book.video.playbackRate, speed);
        book.video.currentTime = 2;
        book.audio.currentTime = 1;
        book.audio.emit('timeupdate');
        assert.equal(book.video.currentTime, 2, 'Cover video must retain its own timeline');
        for (const clip of clips.filter((c) => c.filename.startsWith(prefix))) {
          book.audio.src = `./content/i18n/en/audio/${clip.filename}`;
          book.audio.currentTime = 0;
          book.audio.playbackRate = speed;
          await book.audio.play();
          await book.settle();
          assert.equal(book.audio.playbackRate, speed, clip.filename);
        }
      }
    });
  }
  test(`${href}: later narration does not restart a finished cover video`, async () => {
    const book = await reader(href, duration);
    book.video.currentTime = duration; book.video.ended = true; book.video.paused = true;
    const count = book.video.playCount;
    book.audio.src = `./content/i18n/en/audio/${clips.filter((c) => c.filename.startsWith(prefix))[1].filename}`;
    await book.audio.play(); await book.settle();
    assert.equal(book.video.playCount, count);
    assert.equal(book.audio.playbackRate, 1);
    book.audio.src = `./content/i18n/en/audio/${clips.find((c) => c.filename.startsWith(prefix)).filename}`;
    book.audio.currentTime = 0;
    await book.audio.play(); await book.settle();
    assert.equal(book.video.currentTime, 0, 'A new read-through can replay the cover video');
    assert.equal(book.video.playCount, count + 1);
  });
}

test('The existing title page keeps its synchronized media rates', async () => {
  const book = await reader('pg001_sec001.html', 92);
  for (const speed of [0.5, 1, 1.5, 2]) {
    await book.speed(speed);
    const expected = Math.max(0.25, Math.min(4, book.coordinator.state.plan.totalDuration / 92 * speed));
    assert.equal(book.audio.playbackRate, expected);
  }
});
