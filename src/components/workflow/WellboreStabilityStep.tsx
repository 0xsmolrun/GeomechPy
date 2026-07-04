import { useState } from 'react';
import { useAppStore } from '../../lib/store';
import { calculateBreakdownPressure, calculateBreakoutPressure, mudWeightToPpg } from '../../calculations';
import { CircleDot, AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface WellboreStabilityStepProps {
  onNext: (data: Record<string, unknown>) => void;
}

export function WellboreStabilityStep({ onNext }: WellboreStabilityStepProps) {
  const { formations, workflowSession } = useAppStore();
  const [mudWeight, setMudWeight] = useState(12);

  const porePressureData = workflowSession?.step_data?.['1'] as { results: Array<{ tvd: number; porePressure: number }> } | undefined;
  const elasticData = workflowSession?.step_data?.['2'] as { results: Array<{ formation: string; prSta: number }> } | undefined;
  const rockStrengthData = workflowSession?.step_data?.['3'] as { results: Array<{ formation: string; ucs: number; tstr: number; frictionAngle: number }> } | undefined;
  const horizontalStressesData = workflowSession?.step_data?.['4'] as { results: Array<{ formation: string; shmin: number; shmax: number }> } | undefined;

  const results = formations.map((f, i) => {
    const rsData = rockStrengthData?.results?.[i];
    const hsData = horizontalStressesData?.results?.[i];
    const elData = elasticData?.results?.[i];

    const shmax = hsData?.shmax || 12000;
    const shmin = hsData?.shmin || 10000;
    const porePressure = porePressureData?.results?.find((r) => r.tvd === f.base_depth_tvd)?.porePressure || 5000;
    const overburdenStress = shmax * 1.1;
    const ucs = rsData?.ucs || 8000;
    const tstr = rsData?.tstr || 500;
    const frictionAngle = rsData?.frictionAngle || 30;
    const prSta = elData?.prSta || 0.25;

    const breakdown = calculateBreakdownPressure(shmax, shmin, porePressure, tstr);
    const breakout = calculateBreakoutPressure(shmax, shmin, porePressure, overburdenStress, ucs, frictionAngle, prSta);
    const mudPressure = mudWeight * 0.052 * f.base_depth_tvd;
    const isSafe = mudPressure >= breakout && mudPressure <= breakdown;

    return {
      formation: f.name,
      tvd: f.base_depth_tvd,
      shmin,
      shmax,
      porePressure,
      breakout,
      breakdown,
      safeWindow: breakdown - breakout,
      mudPressure,
      isSafe,
      mudWeightPpg: mudWeight,
    };
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({
      mud_weight_ppg: mudWeight,
      results: results.map((r) => ({
        formation: r.formation,
        tvd: r.tvd,
        breakout_pressure: r.breakout,
        breakdown_pressure: r.breakdown,
        safe_mud_window: r.safeWindow,
        mud_pressure: r.mudPressure,
        is_safe: r.isSafe,
      })),
    });
  };

  return (
    <form id="workflow-form" onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700">
          <p className="font-medium mb-1">Wellbore Stability Analysis</p>
          <p>Calculate breakdown (fracture) and breakout (collapse) pressures using Mohr-Coulomb criterion for a vertical well.</p>
        </div>
      </div>

      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <h4 className="text-sm font-medium text-slate-700 mb-3">Mud Weight Analysis</h4>
        <div className="flex items-center gap-6">
          <div className="flex-1">
            <label className="label">Mud Weight (ppg)</label>
            <input
              type="number"
              value={mudWeight}
              onChange={(e) => setMudWeight(parseFloat(e.target.value) || 10)}
              className="input"
              step="0.1"
              min="8"
              max="18"
            />
          </div>
          <div className="flex-1 text-center">
            <p className="text-sm text-slate-500 mb-1">Mud Pressure at Target Depth</p>
            <p className="text-3xl font-bold text-slate-900">
              {results.length > 0 ? results[results.length - 1].mudPressure.toFixed(0) : 0} psi
            </p>
          </div>
          <div className="flex-1 text-center">
            {results.every((r) => r.isSafe) ? (
              <div className="flex items-center justify-center gap-2 text-green-600 bg-green-100 rounded-lg px-4 py-3">
                <CheckCircle className="w-5 h-5" />
                <span className="font-semibold">Safe</span>
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2 text-red-600 bg-red-100 rounded-lg px-4 py-3">
                <AlertTriangle className="w-5 h-5" />
                <span className="font-semibold">Unsafe</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {results.length === 0 ? (
        <div className="text-center p-8 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-slate-600">Complete previous steps to view stability analysis.</p>
        </div>
      ) : (
        <>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
              <h4 className="font-medium text-slate-900">Mud Weight Window</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Formation</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">TVD (ft)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Breakout (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Breakdown (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Safe Window (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Mud P (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {results.map((r, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{r.formation}</td>
                      <td className="px-4 py-3">{r.tvd.toLocaleString()}</td>
                      <td className="px-4 py-3 text-amber-600 font-medium">{r.breakout.toFixed(0)}</td>
                      <td className="px-4 py-3 text-red-600 font-medium">{r.breakdown.toFixed(0)}</td>
                      <td className="px-4 py-3 font-medium">{r.safeWindow.toFixed(0)}</td>
                      <td className="px-4 py-3 font-medium">{r.mudPressure.toFixed(0)}</td>
                      <td className="px-4 py-3">
                        {r.isSafe ? (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">Safe</span>
                        ) : (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">Unsafe</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <span className="text-sm text-amber-700">Min Safe Mud Weight</span>
              </div>
              <p className="text-xl font-bold text-amber-900">
                {Math.min(...results.map((r) => mudWeightToPpg(r.breakout, r.tvd))).toFixed(1)} ppg
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-red-700">Max Safe Mud Weight</span>
              </div>
              <p className="text-xl font-bold text-red-900">
                {Math.min(...results.map((r) => mudWeightToPpg(r.breakdown, r.tvd))).toFixed(1)} ppg
              </p>
            </div>
            <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
              <div className="flex items-center gap-2 mb-2">
                <CircleDot className="w-4 h-4 text-emerald-500" />
                <span className="text-sm text-emerald-700">Recommended Mud Window</span>
              </div>
              <p className="text-xl font-bold text-emerald-900">
                {Math.min(...results.map((r) => mudWeightToPpg(r.breakout, r.tvd))).toFixed(1)} - {Math.min(...results.map((r) => mudWeightToPpg(r.breakdown, r.tvd))).toFixed(1)} ppg
              </p>
            </div>
          </div>
        </>
      )}
    </form>
  );
}
