# Culture, Art and Sports Standard Two

The accessible reader is served directly from this repository root. GitHub Pages
publishes `main` at https://waziri11.github.io/culture-art-sports-standard-two-adt/.

The 116 reader pages include the front cover at `index.html`, the title page at
`pg001_sec001.html`, and the back cover at `pg073_sec001.html`. Videos are named
`page_1.mp4` through `page_116.mp4`. Source text IDs stay stable so narration,
image descriptions, and printed page numbers remain attached to their content.

## Publishing

1. Update the canonical HTML and localization files, then advance `bundleVersion`
   and the changed assets' version query strings when making reader changes.
2. Run `python -B scripts/rebuild_offline_preloader.py`.
3. Run `node --test scripts/test_cover_playback.cjs`,
   `python -B scripts/validate_deployment.py`,
   `python -B scripts/validate_cover_media.py`, and
   `python -B scripts/validate_bilingual_audio.py` (Python UTF-8 mode is required
   on Windows; the cover validator uses `mutagen`).
4. Check desktop and mobile navigation, drawers, narration, and sign videos in
   the browser. Commit and push `main`, then verify the GitHub Pages deployment
   for that commit and smoke-test the live book.

No ZIP or SCORM package is needed for the web deployment. The existing LMS
bridge and manifest are retained for compatibility.

If navigation or media breaks after publishing, revert the release commit and
push the revert; GitHub Pages republishes the preceding reader. Keep source PDFs
and original compressed videos outside this deployment repository.

## Maintenance files

`scripts/` and its registers/reports retain narration provenance and validation
inputs. Generated reports that are no longer used by a validator can be removed.
`assets/tailwind_css.css` is stylesheet source; the reader loads the compiled
stylesheets. `assets/favicon_io/about.txt` contains required icon attribution.

The active reader runtime, UI stylesheet, and mobile drawer helpers come from
the Writing Standard 1 reference book. See `scripts/sync_responsive_toolbar.py`
and `responsive-toolbar-report.json` for their source and verification details.

Cover narration follows the playback selector directly: Slow 0.5×, Normal 1×,
Fast 1.5×, and Very fast 2×. The short cover videos retain their own timelines;
they do not determine narration speed. Interior pages keep their existing media
synchronization. `scripts/test_cover_playback.cjs` checks this distinction using
the real page and narration metadata, including image descriptions.
