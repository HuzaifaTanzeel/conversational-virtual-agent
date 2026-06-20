// Tavus list responses may vary in shape. Find the first array we can render.
export function extractList(response) {
  if (Array.isArray(response)) return response;
  const data = response?.data ?? response;
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object") {
    for (const value of Object.values(data)) {
      if (Array.isArray(value)) return value;
    }
  }
  return [];
}

export function pickId(item) {
  return (
    item?.id ||
    item?.replica_id ||
    item?.persona_id ||
    item?.property_id ||
    ""
  );
}

export function pickName(item) {
  return item?.name || item?.display_name || item?.title || pickId(item);
}
