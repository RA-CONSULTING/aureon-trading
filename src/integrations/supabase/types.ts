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
      data_access_audit: {
        Row: {
          access_type: string
          accessed_by: string | null
          id: string
          ip_address: string | null
          metadata: Json | null
          resource_type: string
          timestamp: string
          user_id: string
        }
        Insert: {
          access_type: string
          accessed_by?: string | null
          id?: string
          ip_address?: string | null
          metadata?: Json | null
          resource_type: string
          timestamp?: string
          user_id: string
        }
        Update: {
          access_type?: string
          accessed_by?: string | null
          id?: string
          ip_address?: string | null
          metadata?: Json | null
          resource_type?: string
          timestamp?: string
          user_id?: string
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
      hive_agents: {
        Row: {
          agent_index: number
          created_at: string
          current_symbol: string
          hive_id: string
          id: string
          last_trade_at: string | null
          position_entry_price: number | null
          position_open: boolean
          position_quantity: number | null
          position_side: string | null
          total_pnl: number
          trades_count: number
        }
        Insert: {
          agent_index: number
          created_at?: string
          current_symbol: string
          hive_id: string
          id?: string
          last_trade_at?: string | null
          position_entry_price?: number | null
          position_open?: boolean
          position_quantity?: number | null
          position_side?: string | null
          total_pnl?: number
          trades_count?: number
        }
        Update: {
          agent_index?: number
          created_at?: string
          current_symbol?: string
          hive_id?: string
          id?: string
          last_trade_at?: string | null
          position_entry_price?: number | null
          position_open?: boolean
          position_quantity?: number | null
          position_side?: string | null
          total_pnl?: number
          trades_count?: number
        }
        Relationships: [
          {
            foreignKeyName: "hive_agents_hive_id_fkey"
            columns: ["hive_id"]
            isOneToOne: false
            referencedRelation: "hive_instances"
            referencedColumns: ["id"]
          },
        ]
      }
      hive_instances: {
        Row: {
          created_at: string
          current_balance: number
          generation: number
          id: string
          initial_balance: number
          num_agents: number
          parent_hive_id: string | null
          status: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          current_balance: number
          generation?: number
          id?: string
          initial_balance: number
          num_agents?: number
          parent_hive_id?: string | null
          status?: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          current_balance?: number
          generation?: number
          id?: string
          initial_balance?: number
          num_agents?: number
          parent_hive_id?: string | null
          status?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "hive_instances_parent_hive_id_fkey"
            columns: ["parent_hive_id"]
            isOneToOne: false
            referencedRelation: "hive_instances"
            referencedColumns: ["id"]
          },
        ]
      }
      hive_sessions: {
        Row: {
          created_at: string
          current_equity: number
          id: string
          initial_capital: number
          root_hive_id: string
          started_at: string
          status: string
          steps_executed: number
          stopped_at: string | null
          total_agents: number
          total_hives_spawned: number
          total_trades: number
          user_id: string
        }
        Insert: {
          created_at?: string
          current_equity: number
          id?: string
          initial_capital: number
          root_hive_id: string
          started_at?: string
          status?: string
          steps_executed?: number
          stopped_at?: string | null
          total_agents?: number
          total_hives_spawned?: number
          total_trades?: number
          user_id: string
        }
        Update: {
          created_at?: string
          current_equity?: number
          id?: string
          initial_capital?: number
          root_hive_id?: string
          started_at?: string
          status?: string
          steps_executed?: number
          stopped_at?: string | null
          total_agents?: number
          total_hives_spawned?: number
          total_trades?: number
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "hive_sessions_root_hive_id_fkey"
            columns: ["root_hive_id"]
            isOneToOne: false
            referencedRelation: "hive_instances"
            referencedColumns: ["id"]
          },
        ]
      }
      hive_trades: {
        Row: {
          agent_id: string
          closed_at: string | null
          created_at: string
          entry_price: number
          exit_price: number | null
          hive_id: string
          id: string
          opened_at: string
          pnl: number | null
          quantity: number
          session_id: string
          side: string
          status: string
          symbol: string
        }
        Insert: {
          agent_id: string
          closed_at?: string | null
          created_at?: string
          entry_price: number
          exit_price?: number | null
          hive_id: string
          id?: string
          opened_at?: string
          pnl?: number | null
          quantity: number
          session_id: string
          side: string
          status?: string
          symbol: string
        }
        Update: {
          agent_id?: string
          closed_at?: string | null
          created_at?: string
          entry_price?: number
          exit_price?: number | null
          hive_id?: string
          id?: string
          opened_at?: string
          pnl?: number | null
          quantity?: number
          session_id?: string
          side?: string
          status?: string
          symbol?: string
        }
        Relationships: [
          {
            foreignKeyName: "hive_trades_agent_id_fkey"
            columns: ["agent_id"]
            isOneToOne: false
            referencedRelation: "hive_agents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "hive_trades_hive_id_fkey"
            columns: ["hive_id"]
            isOneToOne: false
            referencedRelation: "hive_instances"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "hive_trades_session_id_fkey"
            columns: ["session_id"]
            isOneToOne: false
            referencedRelation: "hive_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      hunt_scans: {
        Row: {
          created_at: string
          hunt_session_id: string
          id: string
          orders_queued: number
          pairs_scanned: number
          scan_duration_ms: number
          scan_timestamp: string
          signals_generated: number
          targets_found: number
          top_score: number | null
          top_symbol: string | null
        }
        Insert: {
          created_at?: string
          hunt_session_id: string
          id?: string
          orders_queued: number
          pairs_scanned: number
          scan_duration_ms: number
          scan_timestamp?: string
          signals_generated: number
          targets_found: number
          top_score?: number | null
          top_symbol?: string | null
        }
        Update: {
          created_at?: string
          hunt_session_id?: string
          id?: string
          orders_queued?: number
          pairs_scanned?: number
          scan_duration_ms?: number
          scan_timestamp?: string
          signals_generated?: number
          targets_found?: number
          top_score?: number | null
          top_symbol?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "hunt_scans_hunt_session_id_fkey"
            columns: ["hunt_session_id"]
            isOneToOne: false
            referencedRelation: "hunt_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      hunt_sessions: {
        Row: {
          created_at: string
          hive_session_id: string | null
          id: string
          last_scan_at: string | null
          max_targets: number
          min_volatility_pct: number
          min_volume_usd: number
          scan_interval_seconds: number
          started_at: string
          status: string
          stopped_at: string | null
          total_orders_queued: number
          total_scans: number
          total_signals_generated: number
          total_targets_found: number
          twap_duration_seconds: number | null
          twap_threshold_usd: number | null
          user_id: string
        }
        Insert: {
          created_at?: string
          hive_session_id?: string | null
          id?: string
          last_scan_at?: string | null
          max_targets?: number
          min_volatility_pct?: number
          min_volume_usd?: number
          scan_interval_seconds?: number
          started_at?: string
          status?: string
          stopped_at?: string | null
          total_orders_queued?: number
          total_scans?: number
          total_signals_generated?: number
          total_targets_found?: number
          twap_duration_seconds?: number | null
          twap_threshold_usd?: number | null
          user_id: string
        }
        Update: {
          created_at?: string
          hive_session_id?: string | null
          id?: string
          last_scan_at?: string | null
          max_targets?: number
          min_volatility_pct?: number
          min_volume_usd?: number
          scan_interval_seconds?: number
          started_at?: string
          status?: string
          stopped_at?: string | null
          total_orders_queued?: number
          total_scans?: number
          total_signals_generated?: number
          total_targets_found?: number
          twap_duration_seconds?: number | null
          twap_threshold_usd?: number | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "hunt_sessions_hive_session_id_fkey"
            columns: ["hive_session_id"]
            isOneToOne: false
            referencedRelation: "hive_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      hunt_targets: {
        Row: {
          base_asset: string
          created_at: string
          discovered_at: string
          hunt_session_id: string
          id: string
          opportunity_score: number
          order_queued: boolean | null
          price: number
          processed_at: string | null
          quote_asset: string
          rejection_reason: string | null
          signal_confidence: number | null
          signal_generated: boolean | null
          signal_tier: number | null
          signal_type: string | null
          status: string
          symbol: string
          volatility_24h: number
          volume_24h: number
        }
        Insert: {
          base_asset: string
          created_at?: string
          discovered_at?: string
          hunt_session_id: string
          id?: string
          opportunity_score: number
          order_queued?: boolean | null
          price: number
          processed_at?: string | null
          quote_asset: string
          rejection_reason?: string | null
          signal_confidence?: number | null
          signal_generated?: boolean | null
          signal_tier?: number | null
          signal_type?: string | null
          status?: string
          symbol: string
          volatility_24h: number
          volume_24h: number
        }
        Update: {
          base_asset?: string
          created_at?: string
          discovered_at?: string
          hunt_session_id?: string
          id?: string
          opportunity_score?: number
          order_queued?: boolean | null
          price?: number
          processed_at?: string | null
          quote_asset?: string
          rejection_reason?: string | null
          signal_confidence?: number | null
          signal_generated?: boolean | null
          signal_tier?: number | null
          signal_type?: string | null
          status?: string
          symbol?: string
          volatility_24h?: number
          volume_24h?: number
        }
        Relationships: [
          {
            foreignKeyName: "hunt_targets_hunt_session_id_fkey"
            columns: ["hunt_session_id"]
            isOneToOne: false
            referencedRelation: "hunt_sessions"
            referencedColumns: ["id"]
          },
        ]
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
          metric_geff?: number
          metric_q?: number
          prism_level?: number | null
          prism_state?: string | null
          threshold?: number
          timestamp?: string
        }
        Relationships: []
      }
      master_equation_field_history: {
        Row: {
          coherence: number
          coherence_linear: number
          coherence_nonlinear: number
          coherence_phi: number
          created_at: string
          dominant_node: string
          echo: number
          effective_gain: number
          id: string
          lambda: number
          metadata: Json | null
          momentum: number | null
          node_weights: Json
          observer: number
          price: number | null
          quality_factor: number
          sentinel_name: string | null
          substrate: number
          symbol: string | null
          temporal_id: string
          timestamp: string
          volatility: number | null
          volume: number | null
        }
        Insert: {
          coherence: number
          coherence_linear?: number
          coherence_nonlinear: number
          coherence_phi: number
          created_at?: string
          dominant_node: string
          echo: number
          effective_gain: number
          id?: string
          lambda: number
          metadata?: Json | null
          momentum?: number | null
          node_weights?: Json
          observer: number
          price?: number | null
          quality_factor: number
          sentinel_name?: string | null
          substrate: number
          symbol?: string | null
          temporal_id: string
          timestamp?: string
          volatility?: number | null
          volume?: number | null
        }
        Update: {
          coherence?: number
          coherence_linear?: number
          coherence_nonlinear?: number
          coherence_phi?: number
          created_at?: string
          dominant_node?: string
          echo?: number
          effective_gain?: number
          id?: string
          lambda?: number
          metadata?: Json | null
          momentum?: number | null
          node_weights?: Json
          observer?: number
          price?: number | null
          quality_factor?: number
          sentinel_name?: string | null
          substrate?: number
          symbol?: string | null
          temporal_id?: string
          timestamp?: string
          volatility?: number | null
          volume?: number | null
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
      oms_execution_metrics: {
        Row: {
          avg_execution_latency_ms: number | null
          avg_wait_time_ms: number | null
          created_at: string
          current_window_orders: number
          id: string
          orders_executed_last_minute: number
          orders_failed_last_minute: number
          queue_depth: number
          rate_limit_utilization: number
          timestamp: string
        }
        Insert: {
          avg_execution_latency_ms?: number | null
          avg_wait_time_ms?: number | null
          created_at?: string
          current_window_orders: number
          id?: string
          orders_executed_last_minute: number
          orders_failed_last_minute: number
          queue_depth: number
          rate_limit_utilization: number
          timestamp?: string
        }
        Update: {
          avg_execution_latency_ms?: number | null
          avg_wait_time_ms?: number | null
          created_at?: string
          current_window_orders?: number
          id?: string
          orders_executed_last_minute?: number
          orders_failed_last_minute?: number
          queue_depth?: number
          rate_limit_utilization?: number
          timestamp?: string
        }
        Relationships: []
      }
      oms_order_queue: {
        Row: {
          agent_id: string
          cancelled_at: string | null
          coherence: number | null
          created_at: string
          error_message: string | null
          exchange_order_id: string | null
          executed_at: string | null
          executed_price: number | null
          executed_quantity: number | null
          hive_id: string
          id: string
          lighthouse_value: number | null
          order_type: string
          price: number
          priority: number
          quantity: number
          queued_at: string
          session_id: string
          side: string
          signal_strength: number | null
          status: string
          symbol: string
        }
        Insert: {
          agent_id: string
          cancelled_at?: string | null
          coherence?: number | null
          created_at?: string
          error_message?: string | null
          exchange_order_id?: string | null
          executed_at?: string | null
          executed_price?: number | null
          executed_quantity?: number | null
          hive_id: string
          id?: string
          lighthouse_value?: number | null
          order_type?: string
          price: number
          priority?: number
          quantity: number
          queued_at?: string
          session_id: string
          side: string
          signal_strength?: number | null
          status?: string
          symbol: string
        }
        Update: {
          agent_id?: string
          cancelled_at?: string | null
          coherence?: number | null
          created_at?: string
          error_message?: string | null
          exchange_order_id?: string | null
          executed_at?: string | null
          executed_price?: number | null
          executed_quantity?: number | null
          hive_id?: string
          id?: string
          lighthouse_value?: number | null
          order_type?: string
          price?: number
          priority?: number
          quantity?: number
          queued_at?: string
          session_id?: string
          side?: string
          signal_strength?: number | null
          status?: string
          symbol?: string
        }
        Relationships: [
          {
            foreignKeyName: "oms_order_queue_agent_id_fkey"
            columns: ["agent_id"]
            isOneToOne: false
            referencedRelation: "hive_agents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "oms_order_queue_hive_id_fkey"
            columns: ["hive_id"]
            isOneToOne: false
            referencedRelation: "hive_instances"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "oms_order_queue_session_id_fkey"
            columns: ["session_id"]
            isOneToOne: false
            referencedRelation: "hive_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      oms_rate_limit_windows: {
        Row: {
          created_at: string
          id: string
          orders_executed: number
          window_end: string
          window_start: string
        }
        Insert: {
          created_at?: string
          id?: string
          orders_executed?: number
          window_end: string
          window_start: string
        }
        Update: {
          created_at?: string
          id?: string
          orders_executed?: number
          window_end?: string
          window_start?: string
        }
        Relationships: []
      }
      payment_transactions: {
        Row: {
          amount: number
          created_at: string
          currency: string
          id: string
          metadata: Json | null
          paid_at: string | null
          payment_provider: string
          payment_status: string
          payment_url: string | null
          transaction_reference: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          amount: number
          created_at?: string
          currency?: string
          id?: string
          metadata?: Json | null
          paid_at?: string | null
          payment_provider?: string
          payment_status?: string
          payment_url?: string | null
          transaction_reference?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          amount?: number
          created_at?: string
          currency?: string
          id?: string
          metadata?: Json | null
          paid_at?: string | null
          payment_provider?: string
          payment_status?: string
          payment_url?: string | null
          transaction_reference?: string | null
          updated_at?: string
          user_id?: string
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
      prism_transformation_states: {
        Row: {
          coherence: number
          created_at: string
          frequency: number
          harmonic_purity: number
          id: string
          input_frequency: number
          is_lhe_correlated: boolean | null
          is_love_locked: boolean | null
          lambda_value: number
          level: number
          lighthouse_event_id: string | null
          lighthouse_signal: number | null
          metadata: Json | null
          resonance_strength: number
          sentinel_name: string | null
          state: string
          temporal_id: string
          timestamp: string
          transformation_quality: number
        }
        Insert: {
          coherence: number
          created_at?: string
          frequency: number
          harmonic_purity: number
          id?: string
          input_frequency: number
          is_lhe_correlated?: boolean | null
          is_love_locked?: boolean | null
          lambda_value: number
          level: number
          lighthouse_event_id?: string | null
          lighthouse_signal?: number | null
          metadata?: Json | null
          resonance_strength: number
          sentinel_name?: string | null
          state: string
          temporal_id: string
          timestamp?: string
          transformation_quality: number
        }
        Update: {
          coherence?: number
          created_at?: string
          frequency?: number
          harmonic_purity?: number
          id?: string
          input_frequency?: number
          is_lhe_correlated?: boolean | null
          is_love_locked?: boolean | null
          lambda_value?: number
          level?: number
          lighthouse_event_id?: string | null
          lighthouse_signal?: number | null
          metadata?: Json | null
          resonance_strength?: number
          sentinel_name?: string | null
          state?: string
          temporal_id?: string
          timestamp?: string
          transformation_quality?: number
        }
        Relationships: [
          {
            foreignKeyName: "prism_transformation_states_lighthouse_event_id_fkey"
            columns: ["lighthouse_event_id"]
            isOneToOne: false
            referencedRelation: "lighthouse_events"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          created_at: string
          data_consent_date: string | null
          data_consent_given: boolean | null
          date_of_birth: string | null
          email: string | null
          full_name: string | null
          id: string
          id_document_path: string | null
          kyc_status: string | null
          kyc_verified_at: string | null
          location: string | null
          payment_completed: boolean | null
          payment_completed_at: string | null
          updated_at: string
        }
        Insert: {
          created_at?: string
          data_consent_date?: string | null
          data_consent_given?: boolean | null
          date_of_birth?: string | null
          email?: string | null
          full_name?: string | null
          id: string
          id_document_path?: string | null
          kyc_status?: string | null
          kyc_verified_at?: string | null
          location?: string | null
          payment_completed?: boolean | null
          payment_completed_at?: string | null
          updated_at?: string
        }
        Update: {
          created_at?: string
          data_consent_date?: string | null
          data_consent_given?: boolean | null
          date_of_birth?: string | null
          email?: string | null
          full_name?: string | null
          id?: string
          id_document_path?: string | null
          kyc_status?: string | null
          kyc_verified_at?: string | null
          location?: string | null
          payment_completed?: boolean | null
          payment_completed_at?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      rainbow_bridge_states: {
        Row: {
          arousal: number
          base_frequency: number
          coherence: number
          color: string
          created_at: string
          dominant_emotion: string
          emotional_tags: string[] | null
          frequency: number
          harmonic_index: number
          id: string
          intensity: number
          lambda_value: number
          metadata: Json | null
          phase: string
          phase_transition: boolean | null
          previous_phase: string | null
          sentinel_name: string | null
          temporal_id: string
          timestamp: string
          valence: number
        }
        Insert: {
          arousal: number
          base_frequency: number
          coherence: number
          color: string
          created_at?: string
          dominant_emotion: string
          emotional_tags?: string[] | null
          frequency: number
          harmonic_index: number
          id?: string
          intensity: number
          lambda_value: number
          metadata?: Json | null
          phase: string
          phase_transition?: boolean | null
          previous_phase?: string | null
          sentinel_name?: string | null
          temporal_id: string
          timestamp?: string
          valence: number
        }
        Update: {
          arousal?: number
          base_frequency?: number
          coherence?: number
          color?: string
          created_at?: string
          dominant_emotion?: string
          emotional_tags?: string[] | null
          frequency?: number
          harmonic_index?: number
          id?: string
          intensity?: number
          lambda_value?: number
          metadata?: Json | null
          phase?: string
          phase_transition?: boolean | null
          previous_phase?: string | null
          sentinel_name?: string | null
          temporal_id?: string
          timestamp?: string
          valence?: number
        }
        Relationships: []
      }
      scheduler_history: {
        Row: {
          action: string
          coherence_at_action: number
          created_at: string
          daily_activations: number
          id: string
          lighthouse_events_count: number
          metadata: Json | null
          reason: string
          timestamp: string
          trading_enabled_after: boolean
          trading_enabled_before: boolean
        }
        Insert: {
          action: string
          coherence_at_action: number
          created_at?: string
          daily_activations?: number
          id?: string
          lighthouse_events_count?: number
          metadata?: Json | null
          reason: string
          timestamp?: string
          trading_enabled_after: boolean
          trading_enabled_before: boolean
        }
        Update: {
          action?: string
          coherence_at_action?: number
          created_at?: string
          daily_activations?: number
          id?: string
          lighthouse_events_count?: number
          metadata?: Json | null
          reason?: string
          timestamp?: string
          trading_enabled_after?: boolean
          trading_enabled_before?: boolean
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
      stargate_network_states: {
        Row: {
          active_nodes: number
          avg_coherence: number | null
          avg_frequency: number | null
          created_at: string
          event_timestamp: string
          grid_energy: number
          id: string
          metadata: Json | null
          network_strength: number
          phase_locks: number | null
          resonance_quality: number | null
          sentinel_name: string | null
          temporal_id: string
        }
        Insert: {
          active_nodes: number
          avg_coherence?: number | null
          avg_frequency?: number | null
          created_at?: string
          event_timestamp?: string
          grid_energy: number
          id?: string
          metadata?: Json | null
          network_strength: number
          phase_locks?: number | null
          resonance_quality?: number | null
          sentinel_name?: string | null
          temporal_id: string
        }
        Update: {
          active_nodes?: number
          avg_coherence?: number | null
          avg_frequency?: number | null
          created_at?: string
          event_timestamp?: string
          grid_energy?: number
          id?: string
          metadata?: Json | null
          network_strength?: number
          phase_locks?: number | null
          resonance_quality?: number | null
          sentinel_name?: string | null
          temporal_id?: string
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
      twap_orders: {
        Row: {
          algo_id: number | null
          algo_status: string | null
          avg_price: number | null
          book_time: string | null
          client_algo_id: string
          created_at: string
          duration_seconds: number
          end_time: string | null
          error_code: number | null
          error_message: string | null
          executed_amount: number | null
          executed_quantity: number | null
          hunt_session_id: string | null
          id: string
          limit_price: number | null
          metadata: Json | null
          oms_order_id: string | null
          side: string
          symbol: string
          total_quantity: number
          updated_at: string
          urgency: string | null
        }
        Insert: {
          algo_id?: number | null
          algo_status?: string | null
          avg_price?: number | null
          book_time?: string | null
          client_algo_id: string
          created_at?: string
          duration_seconds: number
          end_time?: string | null
          error_code?: number | null
          error_message?: string | null
          executed_amount?: number | null
          executed_quantity?: number | null
          hunt_session_id?: string | null
          id?: string
          limit_price?: number | null
          metadata?: Json | null
          oms_order_id?: string | null
          side: string
          symbol: string
          total_quantity: number
          updated_at?: string
          urgency?: string | null
        }
        Update: {
          algo_id?: number | null
          algo_status?: string | null
          avg_price?: number | null
          book_time?: string | null
          client_algo_id?: string
          created_at?: string
          duration_seconds?: number
          end_time?: string | null
          error_code?: number | null
          error_message?: string | null
          executed_amount?: number | null
          executed_quantity?: number | null
          hunt_session_id?: string | null
          id?: string
          limit_price?: number | null
          metadata?: Json | null
          oms_order_id?: string | null
          side?: string
          symbol?: string
          total_quantity?: number
          updated_at?: string
          urgency?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "twap_orders_hunt_session_id_fkey"
            columns: ["hunt_session_id"]
            isOneToOne: false
            referencedRelation: "hunt_sessions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "twap_orders_oms_order_id_fkey"
            columns: ["oms_order_id"]
            isOneToOne: false
            referencedRelation: "oms_order_queue"
            referencedColumns: ["id"]
          },
        ]
      }
      twap_sub_orders: {
        Row: {
          avg_price: number | null
          book_time: string
          created_at: string
          executed_amount: number
          executed_quantity: number
          fee_amount: number | null
          fee_asset: string | null
          id: string
          order_id: number
          order_status: string
          orig_quantity: number
          side: string
          sub_id: number
          symbol: string
          time_in_force: string | null
          twap_order_id: string
        }
        Insert: {
          avg_price?: number | null
          book_time: string
          created_at?: string
          executed_amount?: number
          executed_quantity?: number
          fee_amount?: number | null
          fee_asset?: string | null
          id?: string
          order_id: number
          order_status: string
          orig_quantity: number
          side: string
          sub_id: number
          symbol: string
          time_in_force?: string | null
          twap_order_id: string
        }
        Update: {
          avg_price?: number | null
          book_time?: string
          created_at?: string
          executed_amount?: number
          executed_quantity?: number
          fee_amount?: number | null
          fee_asset?: string | null
          id?: string
          order_id?: number
          order_status?: string
          orig_quantity?: number
          side?: string
          sub_id?: number
          symbol?: string
          time_in_force?: string | null
          twap_order_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "twap_sub_orders_twap_order_id_fkey"
            columns: ["twap_order_id"]
            isOneToOne: false
            referencedRelation: "twap_orders"
            referencedColumns: ["id"]
          },
        ]
      }
      user_binance_credentials: {
        Row: {
          api_key_encrypted: string
          api_secret_encrypted: string
          created_at: string
          id: string
          iv: string | null
          last_used_at: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          api_key_encrypted: string
          api_secret_encrypted: string
          created_at?: string
          id?: string
          iv?: string | null
          last_used_at?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          api_key_encrypted?: string
          api_secret_encrypted?: string
          created_at?: string
          id?: string
          iv?: string | null
          last_used_at?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      user_roles: {
        Row: {
          created_at: string
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
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
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["app_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      app_role: "admin" | "user"
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
    Enums: {
      app_role: ["admin", "user"],
    },
  },
} as const
