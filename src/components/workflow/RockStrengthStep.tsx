import { useState } from 'react';
import { useAppStore } from '../../lib/store';
import { convertYmeStaToUcsPlumb, convertUcsToTstr, calculateFrictionAngle } from '../../calculations';
import { Wrench, Hammer, Info } from 'lucide-react';

interface RockStrengthStepProps {
  onNext: (data: Record<string, unknown>) => void;
}

export function RockStrengthStep({ onNext }: RockStrengthStepProps) {
  const { formations, workflowSession } = useAppStore();
  const [tstrMultiplier, setTstrMultiplier] = useState(0.15);
  const [dtco, setDtco] = useState(80);

  const elasticResults = workflowSession?.step_data?.['2'] as { results: Array<{ formation: string; ymeSta: number; prSta: number }> } | undefined;

  const results = (elasticResults?.results || []).map((r, i) => {
    const f = formations[i];
    const ymeSta = r.ymeSta || 2;
    const ucs = convertYmeStaToUcsPlumb(ymeSta);
    const tstr = convertUcsToTstr(ucs, tstrMultiplier);
    const frictionAngle = calculateFrictionAngle(dtco);

    return {
      formation: r.formation || f?.name || 'Unknown',
      tvd: f?.base_depth_tvd || 0,
      ymeSta,
      ucs,
      tstr,
      frictionAngle,
    };
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({
      tstr_multiplier: tstrMultiplier,
      dtco,
      results: results.map((r) => ({
        formation: r.formation,
        tvd: r.tvd,
        ucs: r.ucs,
        tstr: r.tstr,
        friction_angle: r.frictionAngle,
      })),
    });
  };

  return (
    <form id="workflow-form" onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700">
          <p className="font-medium mb-1">Rock Strength Properties</p>
          <p>Calculate UCS from static Young's modulus using Plumb correlation, and friction angle from compressional slowness using Lal correlation.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Tensile Strength Multiplier</label>
          <input
            type="number"
            value={tstrMultiplier}
            onChange={(e) => setTstrMultiplier(parseFloat(e.target.value) || 0.15)}
            className="input"
            step="0.01"
            min="0.05"
            max="0.3"
          />
          <p className="text-xs text-slate-500 mt-1">TSTR = multiplier Ã— UCS (default: 0.15)</p>
        </div>
        <div>
          <label className="label">Compressional Slowness (Âµs/ft)</label>
          <input
            type="number"
            value={dtco}
            onChange={(e) => setDtco(parseFloat(e.target.value) || 80)}
            className="input"
            step="1"
          />
          <p className="text-xs text-slate-500 mt-1">Used for Lal friction angle correlation</p>
        </div>
      </div>

      {results.length === 0 ? (
        <div className="text-center p-8 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-slate-600">No elastic properties data. Complete Step 2 first.</p>
        </div>
      ) : (
        <>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
              <h4 className="font-medium text-slate-900">Rock Strength Properties</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Formation</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">TVD (ft)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">YME_sta (Mpsi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">UCS (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">TSTR (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">FANG (deg)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {results.map((r, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{r.formation}</td>
                      <td className="px-4 py-3">{r.tvd.toLocaleString()}</td>
                      <td className="px-4 py-3">{r.ymeSta.toFixed(3)}</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{r.ucs.toFixed(0)}</td>
                      <td className="px-4 py-3">{r.tstr.toFixed(1)}</td>
                      <td className="px-4 py-3">{r.frictionAngle.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <Hammer className="w-4 h-4 text-red-500" />
                <span className="text-sm text-red-700">Avg UCS</span>
              </div>
              <p className="text-xl font-bold text-red-900">
                {(results.reduce((s, r) => s + r.ucs, 0) / results.length).toFixed(0)} psi
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Wrench className="w-4 h-4 text-purple-500" />
                <span className="text-sm text-purple-700">Avg Tensile Strength</span>
              </div>
              <p className="text-xl font-bold text-purple-900">
                {(results.reduce((s, r) => s + r.tstr, 0) / results.length).toFixed(0)} psi
              </p>
            </div>
            <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-amber-700">Avg Friction Angle</span>
              </div>
              <p className="text-xl font-bold text-amber-900">
                {results[0]?.frictionAngle.toFixed(1)} deg
              </p>
            </div>
          </div>
        </>
      )}
    </form>
  );
}
