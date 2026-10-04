# Instagram Growth Engine

## Status

Design/specification branch for a verifier-first Instagram content workflow.

This document does **not** claim that Instagram reach or virality can be guaranteed. It defines a repeatable optimization loop that maximizes the probability of non-follower distribution while keeping publication side effects explicit and verifiable.

## Core loop

RAW MEDIA → CURATE → EDIT → QUALITY GATE → PACKAGE → PUBLISH → MEASURE → VERIFY → LEARN → NEXT CREATIVE

## 1. Curate

Rank assets on visual hook strength, subject clarity, personal-brand fit, emotional signal, composition, novelty versus recent posts, image quality, and sequence compatibility.

For a carousel, prefer: Hook/identity → environment → human connection → lifestyle/fitness identity → emotional beat → visual variation → movement → quiet closer.

Do not select near-duplicate frames simply to increase carousel length.

## 2. Quality gate

Masters must preserve original pixel dimensions, avoid unnecessary crop, avoid repeated JPEG recompression, preserve available EXIF/ICC metadata, keep an untouched source copy, and create delivery assets separately from masters.

Report source dimensions, output dimensions, crop applied, resize applied, format, compression mode, and metadata preservation.

## 3. Content packaging

Generate two candidate surfaces when the source supports both:

- Carousel: primary objective is profile conversion and brand identity.
- Reel: primary objective is non-follower discovery.

A Reel must not be a mechanically exported slideshow of the carousel. Re-cut the source as motion-first creative with an immediate opening frame.

## 4. Discovery strategy

Avoid hashtag stuffing. Use a small set of relevant classification signals: creator identity, niche, content theme, location when materially relevant, and audio identity.

Example for the current luxury/lifestyle shoot: #KaranAujla #LuxuryLifestyle #TravelCouple #FitnessLifestyle #CinematicPhotography

Hashtags are supporting metadata, not the primary growth mechanism.

## 5. Primary experiment metrics

For discovery, prioritize:

1. non-follower reach / total reach
2. shares / reach
3. saves / reach
4. profile visits / reach
5. follows / profile visits

Likes and comments remain useful but should not be treated as the sole success metric.

## 6. Experiment record

Every publication should produce: content_id, source_asset_ids, selected_asset_ids, edit_version, surface, caption_version, audio, hashtag_set, publish_timestamp, publication_status, publication_verification, total_reach, non_follower_reach, views, likes, comments, shares, saves, profile_visits, follows, and experiment_verdict.

## 7. Verifier rules

Publication is an external side effect. Never treat a cached generation result as proof that Instagram publication occurred.

API path: approved=true → create container → check container status → publish → read published media → compare returned media ID → VERIFIED only on matching read-back.

Native share path: source file → native share sheet → user selects Instagram → user completes Instagram post. Native share is user-controlled and does not provide publication verification.

## 8. Learning rule

Do not label a creative viral from one metric spike. A candidate should be considered a winner only when it improves the agreed discovery metric against a recent baseline with enough observations to avoid overfitting to a single post.

Verdicts: WIN, PROMISING, NEUTRAL, LOSS, UNKNOWN.

## 9. Account baseline

Public third-party account data may be used only as contextual baseline and must not be treated as first-party Instagram Insights.

Required first-party fields: follower count, non-follower reach, accounts reached, Reel watch time/average watch time, shares, saves, profile activity, and follows attributable to content.

## 10. Integrity

Never buy followers or engagement, use fake comments, automate unsolicited DMs, spam hashtags, impersonate engagement, claim verified publication without evidence, or claim virality without measurement.

The growth engine optimizes legitimate content distribution and learning, not artificial engagement.

## CATCH integration boundary

The existing CATCH Instagram implementation already defines native sharing and a verified API publication boundary. The growth layer should sit above that boundary:

creative planner → CATCH publication boundary → Instagram → first-party metrics → evaluator

Instagram side effects remain outside the reusable CATCH cache.

## Current implementation gap

CATCH currently has publication support but does not yet expose a first-party Instagram analytics ingestion/evaluation loop in this branch. That should be implemented only after authorized Meta/Instagram Insights access is available.

## Next implementation phases

### Phase A
- deterministic content package schema
- quality-gate result schema
- experiment record schema
- discovery score calculation

### Phase B
- authorized Instagram Insights ingestion
- post/Reel metric normalization
- baseline comparison
- experiment verdicts

### Phase C
- automated creative recommendations
- caption/audio/hashtag candidate ranking
- Reel vs carousel recommendation
- verifier-backed publishing workflow

### Phase D
- longitudinal learning across content
- audience/topic clusters
- creative fatigue detection
- controlled experiments

## Non-goal

The system cannot guarantee virality. The objective is measurable improvement in the probability of recommendation and non-follower distribution while preserving authenticity, image quality, and verifiable side effects.