import { useEffect, useState } from "react";
import {
  createProperty,
  createPropertyMedia,
  deleteProperty,
  deletePropertyMedia,
  listProperties,
  listPropertyMedia,
} from "../../lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Trash2, Image } from "lucide-react";
import { toast } from "sonner";

const EMPTY_PROPERTY = {
  name: "",
  property_type: "real_estate",
  location: "",
  description: "",
};

const EMPTY_MEDIA = {
  asset_type: "photo",
  room_name: "",
  asset_url: "",
  thumbnail_url: "",
  tags: "",
  sort_order: 0,
};

export function PropertiesPage() {
  const [properties, setProperties] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [propertyForm, setPropertyForm] = useState(EMPTY_PROPERTY);
  const [mediaForm, setMediaForm] = useState(EMPTY_MEDIA);
  const [showPropertyDialog, setShowPropertyDialog] = useState(false);
  const [showMediaDialog, setShowMediaDialog] = useState(false);

  const loadProperties = () => {
    setLoading(true);
    listProperties()
      .then(setProperties)
      .catch((e) => setError(e?.response?.data?.detail || "Failed to load properties."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProperties();
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setMedia([]);
      return;
    }
    listPropertyMedia(selectedId).then(setMedia).catch(() => setMedia([]));
  }, [selectedId]);

  const saveProperty = async () => {
    try {
      await createProperty(propertyForm);
      setShowPropertyDialog(false);
      setPropertyForm(EMPTY_PROPERTY);
      loadProperties();
      toast.success("Property created");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to create property");
    }
  };

  const saveMedia = async () => {
    if (!selectedId) return;
    try {
      await createPropertyMedia(selectedId, mediaForm);
      setShowMediaDialog(false);
      setMediaForm(EMPTY_MEDIA);
      const assets = await listPropertyMedia(selectedId);
      setMedia(assets);
      toast.success("Media asset added");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to add media");
    }
  };

  const removeProperty = async (id) => {
    if (!confirm("Delete this property and all its media?")) return;
    await deleteProperty(id);
    if (selectedId === id) setSelectedId(null);
    loadProperties();
    toast.success("Property deleted");
  };

  const removeMedia = async (assetId) => {
    if (!selectedId) return;
    await deletePropertyMedia(selectedId, assetId);
    setMedia((prev) => prev.filter((m) => m.id !== assetId));
    toast.success("Media deleted");
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Properties</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage property listings and media shown during tool calls.
          </p>
        </div>
        <Button onClick={() => setShowPropertyDialog(true)}>
          <Plus className="mr-1.5 h-4 w-4" /> Add Property
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Listings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {properties.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedId(p.id)}
                className={`w-full rounded-lg border p-3 text-left transition-colors ${
                  selectedId === p.id ? "border-primary bg-primary/5" : "hover:bg-muted/50"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <p className="font-medium">{p.name}</p>
                    <p className="text-xs text-muted-foreground">{p.location || p.property_type}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{p.media_count} media</Badge>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeProperty(p.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </button>
            ))}
            {properties.length === 0 && (
              <p className="text-sm text-muted-foreground py-4 text-center">No properties yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Media Assets</CardTitle>
            {selectedId && (
              <Button size="sm" onClick={() => setShowMediaDialog(true)}>
                <Plus className="mr-1 h-3.5 w-3.5" /> Add Media
              </Button>
            )}
          </CardHeader>
          <CardContent className="space-y-2">
            {!selectedId && (
              <p className="text-sm text-muted-foreground py-4 text-center">
                Select a property to manage media.
              </p>
            )}
            {media.map((m) => (
              <div key={m.id} className="flex items-center gap-3 rounded-lg border p-3">
                <div className="flex h-10 w-10 items-center justify-center rounded bg-muted">
                  <Image className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{m.room_name || m.asset_type}</p>
                  <p className="text-xs text-muted-foreground truncate">{m.asset_url}</p>
                </div>
                <Badge variant="outline">{m.asset_type}</Badge>
                <Button size="icon" variant="ghost" onClick={() => removeMedia(m.id)}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Dialog open={showPropertyDialog} onOpenChange={setShowPropertyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Property</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                value={propertyForm.name}
                onChange={(e) => setPropertyForm({ ...propertyForm, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={propertyForm.property_type}
                onChange={(e) =>
                  setPropertyForm({ ...propertyForm, property_type: e.target.value })
                }
              >
                <option value="real_estate">Real Estate</option>
                <option value="resort">Resort</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Location</Label>
              <Input
                value={propertyForm.location}
                onChange={(e) => setPropertyForm({ ...propertyForm, location: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={propertyForm.description}
                onChange={(e) =>
                  setPropertyForm({ ...propertyForm, description: e.target.value })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={saveProperty}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showMediaDialog} onOpenChange={setShowMediaDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Media Asset</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Asset Type</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={mediaForm.asset_type}
                onChange={(e) => setMediaForm({ ...mediaForm, asset_type: e.target.value })}
              >
                <option value="photo">Photo</option>
                <option value="video">Video</option>
                <option value="tour_360">360 Tour</option>
                <option value="floor_plan">Floor Plan</option>
                <option value="matterport">Matterport</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Room Name</Label>
              <Input
                placeholder="dining_room"
                value={mediaForm.room_name}
                onChange={(e) => setMediaForm({ ...mediaForm, room_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Asset URL</Label>
              <Input
                value={mediaForm.asset_url}
                onChange={(e) => setMediaForm({ ...mediaForm, asset_url: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Tags (comma-separated)</Label>
              <Input
                placeholder="3d,dining,ground_floor"
                value={mediaForm.tags}
                onChange={(e) => setMediaForm({ ...mediaForm, tags: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={saveMedia}>Add</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
