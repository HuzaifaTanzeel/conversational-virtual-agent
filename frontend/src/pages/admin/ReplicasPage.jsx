import { useEffect, useState } from "react";
import { getSettings, listReplicas, updateSettings } from "../../lib/api";
import { extractList, pickId, pickName } from "./helpers";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, User } from "lucide-react";
import { cn } from "@/lib/utils";

export function ReplicasPage() {
  const [replicas, setReplicas] = useState([]);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSettings().then((s) => setSelected(s.replica_id || "")).catch(() => {});
    listReplicas()
      .then((resp) => setReplicas(extractList(resp)))
      .catch((e) => setError(e?.response?.data?.detail || "Failed to load replicas."))
      .finally(() => setLoading(false));
  }, []);

  const assign = async (replicaId) => {
    await updateSettings({ replica_id: replicaId });
    setSelected(replicaId);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Replicas</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Browse Tavus replicas and set the one used for video calls.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {replicas.map((r) => {
            const id = pickId(r);
            const isSelected = id === selected;
            const thumb = r.thumbnail_url || r.preview_url || r.image_url;
            return (
              <Card
                key={id}
                className={cn(
                  "overflow-hidden transition-shadow hover:shadow-md",
                  isSelected && "ring-2 ring-primary",
                )}
              >
                {thumb ? (
                  <img src={thumb} alt={pickName(r)} className="h-40 w-full object-cover" />
                ) : (
                  <div className="flex h-40 items-center justify-center bg-muted">
                    <User className="h-10 w-10 text-muted-foreground" />
                  </div>
                )}
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-medium truncate">{pickName(r)}</p>
                      <p className="text-xs text-muted-foreground truncate font-mono">{id}</p>
                    </div>
                    {isSelected && <Badge className="shrink-0">Active</Badge>}
                  </div>
                  <Button
                    size="sm"
                    variant={isSelected ? "outline" : "default"}
                    className="mt-3 w-full"
                    disabled={isSelected}
                    onClick={() => assign(id)}
                  >
                    {isSelected ? (
                      <>
                        <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" /> Selected
                      </>
                    ) : (
                      "Use for Calls"
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
          {replicas.length === 0 && (
            <p className="text-sm text-muted-foreground col-span-full py-8 text-center">
              No replicas found. Check your Tavus API key.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
