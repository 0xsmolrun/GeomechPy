import { useState } from 'react';
import { useAppStore } from '../../lib/store';
import {
  calculateElasticFromVelocity,
  dyn2staYmeBradford,
  dyn2staYmeNajib,
  dyn2staYmeMorales,
} from '../../calculations';
import { Zap, ArrowRightLeft, Info } from 'lucide-react';

interface ElasticPropertiesStepProps {
  onNext: (data: Record<string, unknown>) => void;
}

export function ElasticPropertiesStep({ onNext }: ElasticPropertiesStepProps) {
  const { formations } = useAppStore();
  const [correlation, setCorrelation] = useState<'bradford' | 'najib' | 'morales'>('bradford');

  const results = formations.map((f) => {
    const dynamic = calculateElasticFromVelocity(f.p_wave_velocity, f.s_wave_velocity, f.density);

    let ymeSta: number;
    switch (correlation) {
      case 'najib':
        ymeSta = dyn2staYmeNajib(dynamic.youngsModulus / 1e9);
        break;
      case 'morales':
        ymeSta = dyn2staYmeMorales(dynamic.youngsModulus / 1e9, f.porosity);
        break;
      default:
        ymeSta = dyn2staYmeBradford(dynamic.youngsModulus / 1e9);
    }

    const prSta = dynamic.poissonsRatio;

    return {
      formation: f.name,
      tvd: f.base_depth_tvd,
      density: f.density,
      porosity: f.porosity,
      vp: f.p_wave_velocity,
      vs: f.s_wave_velocity,
      dynamic,
      ymeDyn: dynamic.youngsModulus / 1e9,
      ymeSta,
      prSta,
    };
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({
      correlation,
      results: results.map((r) => ({
        formation: r.formation,
        tvd: r.tvd,
        youngs_modulus_dynamic: r.ymeDyn,
        youngs_modulus_static: r.ymeSta,
        poisson_ratio_dynamic: r.dynamic.poissonsRatio,
        poisson_ratio_static: r.prSta,
      })),
    });
  };

  return (
    <form id="workflow-form" onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700">
          <p className="font-medium mb-1">Dynamic to Static Elastic Properties</p>
          <p>Convert P and S wave velocities to dynamic elastic properties, then apply empirical correlations to derive static properties.</p>
        </div>
      </div>

      {/* Correlation Selection */}
      <div>
        <label className="label mb-3">Young's Modulus Correlation</label>
        <div className="flex gap-3">
          {[
            { id: 'bradford', label: 'Bradford', desc: 'Turbiditic Sandstones' },
            { id: 'najib', label: 'Najib', desc: 'Carbonates' },
            { id: 'morales', label: 'Morales', desc: 'Sandstones (porosity-based)' },
          ].map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => setCorrelation(opt.id as typeof correlation)}
              className={`flex-1 p-3 rounded-lg border-2 transition-colors ${
                correlation === opt.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <p className="font-medium text-slate-900">{opt.label}</p>
              <p className="text-xs text-slate-500 mt-1">{opt.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {formations.length === 0 ? (
        <div className="text-center p-8 bg-slate-50 rounded-lg border border-slate-200">
          <p className="text-slate-600">No formations defined. Please add formations to the well first.</p>
        </div>
      ) : (
        <>
          {/* Results Table */}
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
              <h4 className="font-medium text-slate-900">Elastic Properties by Formation</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Formation</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Vp (m/s)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Vs (m/s)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Ï� (kg/mÂ³)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">YME_dyn (GPa)</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-slate-500"><ArrowRightLeft className="w-4 h-4 mx-auto" /></th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">YME_sta (Mpsi)</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">PR_dyn</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">PR_sta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {results.map((r, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{r.formation}</td>
                      <td className="px-4 py-3">{r.vp}</td>
                      <td className="px-4 py-3">{r.vs}</td>
                      <td className="px-4 py-3">{r.density}</td>
                      <td className="px-4 py-3">{r.ymeDyn.toFixed(2)}</td>
                      <td className="px-4 py-3 text-center text-primary-500">â†’</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{r.ymeSta.toFixed(3)}</td>
                      <td className="px-4 py-3">{r.dynamic.poissonsRatio.toFixed(3)}</td>
                      <td className="px-4 py-3">{r.prSta.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Other Properties */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-500">Avg K_dyn</p>
              <p className="text-lg font-bold text-slate-900">
                {(results.reduce((s, r) => s + r.dynamic.bulkModulus, 0) / results.length / 1e9).toFixed(2)} GPa
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-500">Avg G_dyn</p>
              <p className="text-lg font-bold text-slate-900">
                {(results.reduce((s, r) => s + r.dynamic.shearModulus, 0) / results.length / 1e9).toFixed(2)} GPa
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-500">Avg Î¼_dyn</p>
              <p className="text-lg font-bold text-slate-900">
                {(results.reduce((s, r) => s + r.dynamic.lameParameter, 0) / results.length / 1e9).toFixed(2)} GPa
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-500">Avg YME_sta</p>
              <p className="text-lg font-bold text-slate-900">
                {(results.reduce((s, r) => s + r.ymeSta, 0) / results.length).toFixed(3)} Mpsi
              </p>
            </div>
          </div>

          {/* Correlation Comparison */}
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <h4 className="text-sm font-medium text-slate-700 mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Correlation Comparison
            </h4>
            <div className="grid grid-cols-3 gap-3">
              {results.slice(0, 3).map((r, i) => (
                <div key={i} className="bg-white rounded p-2 border border-slate-200">
                  <p className="text-xs text-slate-500 mb-1">{r.formation}</p>
                  <div className="space-y-1 text-xs">
                    <p className="flex justify-between">
                      <span className="text-slate-500">Bradford:</span>
                      <span className="font-medium">{dyn2staYmeBradford(r.ymeDyn).toFixed(3)} Mpsi</span>
                    </p>
                    <p className="flex justify-between">
                      <span className="text-slate-500">Najib:</span>
                      <span className="font-medium">{dyn2staYmeNajib(r.ymeDyn).toFixed(3)} Mpsi</span>
                    </p>
                    <p className="flex justify-between">
                      <span className="text-slate-500">Morales:</span>
                      <span className="font-medium">{dyn2staYmeMorales(r.ymeDyn, r.porosity).toFixed(3)} Mpsi</span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </form>
  );
}
