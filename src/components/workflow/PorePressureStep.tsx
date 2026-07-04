import { useState } from 'react';
import { useAppStore } from '../../lib/store';
import {
  calculatePorePressureOnshore,
  calculatePorePressureOffshore,
  calculateOverburdenStressOnshore,
  calculateOverburdenStressOffshore,
} from '../../calculations';
import { Layers, Mountain, Waves, Info } from 'lucide-react';

interface PorePressureStepProps {
  onNext: (data: Record<string, unknown>) => void;
}

export function PorePressureStep({ onNext }: PorePressureStepProps) {
  const { currentWell } = useAppStore();
  const [formData, setFormData] = useState({
    pore_pressure_gradient: 0.47,
    lithostatic_gradient: 1.05,
    sea_water_gradient: 0.47,
    depth_points: '5000,7500,10000,12500,15000',
  });

  if (!currentWell) return null;

  const depths = formData.depth_points.split(',').map((d) => parseFloat(d.trim()) || 0).filter((d) => d > 0);

  const results = depths.map((tvd) => {
    const porePressure = currentWell.offshore
      ? calculatePorePressureOffshore(tvd, formData.pore_pressure_gradient, currentWell.air_gap, currentWell.water_depth, formData.sea_water_gradient)
      : calculatePorePressureOnshore(tvd, formData.pore_pressure_gradient, currentWell.air_gap);

    const overburdenStress = currentWell.offshore
      ? calculateOverburdenStressOffshore(tvd, formData.lithostatic_gradient, currentWell.air_gap, currentWell.water_depth, formData.sea_water_gradient)
      : calculateOverburdenStressOnshore(tvd, formData.lithostatic_gradient, currentWell.air_gap);

    const effectiveStress = overburdenStress - porePressure;

    return { tvd, porePressure, overburdenStress, effectiveStress };
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({
      pore_pressure_gradient: formData.pore_pressure_gradient,
      lithostatic_gradient: formData.lithostatic_gradient,
      sea_water_gradient: formData.sea_water_gradient,
      depth_points: depths,
      results,
    });
  };

  return (
    <form id="workflow-form" onSubmit={handleSubmit} className="space-y-6">
      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-700">
          <p className="font-medium mb-1">Pore Pressure Calculation</p>
          <p>Calculate pore pressure and overburden stress based on TVD. Reference: Zhang (2019) Applied Petroleum Geomechanics, Chapter 6.</p>
        </div>
      </div>

      {/* Input Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="label">Pore Pressure Gradient (psi/ft)</label>
          <input
            type="number"
            value={formData.pore_pressure_gradient}
            onChange={(e) => setFormData({ ...formData, pore_pressure_gradient: parseFloat(e.target.value) || 0 })}
            className="input"
            step="0.01"
          />
        </div>
        <div>
          <label className="label">Lithostatic Gradient (psi/ft)</label>
          <input
            type="number"
            value={formData.lithostatic_gradient}
            onChange={(e) => setFormData({ ...formData, lithostatic_gradient: parseFloat(e.target.value) || 0 })}
            className="input"
            step="0.01"
          />
        </div>
        {currentWell.offshore && (
          <div>
            <label className="label">Sea Water Gradient (psi/ft)</label>
            <input
              type="number"
              value={formData.sea_water_gradient}
              onChange={(e) => setFormData({ ...formData, sea_water_gradient: parseFloat(e.target.value) || 0 })}
              className="input"
              step="0.01"
            />
          </div>
        )}
        <div>
          <label className="label">Depth Points (TVD ft)</label>
          <input
            type="text"
            value={formData.depth_points}
            onChange={(e) => setFormData({ ...formData, depth_points: e.target.value })}
            className="input"
            placeholder="5000,7500,10000..."
          />
          <p className="text-xs text-slate-500 mt-1">Comma-separated depth values</p>
        </div>
      </div>

      {/* Well Info */}
      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
        <h4 className="text-sm font-medium text-slate-700 mb-2">Well Parameters</h4>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-slate-500">Type:</span>
            <span className="ml-2 font-medium">{currentWell.offshore ? 'Offshore' : 'Onshore'}</span>
          </div>
          <div>
            <span className="text-slate-500">Air Gap:</span>
            <span className="ml-2 font-medium">{currentWell.air_gap} ft</span>
          </div>
          {currentWell.offshore && (
            <div>
              <span className="text-slate-500">Water Depth:</span>
              <span className="ml-2 font-medium">{currentWell.water_depth} ft</span>
            </div>
          )}
        </div>
      </div>

      {/* Results Table */}
      <div className="border border-slate-200 rounded-lg overflow-hidden">
        <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
          <h4 className="font-medium text-slate-900">Calculated Results</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">TVD (ft)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Pore Pressure (psi)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Overburden (psi)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Effective Stress (psi)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {results.map((r, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm text-slate-900">{r.tvd.toLocaleString()}</td>
                  <td className="px-4 py-3 text-sm text-slate-900">{r.porePressure.toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-slate-900">{r.overburdenStress.toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-slate-900">{r.effectiveStress.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <Waves className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-blue-700">Avg Pore Pressure</span>
          </div>
          <p className="text-xl font-bold text-blue-900">
            {(results.reduce((sum, r) => sum + r.porePressure, 0) / results.length).toFixed(0)} psi
          </p>
        </div>
        <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
          <div className="flex items-center gap-2 mb-2">
            <Mountain className="w-4 h-4 text-amber-500" />
            <span className="text-sm text-amber-700">Avg Overburden</span>
          </div>
          <p className="text-xl font-bold text-amber-900">
            {(results.reduce((sum, r) => sum + r.overburdenStress, 0) / results.length).toFixed(0)} psi
          </p>
        </div>
        <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
          <div className="flex items-center gap-2 mb-2">
            <Layers className="w-4 h-4 text-emerald-500" />
            <span className="text-sm text-emerald-700">Avg Effective Stress</span>
          </div>
          <p className="text-xl font-bold text-emerald-900">
            {(results.reduce((sum, r) => sum + r.effectiveStress, 0) / results.length).toFixed(0)} psi
          </p>
        </div>
      </div>
    </form>
  );
}
