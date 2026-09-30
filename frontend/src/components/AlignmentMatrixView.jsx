import React from 'react';
import { Check, AlertTriangle, Table2 } from 'lucide-react';

export default function AlignmentMatrixView({ alignmentMatrix, objectives = [] }) {
  if (!alignmentMatrix || !alignmentMatrix.matrix) return null;

  const { matrix, counts, uncovered_objectives } = alignmentMatrix;
  const itemKeys = Object.keys(matrix);
  const objCodes = objectives.map(o => o.code);

  return (
    <div className="premium-card p-6 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2E8F0] pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-[#123C35] text-white shadow-sm">
            <Table2 className="w-4 h-4 text-[#D4AF37]" />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#123C35] tracking-tight">Objective Alignment Matrix</h3>
            <p className="text-xs text-[#64748B]">Deterministic bipartite mapping of learning objectives to assets</p>
          </div>
        </div>
        {uncovered_objectives && uncovered_objectives.length > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-300 text-amber-800 text-xs font-semibold shadow-sm">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>Uncovered Objectives: {uncovered_objectives.join(', ')}</span>
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[#64748B]">
              <th className="py-3 px-4 font-bold text-[#123C35]">Learning Asset</th>
              {objCodes.map(code => (
                <th key={code} className="py-3 px-4 text-center font-mono text-[#123C35] font-bold">
                  {code}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] text-[#1F2937]">
            {itemKeys.map(k => {
              const row = matrix[k];
              return (
                <tr key={k} className="hover:bg-[#F8FAFC] transition">
                  <td className="py-2.5 px-4 font-semibold text-[#1F2937] flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#123C35] shrink-0" />
                    <span>{row.name}</span>
                  </td>
                  {objCodes.map(code => {
                    const isCovered = row.coverage[code];
                    return (
                      <td key={code} className="py-2.5 px-4 text-center">
                        {isCovered ? (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] font-bold shadow-sm">
                            <Check className="w-3.5 h-3.5" />
                          </span>
                        ) : (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#F8FAFC] border border-[#E2E8F0] text-[#94A3B8] font-mono">
                            -
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-[#E2E8F0] font-bold text-[#123C35] bg-[#F8FAFC]">
              <td className="py-3 px-4">Coverage Frequency</td>
              {objCodes.map(code => (
                <td key={code} className="py-3 px-4 text-center font-mono font-bold">
                  {counts[code] || 0}
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
