import { useEffect, useState } from "react";
import { getDocumentStats, getSummary } from "../../lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  PhoneCall,
  Radio,
  Clock,
  Users,
  FileText,
  Database,
  Sparkles,
} from "lucide-react";

const STAT_ICONS = [PhoneCall, Radio, Clock, Users, FileText, Database];

export function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [docs, setDocs] = useState(null);

  useEffect(() => {
    getSummary().then(setSummary).catch(() => {});
    getDocumentStats().then(setDocs).catch(() => {});
  }, []);

  const cards = [
    { label: "Total Calls", value: summary?.total_sessions ?? null },
    { label: "Active Calls", value: summary?.active_sessions ?? null },
    { label: "Total Minutes", value: summary?.total_minutes ?? null },
    { label: "Demo Users", value: summary?.total_demo_users ?? null },
    { label: "Documents", value: docs?.total_documents ?? null },
    { label: "KB Chunks", value: docs?.total_chunks ?? null },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Overview of Avatour usage and knowledge base.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c, i) => {
          const Icon = STAT_ICONS[i];
          return (
            <Card key={c.label}>
              <CardContent className="flex items-center gap-4 p-5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  {c.value !== null ? (
                    <p className="text-2xl font-bold">{c.value}</p>
                  ) : (
                    <Skeleton className="h-7 w-16" />
                  )}
                  <p className="text-xs text-muted-foreground">{c.label}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Tavus CVI</CardTitle>
          </div>
          <CardDescription>
            Avatar sessions are powered by Tavus Conversational Video Interface.
            Manage replicas and personas from the sidebar.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Configure your Tavus API key, replica, and persona in{" "}
            <code className="text-xs bg-muted px-1 py-0.5 rounded">.env</code> and the admin portal.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
