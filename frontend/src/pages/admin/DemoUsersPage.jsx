import { useEffect, useState } from "react";
import {
  createDemoUser,
  deleteDemoUser,
  listDemoUsers,
  resetDemoUserPassword,
  resetDemoUserUsage,
  updateDemoUser,
} from "../../lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { Plus, Copy, MoreHorizontal, KeyRound, RotateCcw, UserX, Trash2, Check } from "lucide-react";
import { toast } from "sonner";

function CredentialDialog({ credential, onClose }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(credential.password);
    setCopied(true);
    toast.success("Password copied to clipboard");
  };
  return (
    <Dialog open={!!credential} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Credentials (shown once)</DialogTitle>
          <DialogDescription>
            Copy and share these now — the password cannot be retrieved later.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 rounded-md bg-muted p-4 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Username</span>
            <code className="font-mono">{credential?.username}</code>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Password</span>
            <code className="font-mono">{credential?.password}</code>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={copy}>
            {copied ? <><Check className="mr-1.5 h-3.5 w-3.5" /> Copied!</> : <><Copy className="mr-1.5 h-3.5 w-3.5" /> Copy Password</>}
          </Button>
          <Button variant="ghost" onClick={onClose}>Done</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function DemoUsersPage() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [credential, setCredential] = useState(null);
  const [form, setForm] = useState({ username: "", display_name: "", minute_quota: 30 });
  const [confirmDelete, setConfirmDelete] = useState(null);

  const refresh = async () => {
    try {
      setUsers(await listDemoUsers());
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load demo users.");
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const create = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const created = await createDemoUser({
        username: form.username.trim(),
        display_name: form.display_name.trim() || null,
        minute_quota: Number(form.minute_quota),
      });
      setCredential({ username: created.username, password: created.password });
      setForm({ username: "", display_name: "", minute_quota: 30 });
      await refresh();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to create demo user.");
    }
  };

  const reset = async (u) => {
    const res = await resetDemoUserPassword(u.id);
    setCredential({ username: res.username, password: res.password });
  };

  const toggleActive = async (u) => {
    await updateDemoUser(u.id, { is_active: !u.is_active });
    await refresh();
    toast.success(u.is_active ? "User disabled" : "User enabled");
  };

  const setQuota = async (u) => {
    const value = window.prompt("New minute quota:", u.minute_quota);
    if (value === null) return;
    await updateDemoUser(u.id, { minute_quota: Number(value) });
    await refresh();
    toast.success("Quota updated");
  };

  const resetUsage = async (u) => {
    await resetDemoUserUsage(u.id);
    await refresh();
    toast.success("Usage reset");
  };

  const remove = async () => {
    if (!confirmDelete) return;
    await deleteDemoUser(confirmDelete.id);
    setConfirmDelete(null);
    await refresh();
    toast.success("User deleted");
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Demo Users</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Create call credentials and control how many minutes each prospect can use.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>
      )}

      {/* Create form */}
      <Card className="mb-6">
        <CardContent className="p-5">
          <form onSubmit={create} className="flex flex-wrap items-end gap-4">
            <div className="space-y-2 flex-1 min-w-[160px]">
              <Label>Username</Label>
              <Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            </div>
            <div className="space-y-2 flex-1 min-w-[160px]">
              <Label>Display Name</Label>
              <Input value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
            </div>
            <div className="space-y-2 w-28">
              <Label>Quota (min)</Label>
              <Input type="number" min={1} value={form.minute_quota} onChange={(e) => setForm({ ...form, minute_quota: e.target.value })} required />
            </div>
            <Button type="submit">
              <Plus className="mr-1.5 h-4 w-4" /> Create
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Users table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Username</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Used / Quota</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id}>
                <TableCell className="font-medium">{u.username}</TableCell>
                <TableCell>{u.display_name || "\u2014"}</TableCell>
                <TableCell>{u.minutes_used.toFixed(1)} / {u.minute_quota}</TableCell>
                <TableCell>
                  <Badge variant={u.is_active ? "success" : "destructive"}>
                    {u.is_active ? "active" : "disabled"}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => setQuota(u)}>
                        Set quota
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => resetUsage(u)}>
                        <RotateCcw className="mr-2 h-3.5 w-3.5" /> Reset usage
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => reset(u)}>
                        <KeyRound className="mr-2 h-3.5 w-3.5" /> Reset password
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => toggleActive(u)}>
                        <UserX className="mr-2 h-3.5 w-3.5" /> {u.is_active ? "Disable" : "Enable"}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setConfirmDelete(u)} className="text-destructive focus:text-destructive">
                        <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
            {users.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                  No demo users yet.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      <CredentialDialog credential={credential} onClose={() => setCredential(null)} />

      {/* Delete confirmation */}
      <Dialog open={!!confirmDelete} onOpenChange={(open) => !open && setConfirmDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Demo User</DialogTitle>
            <DialogDescription>
              Delete user "{confirmDelete?.username}"? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setConfirmDelete(null)}>Cancel</Button>
            <Button variant="destructive" onClick={remove}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
