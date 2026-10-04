# Instagram Growth Engine

## Purpose

A verifier-first workflow for improving the probability of Instagram non-follower distribution without artificial engagement or hashtag stuffing. This is an optimization system, not a promise of virality.

## Core loop

RAW MEDIA → CURATE → EDIT → QUALITY GATE → PACKAGE → PUBLISH → MEASURE → VERIFY → LEARN → NEXT CREATIVE

## Curation

Rank source assets by visual hook strength, subject clarity, personal-brand fit, emotional signal, composition, novelty versus recent posts, image quality, and sequence compatibility.

For carousels prefer:
1. Hook / identity
2. Environment
3. Human connection
4. Lifestyle / fitness identity
5. Emotional beat
6. Visual variation
7. Movement
8. Quiet closer

Do not select near-duplicates only to increase carousel length.

## Quality gate

Masters must preserve original pixel dimensions, avoid unnecessary crops, avoid repeated JPEG recompression, preserve available EXIF/ICC metadata, keep untouched source copies, and create delivery assets separately.

Report source dimensions, output dimensions, crop applied, resize applied, format, compression mode, and metadata preservation.

## Packaging

When the source supports both:
- Carousel: optimize for profile conversion and brand identity.
- Reel: optimize for non-follower discovery.

A Reel should be a motion-first re-cut, not a mechanical carousel slideshow.

## Discovery

Use a small set of relevant classification signals: creator identity, niche, content theme, location when materially relevant, and audio identity.

Example current package:
#KaranAujla #LuxuryLifestyle #TravelCouple #FitnessLifestyle #CinematicPhotography

Hashtags are supporting metadata, not the primary growth mechanism.

## Primary experiment metrics

Prioritize:
1. non-follower reach / total reach
2. shares / reach
3. saves / reach
4. profile visits / reach
5. follows / profile visits

Likes and comments remain useful but are not the sole success metric.

## Experiment record

Every publication should record:
- content_id
- source_asset_ids
- selected_asset_ids
- edit_version
- surface
- caption_version
- audio
- hashtag_set
- publish_timestamp
- publication_status
- publication_verification
- total_reach
- non_follower_reach
- views
- likes
- comments
- shares
- saves
- profile_visits
- follows
- experiment_verdict

## Verifier rules

Instagram publication is an external side effect. A cached generation result is never proof that publication occurred.

API path:
approved=true → create container → status check → publish → read published media → compare media ID → VERIFIED only on matching read-back.

Native path:
source file → native share sheet → user selects Instagram → user completes post.

Native sharing is user-controlled and does not prove publication.

## Learning

Do not label a creative viral from one metric spike. Compare against a recent baseline and require enough observations to avoid overfitting.

Verdicts:
- WIN
- PROMISING
- NEUTRAL
- LOSS
- UNKNOWN

## Account analytics boundary

Public third-party account data may be contextual only. It is not a substitute for first-party Instagram Insights.

For first-party optimization, ingest follower count, non-follower reach, accounts reached, Reel watch time/average watch time, shares, saves, profile activity, and follows attributable to content.

## CATCH integration

Existing CATCH Instagram support defines native sharing and a verified API publication boundary. The growth layer should sit above it:

creative planner → CATCH publication boundary → Instagram → first-party metrics → evaluator

Instagram side effects remain outside the reusable CATCH cache.

## Implementation phases

### Phase A
- content package schema
- quality-gate result schema
- experiment record schema
- discovery score calculation

### Phase B
- authorized Instagram Insights ingestion
- post/Reel metric normalization
- baseline comparison
- experiment verdicts

### Phase C
- caption/audio/hashtag candidate ranking
- Reel vs carousel recommendation
- verifier-backed publishing workflow
- creative recommendations

### Phase D
- longitudinal learning
- audience/topic clusters
- creative fatigue detection
- controlled experiments

## Integrity rules

Never buy followers or engagement, use fake comments, automate unsolicited DMs, spam hashtags, impersonate engagement, claim verified publication without evidence, or claim virality without measurement.

## Non-goal

The system cannot guarantee virality. The objective is measurable improvement in the probability of recommendation and non-follower distribution while preserving authenticity, image quality, and verifiable side effects.
