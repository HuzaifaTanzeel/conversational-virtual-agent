import { useEffect, useState } from "react";
import { cancelMeeting, listMeetings, resendMeetingEmail } from "../../lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, Mail, Ban } from "lucide-react";
import { toast } from "sonner";

const STATUS_VARIANT = {
  pending: "secondary",
  redeemed: "warning",
  completed: "success",
  cancelled: "destructive",
};

export function MeetingsPage() {
  const [meetings, setMeetings] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    listMeetings()
      .then(setMeetings)
      .catch((e) => setError(e?.response?.data?.detail || "Failed to load meetings."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleCancel = async (id) => {
    try {
      await cancelMeeting(id);
      toast.success("Meeting cancelled");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to cancel meeting.");
    }
  };

  const handleResend = async (id) => {
    try {
      await resendMeetingEmail(id);
      toast.success("Email resent with a new passcode");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to resend email.");
    }
  };

  const fmt = (s) => (s ? new Date(s).toLocaleString() : "\u2014");

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Meetings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          View scheduled and completed meeting invites.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Prospect</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Meeting ID</TableHead>
              <TableHead>Scheduled</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {meetings.map((m) => (
              <TableRow key={m.id}>
                <TableCell className="font-medium">{m.prospect_name}</TableCell>
                <TableCell className="text-sm">{m.prospect_email}</TableCell>
                <TableCell>
                  <code className="text-xs font-mono">{m.meeting_id}</code>
                </TableCell>
                <TableCell className="text-xs">
                  {m.scheduled_at ? fmt(m.scheduled_at) : "Instant"}
                </TableCell>
                <TableCell>
                  <Badge variant={STATUS_VARIANT[m.status] || "secondary"}>
                    {m.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs">{fmt(m.created_at)}</TableCell>
                <TableCell>
                  {m.status === "pending" && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleResend(m.id)}>
                          <Mail className="mr-2 h-4 w-4" />
                          Resend email
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => handleCancel(m.id)}
                        >
                          <Ban className="mr-2 h-4 w-4" />
                          Cancel
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {!loading && meetings.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                  No meetings yet.
                </TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                  Loading...
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
