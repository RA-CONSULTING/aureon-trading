import { createClient } from '@supabase/supabase-js';

// Robust browser client.
// Prefer build-time Vite env vars, but provide a safe fallback for preview environments
// where Vite env injection can be temporarily missing.
const supabaseUrl =
  (import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_URL.trim()) ||
  'https://owfeyxrfyhprpcgqwxqh.supabase.co';

const supabaseKey =
  (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY &&
    import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY.trim()) ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93ZmV5eHJmeWhwcnBjZ3F3eHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMyOTU5MTksImV4cCI6MjA3ODg3MTkxOX0.sb5uA0adyyVazBItAL3pk9Gm7qCZJoYnwc3W7LvPFAQ';

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    storage: localStorage,
    persistSession: true,
    autoRefreshToken: true,
  },
});
