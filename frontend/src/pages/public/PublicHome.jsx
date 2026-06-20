import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { bookCall, getPublicContent } from "../../lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Sparkles,
  MessageSquare,
  Shield,
  Zap,
  Clock,
  ArrowRight,
  PlayCircle,
  Star,
  ChevronDown,
  ChevronUp,
  Calendar,
  Video,
  Mail,
} from "lucide-react";
import { cn, formatApiError } from "@/lib/utils";

const DEFAULT_SERVICES = [
  {
    title: "Product Demos",
    description: "Interactive AI-powered product demonstrations that adapt to your prospect's interests in real time.",
    icon: PlayCircle,
  },
  {
    title: "Instant Answers",
    description: "Get immediate, accurate answers to any product or pricing questions — available 24/7.",
    icon: MessageSquare,
  },
  {
    title: "Enterprise Security",
    description: "SOC 2 compliant with end-to-end encryption. Your data stays private and secure.",
    icon: Shield,
  },
  {
    title: "Lightning Fast",
    description: "Sub-second response times powered by advanced AI. No waiting, no scheduling.",
    icon: Zap,
  },
];

const HOW_IT_WORKS = [
  { step: "1", title: "Book a Call", description: "Enter your name and email to receive a meeting link and passcode instantly or for later." },
  { step: "2", title: "Join the Meeting", description: "Click the link in your email or enter your Meeting ID and Passcode on the join page." },
  { step: "3", title: "Talk Naturally", description: "Speak with our AI avatar and get personalized answers about our products and services." },
];

const TESTIMONIALS = [
  { name: "Sarah Chen", role: "VP of Sales, TechCorp", quote: "The AI agent handled our prospect calls flawlessly. Response quality is incredible.", rating: 5 },
  { name: "Marcus Johnson", role: "Head of Growth, StartupXYZ", quote: "We reduced our sales response time from hours to seconds. Game changer for our pipeline.", rating: 5 },
  { name: "Emily Rodriguez", role: "CTO, DataFlow Inc", quote: "The natural conversation flow surprised us. Prospects often don't realize they're talking to AI.", rating: 5 },
];

const FAQ = [
  { q: "How does the AI sales agent work?", a: "Our AI agent uses advanced language models combined with your product knowledge base to have natural, informed conversations with prospects via a lifelike video avatar." },
  { q: "Is my data secure?", a: "Absolutely. All conversations are encrypted end-to-end, and your product data is stored in isolated vector databases with strict access controls." },
  { q: "Can I customize the avatar and voice?", a: "Yes! Choose from a library of professional avatars and voices, or upload your own. You can also fully customize the conversation context and personality." },
  { q: "How long are demo sessions?", a: "Session length is configurable per user. Admins can set minute quotas from the dashboard to control usage." },
];

