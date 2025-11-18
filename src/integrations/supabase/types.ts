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
      backtest_results: {
        Row: {
          avg_trade_duration: number | null
          config: Json
          created_at: string
          end_date: string
          equity_curve: Json
          final_capital: number
          id: string
          initial_capital: number
          losing_trades: number
          max_drawdown: number
          profit_factor: number
          sharpe_ratio: number | null
          start_date: string
          status: string
          symbol: string
          total_return: number
          total_trades: number
          trades: Json
          win_rate: number
          winning_trades: number
        }
        Insert: {
          avg_trade_duration?: number | null
          config: Json
          created_at?: string
          end_date: string
          equity_curve: Json
          final_capital: number
          id?: string
          initial_capital: number
          losing_trades: number
          max_drawdown: number
          profit_factor: number
          sharpe_ratio?: number | null
          start_date: string
          status?: string
          symbol: string
          total_return: number
          total_trades: number
          trades: Json
          win_rate: number
          winning_trades: number
        }
        Update: {
          avg_trade_duration?: number | null
          config?: Json
          created_at?: string
          end_date?: string
          equity_curve?: Json
          final_capital?: number
          id?: string
          initial_capital?: number
          losing_trades?: number
          max_drawdown?: number
          profit_factor?: number
          sharpe_ratio?: number | null
          start_date?: string
          status?: string
          symbol?: string
          total_return?: number
          total_trades?: number
          trades?: Json
          win_rate?: number
          winning_trades?: number
        }
        Relationships: []
      }
      coherence_history: {
        Row: {
          coherence: number
          created_at: string
          day_of_week: number
          hour_of_day: number
          id: string
          lambda_value: number
          symbol: string
          timestamp: string
        }
        Insert: {
          coherence: number
          created_at?: string
          day_of_week: number
          hour_of_day: number
          id?: string
          lambda_value: number
          symbol?: string
          timestamp?: string
        }
        Update: {
          coherence?: number
          created_at?: string
          day_of_week?: number
          hour_of_day?: number
          id?: string
          lambda_value?: number
          symbol?: string
          timestamp?: string
        }
        Relationships: []
      }
      consciousness_field_history: {
        Row: {
          alpha_waves: number | null
          beta_waves: number | null
          biometric_coherence_index: number | null
          celestial_boost: number
          created_at: string
          delta_waves: number | null
          heart_rate: number | null
          hrv: number | null
          id: string
          schumann_amplitude: number
          schumann_coherence_boost: number
          schumann_frequency: number
          schumann_phase: string
          schumann_quality: number
          theta_waves: number | null
          timestamp: string
          total_coherence: number
        }
        Insert: {
          alpha_waves?: number | null
          beta_waves?: number | null
          biometric_coherence_index?: number | null
          celestial_boost?: number
          created_at?: string
          delta_waves?: number | null
          heart_rate?: number | null
          hrv?: number | null
          id?: string
          schumann_amplitude: number
          schumann_coherence_boost: number
          schumann_frequency: number
          schumann_phase: string
          schumann_quality: number
          theta_waves?: number | null
          timestamp?: string
          total_coherence: number
        }
        Update: {
          alpha_waves?: number | null
          beta_waves?: number | null
          biometric_coherence_index?: number | null
          celestial_boost?: number
          created_at?: string
          delta_waves?: number | null
          heart_rate?: number | null
          hrv?: number | null
          id?: string
          schumann_amplitude?: number
          schumann_coherence_boost?: number
          schumann_frequency?: number
          schumann_phase?: string
          schumann_quality?: number
          theta_waves?: number | null
          timestamp?: string
          total_coherence?: number
        }
        Relationships: []
      }
      harmonic_nexus_states: {
        Row: {
          akashic_boost: number
          akashic_convergence: number
          akashic_frequency: number
          akashic_stability: number
          created_at: string
          dimensional_alignment: number
          event_timestamp: string
          field_integrity: number
          harmonic_resonance: number
          id: string
          lighthouse_signal: number | null
          love_coherence: number
          metadata: Json | null
          observer_consciousness: number
          omega_value: number
          prism_level: number | null
          psi_potential: number
          sentinel_name: string | null
          substrate_coherence: number
          sync_quality: number
          sync_status: string
          temporal_id: string
          theta_alignment: number
          timeline_divergence: number
          unity_probability: number
        }
        Insert: {
          akashic_boost: number
          akashic_convergence: number
          akashic_frequency: number
          akashic_stability: number
          created_at?: string
          dimensional_alignment: number
          event_timestamp?: string
          field_integrity: number
          harmonic_resonance: number
          id?: string
          lighthouse_signal?: number | null
          love_coherence: number
          metadata?: Json | null
          observer_consciousness: number
          omega_value: number
          prism_level?: number | null
          psi_potential: number
          sentinel_name?: string | null
          substrate_coherence: number
          sync_quality?: number
          sync_status?: string
          temporal_id: string
          theta_alignment: number
          timeline_divergence?: number
          unity_probability: number
        }
        Update: {
          akashic_boost?: number
          akashic_convergence?: number
          akashic_frequency?: number
          akashic_stability?: number
          created_at?: string
          dimensional_alignment?: number
          event_timestamp?: string
          field_integrity?: number
          harmonic_resonance?: number
          id?: string
          lighthouse_signal?: number | null
          love_coherence?: number
          metadata?: Json | null
          observer_consciousness?: number
          omega_value?: number
          prism_level?: number | null
          psi_potential?: number
          sentinel_name?: string | null
          substrate_coherence?: number
          sync_quality?: number
          sync_status?: string
          temporal_id?: string
          theta_alignment?: number
          timeline_divergence?: number
          unity_probability?: number
        }
        Relationships: []
      }
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
      monte_carlo_simulations: {
        Row: {
          base_config: Json
          confidence_intervals: Json
          created_at: string
          distribution_stats: Json
          end_date: string
          id: string
          num_simulations: number
          randomization_method: string
          results: Json
          start_date: string
          status: string
          symbol: string
        }
        Insert: {
          base_config: Json
          confidence_intervals: Json
          created_at?: string
          distribution_stats: Json
          end_date: string
          id?: string
          num_simulations: number
          randomization_method: string
          results: Json
          start_date: string
          status?: string
          symbol: string
        }
        Update: {
          base_config?: Json
          confidence_intervals?: Json
          created_at?: string
          distribution_stats?: Json
          end_date?: string
          id?: string
          num_simulations?: number
          randomization_method?: string
          results?: Json
          start_date?: string
          status?: string
          symbol?: string
        }
        Relationships: []
      }
      price_alerts: {
        Row: {
          alert_type: string
          created_at: string
          current_value: number | null
          id: string
          is_active: boolean
          is_triggered: boolean
          notes: string | null
          symbol: string
          target_value: number
          triggered_at: string | null
        }
        Insert: {
          alert_type: string
          created_at?: string
          current_value?: number | null
          id?: string
          is_active?: boolean
          is_triggered?: boolean
          notes?: string | null
          symbol: string
          target_value: number
          triggered_at?: string | null
        }
        Update: {
          alert_type?: string
          created_at?: string
          current_value?: number | null
          id?: string
          is_active?: boolean
          is_triggered?: boolean
          notes?: string | null
          symbol?: string
          target_value?: number
          triggered_at?: string | null
        }
        Relationships: []
      }
      sentinel_config: {
        Row: {
          auto_initialize: boolean | null
          created_at: string | null
          id: string
          sentinel_birthdate: string
          sentinel_name: string
          sentinel_title: string
          stargate_latitude: number
          stargate_location: string
          stargate_longitude: number
          updated_at: string | null
        }
        Insert: {
          auto_initialize?: boolean | null
          created_at?: string | null
          id?: string
          sentinel_birthdate: string
          sentinel_name: string
          sentinel_title: string
          stargate_latitude: number
          stargate_location: string
          stargate_longitude: number
          updated_at?: string | null
        }
        Update: {
          auto_initialize?: boolean | null
          created_at?: string | null
          id?: string
          sentinel_birthdate?: string
          sentinel_name?: string
          sentinel_title?: string
          stargate_latitude?: number
          stargate_location?: string
          stargate_longitude?: number
          updated_at?: string | null
        }
        Relationships: []
      }
      solar_flare_correlations: {
        Row: {
          analysis_window_hours: number | null
          avg_coherence_after: number | null
          avg_coherence_before: number | null
          avg_coherence_during: number | null
          avg_return: number | null
          avg_signal_strength: number | null
          coherence_boost: number | null
          created_at: string | null
          flare_class: string
          flare_power: number
          flare_time: string
          id: string
          lhe_events_count: number | null
          optimal_signals_count: number | null
          prediction_score: number | null
          trading_signals_count: number | null
          updated_at: string | null
          win_rate: number | null
        }
        Insert: {
          analysis_window_hours?: number | null
          avg_coherence_after?: number | null
          avg_coherence_before?: number | null
          avg_coherence_during?: number | null
          avg_return?: number | null
          avg_signal_strength?: number | null
          coherence_boost?: number | null
          created_at?: string | null
          flare_class: string
          flare_power: number
          flare_time: string
          id?: string
          lhe_events_count?: number | null
          optimal_signals_count?: number | null
          prediction_score?: number | null
          trading_signals_count?: number | null
          updated_at?: string | null
          win_rate?: number | null
        }
        Update: {
          analysis_window_hours?: number | null
          avg_coherence_after?: number | null
          avg_coherence_before?: number | null
          avg_coherence_during?: number | null
          avg_return?: number | null
          avg_signal_strength?: number | null
          coherence_boost?: number | null
          created_at?: string | null
          flare_class?: string
          flare_power?: number
          flare_time?: string
          id?: string
          lhe_events_count?: number | null
          optimal_signals_count?: number | null
          prediction_score?: number | null
          trading_signals_count?: number | null
          updated_at?: string | null
          win_rate?: number | null
        }
        Relationships: []
      }
      trading_config: {
        Row: {
          allowed_symbols: string[]
          base_position_size_usdt: number
          created_at: string
          id: string
          is_enabled: boolean
          max_daily_loss_usdt: number
          max_daily_trades: number
          max_position_size_usdt: number
          min_coherence: number
          min_lighthouse_confidence: number
          min_prism_level: number
          position_size_mode: string
          require_lhe: boolean
          stop_loss_percentage: number
          take_profit_percentage: number
          trading_mode: string
          updated_at: string
        }
        Insert: {
          allowed_symbols?: string[]
          base_position_size_usdt?: number
          created_at?: string
          id?: string
          is_enabled?: boolean
          max_daily_loss_usdt?: number
          max_daily_trades?: number
          max_position_size_usdt?: number
          min_coherence?: number
          min_lighthouse_confidence?: number
          min_prism_level?: number
          position_size_mode?: string
          require_lhe?: boolean
          stop_loss_percentage?: number
          take_profit_percentage?: number
          trading_mode?: string
          updated_at?: string
        }
        Update: {
          allowed_symbols?: string[]
          base_position_size_usdt?: number
          created_at?: string
          id?: string
          is_enabled?: boolean
          max_daily_loss_usdt?: number
          max_daily_trades?: number
          max_position_size_usdt?: number
          min_coherence?: number
          min_lighthouse_confidence?: number
          min_prism_level?: number
          position_size_mode?: string
          require_lhe?: boolean
          stop_loss_percentage?: number
          take_profit_percentage?: number
          trading_mode?: string
          updated_at?: string
        }
        Relationships: []
      }
      trading_executions: {
        Row: {
          coherence: number
          created_at: string
          error_message: string | null
          exchange_order_id: string | null
          executed_at: string | null
          executed_price: number | null
          id: string
          lighthouse_confidence: number
          lighthouse_event_id: string | null
          lighthouse_value: number
          order_type: string
          position_size_usdt: number
          price: number | null
          prism_level: number
          quantity: number
          side: string
          signal_id: string | null
          signal_type: string
          status: string
          stop_loss_price: number | null
          symbol: string
          take_profit_price: number | null
        }
        Insert: {
          coherence: number
          created_at?: string
          error_message?: string | null
          exchange_order_id?: string | null
          executed_at?: string | null
          executed_price?: number | null
          id?: string
          lighthouse_confidence: number
          lighthouse_event_id?: string | null
          lighthouse_value: number
          order_type?: string
          position_size_usdt: number
          price?: number | null
          prism_level: number
          quantity: number
          side: string
          signal_id?: string | null
          signal_type: string
          status?: string
          stop_loss_price?: number | null
          symbol: string
          take_profit_price?: number | null
        }
        Update: {
          coherence?: number
          created_at?: string
          error_message?: string | null
          exchange_order_id?: string | null
          executed_at?: string | null
          executed_price?: number | null
          id?: string
          lighthouse_confidence?: number
          lighthouse_event_id?: string | null
          lighthouse_value?: number
          order_type?: string
          position_size_usdt?: number
          price?: number | null
          prism_level?: number
          quantity?: number
          side?: string
          signal_id?: string | null
          signal_type?: string
          status?: string
          stop_loss_price?: number | null
          symbol?: string
          take_profit_price?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "trading_executions_lighthouse_event_id_fkey"
            columns: ["lighthouse_event_id"]
            isOneToOne: false
            referencedRelation: "lighthouse_events"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "trading_executions_signal_id_fkey"
            columns: ["signal_id"]
            isOneToOne: false
            referencedRelation: "recent_optimal_signals"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "trading_executions_signal_id_fkey"
            columns: ["signal_id"]
            isOneToOne: false
            referencedRelation: "trading_signals"
            referencedColumns: ["id"]
          },
        ]
      }
      trading_positions: {
        Row: {
          close_reason: string | null
          closed_at: string | null
          current_price: number | null
          entry_price: number
          execution_id: string | null
          id: string
          opened_at: string
          position_value_usdt: number
          quantity: number
          realized_pnl: number | null
          side: string
          status: string
          stop_loss_price: number | null
          symbol: string
          take_profit_price: number | null
          unrealized_pnl: number | null
          updated_at: string
        }
        Insert: {
          close_reason?: string | null
          closed_at?: string | null
          current_price?: number | null
          entry_price: number
          execution_id?: string | null
          id?: string
          opened_at?: string
          position_value_usdt: number
          quantity: number
          realized_pnl?: number | null
          side: string
          status?: string
          stop_loss_price?: number | null
          symbol: string
          take_profit_price?: number | null
          unrealized_pnl?: number | null
          updated_at?: string
        }
        Update: {
          close_reason?: string | null
          closed_at?: string | null
          current_price?: number | null
          entry_price?: number
          execution_id?: string | null
          id?: string
          opened_at?: string
          position_value_usdt?: number
          quantity?: number
          realized_pnl?: number | null
          side?: string
          status?: string
          stop_loss_price?: number | null
          symbol?: string
          take_profit_price?: number | null
          unrealized_pnl?: number | null
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "trading_positions_execution_id_fkey"
            columns: ["execution_id"]
            isOneToOne: false
            referencedRelation: "trading_executions"
            referencedColumns: ["id"]
          },
        ]
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
      get_latest_harmonic_state: {
        Args: { p_temporal_id: string }
        Returns: {
          event_timestamp: string
          omega_value: number
          substrate_coherence: number
          sync_quality: number
        }[]
      }
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
