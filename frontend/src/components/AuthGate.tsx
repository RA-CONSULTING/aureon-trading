/**
 * AuthGate — optional Supabase session gate for the whole console.
 *
 * Off by default: the console stays open in dev/local exactly as before.
 * Set VITE_REQUIRE_AUTH=1 at build time (the production image does) and the
 * console renders the existing AuthForm until a Supabase session exists.
 * Session changes (sign-out, token expiry) drop the user back to the form.
 */

import { type ReactNode, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/integrations/supabase/client";
import { AuthForm } from "@/components/AuthForm";
import { Button } from "@/components/ui/button";

const REQUIRE_AUTH = (import.meta.env.VITE_REQUIRE_AUTH as string | undefined) === "1";

export function AuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [checking, setChecking] = useState(REQUIRE_AUTH);

  useEffect(() => {
    if (!REQUIRE_AUTH) return;
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setChecking(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  if (!REQUIRE_AUTH) return <>{children}</>;

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-muted-foreground">
        Checking session…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <AuthForm onSuccess={() => supabase.auth.getSession().then(({ data }) => setSession(data.session))} />
      </div>
    );
  }

  return (
    <>
      <div className="fixed top-2 right-2 z-50">
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-muted-foreground"
          onClick={() => supabase.auth.signOut()}
        >
          Sign out{session.user?.email ? ` (${session.user.email})` : ""}
        </Button>
      </div>
      {children}
    </>
  );
}