function BookCallDialog({ open, onOpenChange }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [meetingId, setMeetingId] = useState("");

  const reset = () => {
    setName("");
    setEmail("");
    setScheduledAt("");
    setError("");
    setConfirmed(false);
    setMeetingId("");
    setSubmitting(false);
  };

  const handleOpenChange = (next) => {
    if (!next) reset();
    onOpenChange(next);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const scheduled = scheduledAt ? new Date(scheduledAt).toISOString() : null;
      const data = await bookCall({
        name: name.trim(),
        email: email.trim(),
        scheduled_at: scheduled,
      });
      setMeetingId(data.meeting_id);
      setConfirmed(true);
    } catch (err) {
      setError(formatApiError(err, "Failed to book meeting. Please try again."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        {confirmed ? (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-primary" />
                Check your email
              </DialogTitle>
              <DialogDescription>
                We sent your meeting link and passcode to <strong>{email}</strong>.
                {meetingId && (
                  <span className="mt-2 block">
                    Meeting ID: <code className="font-mono font-semibold">{meetingId}</code>
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="flex-col gap-2 sm:flex-col">
              <Button asChild className="w-full">
                <Link to="/call">Join with Meeting ID</Link>
              </Button>
              <Button variant="ghost" onClick={() => handleOpenChange(false)}>
                Done
              </Button>
            </DialogFooter>
          </>
        ) : (
          <form onSubmit={submit}>
            <DialogHeader>
              <DialogTitle>Book a Call</DialogTitle>
              <DialogDescription>
                Enter your details to receive a meeting link and passcode by email.
                Leave the schedule empty to start instantly.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {error && (
                <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="book-name">Name</Label>
                <Input
                  id="book-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="book-email">Email</Label>
                <Input
                  id="book-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="book-schedule">
                  Schedule for later <span className="text-muted-foreground font-normal">(optional)</span>
                </Label>
                <Input
                  id="book-schedule"
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={(e) => setScheduledAt(e.target.value)}
                  min={new Date().toISOString().slice(0, 16)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => handleOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Booking..." : scheduledAt ? "Schedule Meeting" : "Book Now"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

function FAQItem({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-4 text-left text-sm font-medium hover:text-primary transition-colors"
      >
        {item.q}
        {open ? <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />}
      </button>
      {open && <p className="pb-4 text-sm text-muted-foreground leading-relaxed">{item.a}</p>}
    </div>
  );
}

export function PublicHome() {
  const [content, setContent] = useState(null);
  const [bookOpen, setBookOpen] = useState(false);

  useEffect(() => {
    getPublicContent()
      .then(setContent)
      .catch(() => setContent({}));
  }, []);

  const services = Array.isArray(content?.services_json) ? content.services_json : [];
  const displayServices = services.length > 0
    ? services.map((s, i) => ({ title: s.title || s.name || `Service ${i + 1}`, description: s.description || s.desc || "", icon: DEFAULT_SERVICES[i % DEFAULT_SERVICES.length].icon }))
    : DEFAULT_SERVICES;

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2.5">
            {content?.logo_url ? (
              <img src={content.logo_url} alt="logo" className="h-8" />
            ) : (
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Sparkles className="h-4 w-4" />
              </div>
            )}
            <span className="text-lg font-semibold tracking-tight">
              {content?.company_name || "Avatar Sales Agent"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" asChild>
              <Link to="/call">
                <Video className="mr-1.5 h-4 w-4" />
                Join Meeting
              </Link>
            </Button>
            <Button onClick={() => setBookOpen(true)}>
              Book a Call
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-violet-50" />
        <div className="relative mx-auto max-w-6xl px-4 py-20 text-center sm:px-6 sm:py-28 lg:py-36">
          <div className="mx-auto inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm mb-6">
            <Sparkles className="h-3 w-3 text-primary" />
            AI-Powered Sales Conversations
          </div>
          <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            {content?.hero_title || "Meet Your AI Sales Agent"}
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground leading-relaxed">
            {content?.hero_subtitle ||
              "Have a live, face-to-face conversation with a virtual sales representative who knows your products inside and out. Available 24/7, always ready to help."}
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button size="lg" className="shadow-md" onClick={() => setBookOpen(true)}>
              <PlayCircle className="mr-2 h-4 w-4" />
              Book a Call
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/call">
                <Video className="mr-2 h-4 w-4" />
                Join a Meeting
              </Link>
            </Button>
            <Button asChild variant="ghost" size="lg">
              <a href="#how-it-works">Learn More</a>
            </Button>
          </div>
          <div className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-primary" />
              <span>24/7 Available</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Zap className="h-4 w-4 text-primary" />
              <span>Sub-second Responses</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Shield className="h-4 w-4 text-primary" />
              <span>Enterprise Secure</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats strip */}
      <section className="border-y bg-slate-50/80">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-4 py-10 text-center sm:grid-cols-4 sm:px-6">
          {[
            { value: "10k+", label: "Conversations" },
            { value: "98%", label: "Satisfaction" },
            { value: "<1s", label: "Response Time" },
            { value: "24/7", label: "Availability" },
          ].map((s) => (
            <div key={s.label}>
              <div className="text-2xl font-bold text-primary sm:text-3xl">{s.value}</div>
              <div className="mt-1 text-sm text-muted-foreground">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Services / Features */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <div className="text-center">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            What We Offer
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-muted-foreground">
            Everything you need for intelligent, automated sales conversations.
          </p>
        </div>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {displayServices.map((s, i) => {
            const Icon = s.icon || Sparkles;
            return (
              <Card key={i} className="group relative overflow-hidden transition-shadow hover:shadow-md">
                <CardContent className="p-6">
                  <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-white">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold">{s.title}</h3>
                  <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">{s.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-slate-50/80 scroll-mt-16">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              How It Works
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
              Get started in three simple steps.
            </p>
          </div>
          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-white shadow-sm">
                  {item.step}
                </div>
                <h3 className="mt-4 font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <div className="text-center">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            What People Are Saying
          </h2>
        </div>
        <div className="mt-10 grid gap-5 sm:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <Card key={i} className="transition-shadow hover:shadow-md">
              <CardContent className="p-6">
                <div className="flex gap-0.5 mb-3">
                  {Array.from({ length: t.rating }).map((_, j) => (
                    <Star key={j} className="h-4 w-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed italic">"{t.quote}"</p>
                <div className="mt-4 flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {t.name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{t.name}</p>
                    <p className="text-xs text-muted-foreground">{t.role}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-slate-50/80">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Frequently Asked Questions
            </h2>
          </div>
          <Card className="mt-10">
            <CardContent className="p-6">
              {FAQ.map((item, i) => (
                <FAQItem key={i} item={item} />
              ))}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <Card className="overflow-hidden bg-gradient-to-br from-primary to-violet-600 text-white border-0">
          <CardContent className="p-8 text-center sm:p-12">
            <h2 className="text-2xl font-bold sm:text-3xl">Ready to Get Started?</h2>
            <p className="mx-auto mt-3 max-w-xl text-white/80">
              Experience the future of sales conversations. Talk to our AI agent now.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Button size="lg" variant="secondary" className="shadow-md" onClick={() => setBookOpen(true)}>
                <Calendar className="mr-2 h-4 w-4" />
                Book a Call
              </Button>
              <Button asChild size="lg" variant="outline" className="shadow-md border-white/30 text-white hover:bg-white/10">
                <Link to="/call">
                  <Video className="mr-2 h-4 w-4" />
                  Join a Meeting
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-6 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5" />
            <span>&copy; {new Date().getFullYear()} {content?.company_name || "Avatar Sales Agent"}. All rights reserved.</span>
          </div>
          <Link to="/admin/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Admin Portal
          </Link>
        </div>
      </footer>

      <BookCallDialog open={bookOpen} onOpenChange={setBookOpen} />
    </div>
  );
}
