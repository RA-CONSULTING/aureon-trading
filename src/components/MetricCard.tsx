import React from "react";
import { fmt } from "@/utils/number";

type MetricCardProps = {
  label: string;
  value?: number | string | null;
  unit?: string;
  digits?: number;
};

export default function MetricCard({ 
  label, 
  value, 
  unit, 
  digits = 2 
}: MetricCardProps) {
  const display = typeof value === 'string' ? value : fmt(value, digits);
  
  return (
    <div className="rounded-xl bg-zinc-900/60 p-3">
      <div className="text-xs text-zinc-400">{label}</div>
      <div className="text-xl font-semibold text-zinc-100">
        {display}{unit ? ` ${unit}` : ""}
      </div>
    </div>
  );
}