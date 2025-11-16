export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.5"
  }
  public: {
    Tables: {
      lighthouse_events: {
        Row: {
          coherence: number
          confidence: number
          created_at: string
          dominant_node: string | null
          id: string
          is_lhe: boolean
          lambda_value: number
          lighthouse_signal: number
          metric_clin: number
          metric_cnonlin: number
          metric_cphi: number
          metric_geff: number
          metric_q: number
          prism_level: number | null
          prism_state: string | null
          threshold: number
          timestamp: string
        }
        Insert: {
          coherence: number
          confidence: number
          created_at?: string
          dominant_node?: string | null
          id?: string
          is_lhe: boolean
          lambda_value: number
          lighthouse_signal: number
          metric_clin: number
          metric_cnonlin: number
          metric_cphi: number
          metric_geff: number
          metric_q: number
          prism_level?: number | null
          prism_state?: string | null
          threshold: number
          timestamp?: string
        }
        Update: {
          coherence?: number
          confidence?: number
          created_at?: string
          dominant_node?: string | null
          id?: string
          is_lhe?: boolean
          lambda_value?: number
          lighthouse_signal?: number
          metric_clin?: number
          metric_cnonlin?: number
          metric_cphi?: number
          metric_geff?: number
          metric_q?: number
          prism_level?: number | null
          prism_state?: string | null
          threshold?: number
          timestamp?: string
        }
        Relationships: []
      }
      trading_signals: {
        Row: {
          coherence: number
          created_at: string
          id: string
          lighthouse_event_id: string | null
          lighthouse_value: number
          prism_level: number
          reason: string
          signal_type: string
          strength: number
          timestamp: string
        }
        Insert: {
          coherence: number
          created_at?: string
          id?: string
          lighthouse_event_id?: string | null
          lighthouse_value: number
          prism_level: number
          reason: string
          signal_type: string
          strength: number
          timestamp?: string
        }
        Update: {
          coherence?: number
          created_at?: string
          id?: string
          lighthouse_event_id?: string | null
          lighthouse_value?: number
          prism_level?: number
          reason?: string
          signal_type?: string
          strength?: number
          timestamp?: string
        }
        Relationships: [
          {
            foreignKeyName: "trading_signals_lighthouse_event_id_fkey"
            columns: ["lighthouse_event_id"]
            isOneToOne: false
            referencedRelation: "lighthouse_events"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      recent_optimal_signals: {
        Row: {
          coherence: number | null
          id: string | null
          is_lhe: boolean | null
          lhe_confidence: number | null
          lighthouse_signal: number | null
          lighthouse_value: number | null
          reason: string | null
          signal_type: string | null
          strength: number | null
          timestamp: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      get_signal_statistics: {
        Args: { time_range?: unknown }
        Returns: {
          avg_strength: number
          hold_signals: number
          lhe_count: number
          long_signals: number
          optimal_signals: number
          short_signals: number
          total_signals: number
        }[]
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
