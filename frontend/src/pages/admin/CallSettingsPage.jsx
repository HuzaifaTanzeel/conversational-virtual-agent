import { useEffect, useState } from "react";
import { getSettings, updateSettings } from "../../lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Settings, Save } from "lucide-react";
import { toast } from "sonner";

export function CallSettingsPage() {
  const [settings, setSettings] = useState(null);
  const [servicesText, setServicesText] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getSettings()
      .then((s) => {
        setSettings(s);
        setServicesText(
          s.services_json ? JSON.stringify(s.services_json, null, 2) : "",
        );
      })
      .catch((e) => setError(e?.response?.data?.detail || "Failed to load settings."));
  }, []);

  const update = (patch) => setSettings((prev) => ({ ...prev, ...patch }));

  const save = async (e) => {
    e.preventDefault();
    setError("");
    let services_json = null;
    if (servicesText.trim()) {
      try {
        services_json = JSON.parse(servicesText);
      } catch {
        setError("Services must be valid JSON (an array of {title, description}).");
        return;
      }
    }
    try {
      const payload = {
        tavus_sandbox: settings.tavus_sandbox,
        company_name: settings.company_name,
        hero_title: settings.hero_title,
        hero_subtitle: settings.hero_subtitle,
        logo_url: settings.logo_url,
        primary_color: settings.primary_color,
        services_json,
      };
      const updated = await updateSettings(payload);
      setSettings(updated);
      toast.success("Settings saved");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to save settings.");
    }
  };

  if (!settings)
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Call Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configure call behavior and the public marketing page content.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>
      )}

      {/* Active config (read-only summary) */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Settings className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Active Call Configuration</CardTitle>
          </div>
          <CardDescription>Assign these on the Replicas and Personas pages.</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-3 sm:grid-cols-2 text-sm">
            <div>
              <dt className="text-muted-foreground">Replica</dt>
              <dd className="font-mono text-xs mt-0.5">{settings.replica_id || "not set"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Persona</dt>
              <dd className="font-mono text-xs mt-0.5">{settings.persona_id || "not set"}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Editable settings form */}
      <Card>
        <CardContent className="p-6">
          <form onSubmit={save} className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-sm font-medium">Tavus Sandbox Mode</Label>
                <p className="text-xs text-muted-foreground">Sandbox conversations — turn off for production.</p>
              </div>
              <Switch
                checked={!!settings.tavus_sandbox}
                onCheckedChange={(checked) => update({ tavus_sandbox: checked })}
              />
            </div>

            <Separator />

            <h3 className="font-semibold">Public Page Content</h3>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Company Name</Label>
                <Input
                  value={settings.company_name || ""}
                  onChange={(e) => update({ company_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Hero Title</Label>
                <Input
                  value={settings.hero_title || ""}
                  onChange={(e) => update({ hero_title: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Hero Subtitle</Label>
                <Textarea
                  rows={2}
                  value={settings.hero_subtitle || ""}
                  onChange={(e) => update({ hero_subtitle: e.target.value })}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Logo URL</Label>
                  <Input
                    value={settings.logo_url || ""}
                    onChange={(e) => update({ logo_url: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Primary Color</Label>
                  <Input
                    value={settings.primary_color || ""}
                    placeholder="#6366f1"
                    onChange={(e) => update({ primary_color: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Services (JSON array)</Label>
                <Textarea
                  rows={6}
                  className="font-mono text-xs"
                  placeholder='[{"title": "Service A", "description": "..."}]'
                  value={servicesText}
                  onChange={(e) => setServicesText(e.target.value)}
                />
              </div>
            </div>

            <Button type="submit">
              <Save className="mr-1.5 h-4 w-4" /> Save Settings
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
