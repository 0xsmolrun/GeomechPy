import { useState } from 'react';
import { useAppStore } from '../../lib/store';
import { calculateHorizontalStresses } from '../../calculations';
import { Target, Activity, Info } from 'lucide-react';

interface HorizontalStressesStepProps {
  onNext: (data: Record<string, unknown>) => void;
}

export function HorizontalStressesStep({ onNext }: HorizontalStressesStepProps) {
  const { formations, workflowSession } = useAppStore();
  const [biotCoefficient, setBiotCoefficient] = useState(1.0);
  const [tectonicStrainX, setTectonicStrainX] = useState(0.0001);
  const [tectonicStrainY, setTectonicStrainY] = useState(0.009);

  const porePressureData = workflowSession?.step_data?.['1'] as { results: Array<{ tvd: number; porePressure: number; overburdenStress: number }> } | undefined;
  const elasticData = workflowSession?.step_data?.['2'] as { results: Array<{ formation: string; ymeSta: number; prSta: number }> } | undefined;
  const workflowSessionData = workflowSession?.step_data;
  const rockStrengthData = workflowSessionData?.['3'] as { results: Array<{ formation: string; frictionAngle: number }> } | undefined;
  void rockStrengthData; // Used for reference in future workflow steps

  const results = formations.map((f, i) => {
    const ppData = porePressureData?.results?.find((r) => r.tvd === f.base_depth_tvd);
    const elData = elasticData?.results?.[i];
    // Rock strength data used via index below

    const porePressure = ppData?.porePressure || 5000;
    const overburdenStress = ppData?.overburdenStress || 10000;
    const ymeSta = elData?.ymeSta || 2;
    const prSta = elData?.prSta || 0.25;

    const horizontalStresses = calculateHorizontalStresses(
      overburdenStress,
      porePressure,
      prSta,
      ymeSta,
      biotCoefficient,
      tectonicStrainX * 1000,
      tectonicStrainY * 1000
    );

    return {
      formation: f.name,
      tvd: f.base_depth_tvd,
      porePressure,
      overburdenStress,
      shmin: horizontalStresses.shmin,
      shmax: horizontalStresses.shmax,
      qFactor: horizontalStresses.qFactor,
      stressRegime: horizontalStresses.stressRegime,
    };
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({
      biot_coefficient: biotCoefficient,
      tectonic_strain_x: tectonicStrainX,
      tectonic_strain_y: tectonicStrainY,
      results: results.map((r) => ({
        formation: r.formation,
        tvd: r.tvd,
        shmin: r.shmin,
        shmax: r.shmax,
        q_factor: r.qFactor,
        stress_regime: r.stressRegime,
      })),
    });
  };

  return (
    <form id="workflow-form" onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700">
          <p className="font-medium mb-1">Horizontal Stresses</p>
          <p>Calculate Shmin and Shmax using poroelastic equations with tectonic strains (Thiercelin & Plumb, 1994).</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="label">Biot Coefficient</label>
          <input
            type="number"
            value={biotCoefficient}
            onChange={(e) => setBiotCoefficient(parseFloat(e.target.value) || 1)}
            className="input"
            step="0.05"
            min="0"
            max="1"
          />
        </div>
        <div>
          <label className="label">Tectonic Strain EX</label>
          <input
            type="number"
            value={tectonicStrainX}
            onChange={(e) => setTectonicStrainX(parseFloat(e.target.value) || 0.0001)}
            className="input"
            step="0.0001"
          />
        </div>
        <div>
          <label className="label">Tectonic Strain EY</label>
          <input
            type="number"
            value={tectonicStrainY}
            onChange={(e) => setTectonicStrainY(parseFloat(e.target.value) || 0.009)}
            className="input"
            step="0.0001"
          />
        </div>
      </div>

      {results.length === 0 ? (
        <div className="text-center p-8 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-slate-600">No data available. Complete previous steps first.</p>
        </div>
      ) : (
        <>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
              <h4 className="font-medium text-slate-900">Horizontal Stresses</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Formation</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">TVD (ft)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Pp (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Sv (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Shmin (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Shmax (psi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Q Factor</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Regime</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {results.map((r, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{r.formation}</td>
                      <td className="px-4 py-3">{r.tvd.toLocaleString()}</td>
                      <td className="px-4 py-3">{r.porePressure.toFixed(0)}</td>
                      <td className="px-4 py-3">{r.overburdenStress.toFixed(0)}</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{r.shmin.toFixed(0)}</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{r.shmax.toFixed(0)}</td>
                      <td className="px-4 py-3">{r.qFactor.toFixed(2)}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          r.stressRegime === 'Normal Faulting' ? 'bg-green-100 text-green-800' :
                          r.stressRegime === 'Strike-Slip' ? 'bg-yellow-100 text-yellow-800' :
                          r.stressRegime === 'Reverse Faulting' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {r.stressRegime}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-blue-700">Avg Shmin</span>
              </div>
              <p className="text-xl font-bold text-blue-900">
                {(results.reduce((s, r) => s + r.shmin, 0) / results.length).toFixed(0)} psi
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-green-700">Avg Shmax</span>
              </div>
              <p className="text-xl font-bold text-green-900">
                {(results.reduce((s, r) => s + r.shmax, 0) / results.length).toFixed(0)} psi
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-purple-500" />
                <span className="text-sm text-purple-700">Avg Q Factor</span>
              </div>
              <p className="text-xl font-bold text-purple-900">
                {(results.reduce((s, r) => s + r.qFactor, 0) / results.length).toFixed(2)}
              </p>
            </div>
            <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-amber-700">Shmax/Shmin Ratio</span>
              </div>
              <p className="text-xl font-bold text-amber-900">
                {(results.reduce((s, r) => s + r.shmax / r.shmin, 0) / results.length).toFixed(2)}
              </p>
            </div>
          </div>
        </>
      )}
    </form>
  );
}
