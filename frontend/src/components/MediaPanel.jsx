export function MediaPanel({ media }) {
  if (!media) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-900 p-6 text-center">
        <p className="text-sm text-white/50">
          Media will appear here during the conversation
        </p>
      </div>
    );
  }

  const { parameters } = media;
  const params =
    typeof parameters === "string"
      ? (() => {
          try {
            return JSON.parse(parameters);
          } catch {
            return {};
          }
        })()
      : parameters || {};

  const assetType = params.asset_type;
  const rawUrl = params.asset_url;
  const assetUrl =
    rawUrl && rawUrl.startsWith("/")
      ? `${window.location.origin}${rawUrl}`
      : rawUrl;

  if (!assetUrl) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-900 p-6 text-center">
        <p className="text-sm text-white/50">Loading media&hellip;</p>
      </div>
    );
  }

  if (assetType === "matterport" || assetType === "tour_360") {
    return (
      <iframe
        src={assetUrl}
        className="h-full w-full border-0 bg-black"
        allow="xr-spatial-tracking; fullscreen"
        title="3D Tour"
      />
    );
  }

  if (assetType === "video") {
    return (
      <video
        src={assetUrl}
        autoPlay
        controls
        className="h-full w-full bg-black object-contain"
      />
    );
  }

  if (assetType === "photo") {
    return (
      <img
        src={assetUrl}
        alt="Property view"
        className="h-full w-full bg-black object-cover"
      />
    );
  }

  if (assetType === "floor_plan") {
    return (
      <iframe
        src={assetUrl}
        className="h-full w-full border-0 bg-white"
        title="Floor Plan"
      />
    );
  }

  return (
    <div className="flex h-full items-center justify-center bg-slate-900 p-6">
      <p className="text-sm text-white/50">Unsupported media type: {assetType}</p>
    </div>
  );
}
