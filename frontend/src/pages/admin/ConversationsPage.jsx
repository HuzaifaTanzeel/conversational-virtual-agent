import { useEffect, useState } from "react";
import { getSessionMessages, listSessions } from "../../lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

export function ConversationsPage() {
  const [sessions, setSessions] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch((e) => setError(e?.response?.data?.detail || "Failed to load sessions."));
  }, []);

  const open = async (session) => {
    setActive(session);
    setMessages([]);
    try {
      setMessages(await getSessionMessages(session.id));
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load transcript.");
    }
  };

  const fmt = (s) => (s ? new Date(s).toLocaleString() : "\u2014");

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Conversations</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review call sessions and stored transcripts.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Started</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Msgs</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sessions.map((s) => (
                <TableRow
                  key={s.id}
                  className={cn(
                    "cursor-pointer",
                    active?.id === s.id && "bg-primary/5"
                  )}
                  onClick={() => open(s)}
                >
                  <TableCell className="text-xs">{fmt(s.started_at)}</TableCell>
                  <TableCell>{s.demo_username || "\u2014"}</TableCell>
                  <TableCell className="text-xs">
                    {Math.round(s.duration_seconds / 60)}m {s.duration_seconds % 60}s
                  </TableCell>
                  <TableCell>
                    <Badge variant={s.status === "active" ? "warning" : "success"}>
                      {s.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{s.message_count}</TableCell>
                </TableRow>
              ))}
              {sessions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No call sessions yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>

        <Card className="min-h-[300px]">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[calc(70vh-10rem)]">
              {!active ? (
                <p className="text-sm text-muted-foreground py-8 text-center">
                  Select a session to view its transcript.
                </p>
              ) : messages.length === 0 ? (
                <p className="text-sm text-muted-foreground py-8 text-center">
                  No messages stored for this session.
                </p>
              ) : (
                <div className="flex flex-col gap-3 pr-4">
                  {messages.map((m, i) => (
                    <div
                      key={i}
                      className={cn(
                        "max-w-[90%] rounded-lg px-3 py-2 text-sm animate-fade-in",
                        m.role === "user"
                          ? "ml-auto bg-primary/10 text-foreground"
                          : "bg-muted"
                      )}
                    >
                      <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-0.5">
                        {m.role === "user" ? "Prospect" : "Agent"}
                      </span>
                      <p className="leading-relaxed">{m.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
