import { useEffect, useState } from "react";
import { getSettings, listPersonas, updateSettings } from "../../lib/api";
import { extractList, pickId, pickName } from "./helpers";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, MessageSquareText } from "lucide-react";
import { cn } from "@/lib/utils";

export function PersonasPage() {
  const [personas, setPersonas] = useState([]);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSettings().then((s) => setSelected(s.persona_id || "")).catch(() => {});
    listPersonas()
      .then((resp) => setPersonas(extractList(resp)))
      .catch((e) => setError(e?.response?.data?.detail || "Failed to load personas."))
      .finally(() => setLoading(false));
  }, []);

  const assign = async (personaId) => {
    await updateSettings({ persona_id: personaId });
    setSelected(personaId);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Personas</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Browse Tavus personas and set the one that drives conversation behavior.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {personas.map((p) => {
            const id = pickId(p);
            const isSelected = id === selected;
            return (
              <Card
                key={id}
                className={cn(isSelected && "ring-2 ring-primary")}
              >
                <CardContent className="p-4 flex items-start gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <MessageSquareText className="h-6 w-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-medium">{pickName(p)}</p>
                        <p className="text-xs text-muted-foreground font-mono truncate">{id}</p>
                      </div>
                      {isSelected && <Badge>Active</Badge>}
                    </div>
                    {p.system_prompt && (
                      <p className="mt-2 text-xs text-muted-foreground line-clamp-2">
                        {p.system_prompt}
                      </p>
                    )}
                    <Button
                      size="sm"
                      variant={isSelected ? "outline" : "default"}
                      className="mt-3"
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
                  </div>
                </CardContent>
              </Card>
            );
          })}
          {personas.length === 0 && (
            <p className="text-sm text-muted-foreground col-span-full py-8 text-center">
              No personas found. Check your Tavus API key.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
