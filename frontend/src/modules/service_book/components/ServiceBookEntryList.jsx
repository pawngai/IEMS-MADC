import React from "react";
import { CheckCircle, FileText } from "lucide-react";
import {
  PART_COLORS,
  PART_ICONS,
  PART_NAMES,
} from "@/modules/service_book/components/serviceBookLedger.constants";
import { getPartStats } from "@/modules/service_book/components/serviceBookLedger.utils";

export default function ServiceBookEntryList({
  partKeys,
  activePart,
  onSelectPart,
  serviceBook,
  partsInfo,
  getPartData,
  completionPct,
}) {
  return (
    <aside className="w-full lg:w-56 shrink-0 border-b lg:border-b-0 lg:border-r border-slate-200 bg-slate-50 flex flex-col">
      <div className="px-3 py-2.5 border-b border-slate-200">
        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Parts Index</p>
      </div>

      <nav className="flex-1 flex lg:flex-col gap-1 overflow-x-auto lg:overflow-x-visible lg:overflow-y-auto py-1 px-1 lg:px-0" role="tablist" aria-label="Service Book parts">
        {partKeys.map((key) => {
          const isActive = activePart === key;
          const isCompleted = serviceBook?.parts_completed?.includes(key);
          const partData = getPartData(serviceBook, key);
          const { entryCount, hasDrafts } = getPartStats(key, partData);
          const Icon = PART_ICONS[key] || FileText;

          return (
            <button
              key={key}
              role="tab"
              aria-selected={isActive}
              aria-label={`Part ${key}: ${PART_NAMES[key]}`}
              onClick={() => onSelectPart(key)}
              className={`w-full min-w-[160px] lg:min-w-0 text-left px-3 py-2 flex items-center gap-2.5 transition-colors relative group ${
                isActive
                  ? "bg-blue-50 border-l-[3px] border-l-blue-600 shadow-sm"
                  : "border-l-[3px] border-l-transparent hover:bg-slate-100"
              }`}
            >
              <div className={`p-1 rounded ${isActive ? PART_COLORS[key] : isCompleted ? PART_COLORS[key] : "bg-slate-200 text-slate-400"}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className={`text-xs font-semibold ${isActive ? "text-blue-700" : "text-slate-600"}`}>
                  Part {key}
                </div>
                <div className="text-[11px] text-slate-400 truncate leading-tight">
                  {PART_NAMES[key] || partsInfo[key]?.name || ""}
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {hasDrafts && <span className="w-2 h-2 rounded-full bg-amber-400" title="Has draft entries" />}
                {isCompleted ? (
                  <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                ) : entryCount > 0 ? (
                  <span className="text-[10px] text-slate-400 font-medium">{entryCount}</span>
                ) : null}
              </div>
            </button>
          );
        })}
      </nav>

      <div className="px-3 py-2.5 border-t border-slate-200 bg-slate-50">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-slate-400 font-medium">Completion</span>
          <span className="text-[10px] text-slate-500 font-semibold">{completionPct}%</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-1.5">
          <div className="bg-blue-600 h-1.5 rounded-full transition-all duration-500" style={{ width: `${completionPct}%` }} />
        </div>
      </div>
    </aside>
  );
}
