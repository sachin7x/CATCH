# Instagram publishing

CATCH supports two photo-to-Instagram paths.

## 1. Native share

The web UI has a **Photo** button. On iPhone/iPad, selecting an image and pressing **Share to Instagram** uses the browser's native Web Share API with the image file. Instagram can then be selected as the share target.

This path does not require Meta credentials and does not silently publish. The user completes the post in Instagram.

## 2. Verified API publishing

The FastAPI runtime exposes:

`POST /api/instagram/publish`

Payload:

```json
{
  "image_url": "https://public.example/image.jpg",
  "caption": "Caption #example",
  "alt_text": "Description of the image",
  "approved": true
}
```

Required environment variables:

- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_USER_ID`
- optional `INSTAGRAM_GRAPH_VERSION` (defaults to `v26.0`)

The image URL must be reachable by Instagram. The publisher:

1. Requires explicit `approved: true`.
2. Creates an Instagram media container.
3. Reads the container status.
4. Publishes the container.
5. Reads the published media back.
6. Returns `VERIFIED` only when the returned media ID matches the publication read-back.

Instagram publishing is an external side effect and is intentionally not placed in the reusable CATCH cache.

## Security boundary

Never commit Instagram access tokens. Configure them only in the runtime/deployment secret store.

The native share path is the recommended zero-configuration path for personal use. The API path is for an Instagram professional account configured for Meta's Content Publishing API.
