/**
 * Shared page chrome for shell routes: per-route error boundary (a crashing
 * dashboard never takes down the shell), a branded loading skeleton, and an
 * honest live-data notice for dashboards that need a running backend.
 */

import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCcw, Wifi } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function PageSkeleton() {
  return (
    <div className="space-y-4 p-6" aria-busy="true" aria-label="Loading">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96" />
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-36" />
        <Skeleton className="h-36" />
        <Skeleton className="h-36" />
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}

export function LiveDataNotice() {
  return (
    <Alert className="mb-4 border-border/60">
      <Wifi className="h-4 w-4" />
      <AlertTitle>Live surface</AlertTitle>
      <AlertDescription>
        This view streams from the running Aureon backend (gateway / bridge /
        Supabase feed). With no backend connected it renders with empty or stale
        data — that is honest, not broken.
      </AlertDescription>
    </Alert>
  );
}

interface BoundaryProps {
  name: string;
  children: ReactNode;
}

interface BoundaryState {
  error: Error | null;
}

export class RouteErrorBoundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): BoundaryState {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="p-6">
          <Card className="max-w-xl border-destructive/40">
            <CardContent className="space-y-4 p-6">
              <div className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-5 w-5" />
                <p className="font-semibold">{this.props.name} failed to render</p>
              </div>
              <p className="text-sm text-muted-foreground break-words">
                {this.state.error.message || String(this.state.error)}
              </p>
              <p className="text-xs text-muted-foreground">
                The rest of the platform is unaffected — pick another surface from
                the sidebar, or retry this one.
              </p>
              <Button size="sm" variant="outline" onClick={() => this.setState({ error: null })}>
                <RefreshCcw className="mr-2 h-4 w-4" /> Retry
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
    return this.props.children;
  }
}
