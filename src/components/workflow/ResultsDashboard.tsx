import { useAppStore } from '../../lib/store';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Download, FileText, CheckCircle, AlertTriangle } from 'lucide-react';

export function ResultsDashboard() {
  const { workflowSession } = useAppStore();

  const porePressureData = (workflowSession?.step_data?.['1'] as { results?: Array<{ tvd: number; porePressure: number; overburdenStress: number }> })?.results || [];
  const horizontalStressesData = (workflowSession?.step_data?.['4'] as { results?: Array<{ formation: string; tvd: number; shmin: number; shmax: number; stressRegime: string }> })?.results || [];
  const wellboreStabilityData = (workflowSession?.step_data?.['5'] as { results?: Array<{ formation: string; tvd: number; breakout_pressure: number; breakdown_pressure: number; mud_pressure: number; is_safe: boolean }> })?.results || [];

  const chartData = horizontalStressesData.map((h, i) => {
    const ws = wellboreStabilityData[i];
    const pp = porePressureData.find((p) => p.tvd === h.tvd);
    return {
      name: h.formation,
      tvd: h.tvd,
      porePressure: pp?.porePressure || 0,
      overburden: pp?.overburdenStress || 0,
      shmin: h.shmin,
      shmax: h.shmax,
      breakout: ws?.breakout_pressure || 0,
      breakdown: ws?.breakdown_pressure || 0,
    };
  }).reverse();

  const allStepsCompleted = workflowSession?.current_step === 6;
  console.log('All steps completed:', allStepsCompleted);

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-primary-500 to-cyan-500 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Analysis Complete</h2>
            <p className="opacity-90">Your wellbore stability workflow has been completed successfully.</p>
          </div>
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
            <CheckCircle className="w-8 h-8" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pressure vs Depth */}
        <div className="card p-4">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Pressure vs Depth</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="tvd" tick={{ fontSize: 12 }} label={{ value: 'TVD (ft)', position: 'bottom', offset: -5, fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} label={{ value: 'Pressure (psi)', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                  labelStyle={{ fontWeight: 'bold' }}
                />
                <Line type="monotone" dataKey="porePressure" stroke="#3b82f6" strokeWidth={2} name="Pore Pressure" />
                <Line type="monotone" dataKey="overburden" stroke="#f59e0b" strokeWidth={2} name="Overburden" />
                <Line type="monotone" dataKey="shmin" stroke="#10b981" strokeWidth={2} name="Shmin" />
                <Line type="monotone" dataKey="shmax" stroke="#8b5cf6" strokeWidth={2} name="Shmax" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-4 mt-4 text-xs">
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-blue-500 rounded" /> Pore Pressure</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-amber-500 rounded" /> Overburden</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-emerald-500 rounded" /> Shmin</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-purple-500 rounded" /> Shmax</div>
          </div>
        </div>

        {/* Mud Weight Window */}
        <div className="card p-4">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Mud Weight Window</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="tvd" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                />
                <Area type="monotone" dataKey="breakdown" stackId="1" stroke="#ef4444" fill="#fee2e2" name="Breakdown" />
                <Area type="monotone" dataKey="breakout" stackId="2" stroke="#f59e0b" fill="#fef3c7" name="Breakout" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-4 text-xs">
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-red-200 rounded" /> Breakdown Limit</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-amber-200 rounded" /> Breakout Limit</div>
          </div>
        </div>
      </div>

      {/* Summary Table */}
      <div className="card overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">Final Results Summary</h3>
          <button className="btn-secondary">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Formation</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">TVD (ft)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Pp (psi)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Sv (psi)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Shmin</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Shmax</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Breakout</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Breakdown</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500">Safe Window</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {horizontalStressesData.map((h, i) => {
                const ws = wellboreStabilityData[i];
                const pp = porePressureData.find((p) => p.tvd === h.tvd);
                return (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{h.formation}</td>
                    <td className="px-4 py-3">{h.tvd.toLocaleString()}</td>
                    <td className="px-4 py-3">{pp?.porePressure.toFixed(0) || '-'}</td>
                    <td className="px-4 py-3">{pp?.overburdenStress.toFixed(0) || '-'}</td>
                    <td className="px-4 py-3">{h.shmin.toFixed(0)}</td>
                    <td className="px-4 py-3">{h.shmax.toFixed(0)}</td>
                    <td className="px-4 py-3 text-amber-600">{ws?.breakout_pressure.toFixed(0) || '-'}</td>
                    <td className="px-4 py-3 text-red-600">{ws?.breakdown_pressure.toFixed(0) || '-'}</td>
                    <td className="px-4 py-3">
                      {ws ? (
                        ws.is_safe ? (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 flex items-center gap-1 w-fit">
                            <CheckCircle className="w-3 h-3" />
                            {ws.breakdown_pressure - ws.breakout_pressure} psi
                          </span>
                        ) : (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 flex items-center gap-1 w-fit">
                            <AlertTriangle className="w-3 h-3" />
                            Unsafe
                          </span>
                        )
                      ) : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Export Options */}
      <div className="card p-4">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Export Options</h3>
        <div className="flex gap-4">
          <button className="btn-secondary flex-1">
            <FileText className="w-4 h-4" />
            Export as CSV
          </button>
          <button className="btn-secondary flex-1">
            <Download className="w-4 h-4" />
            Export as PDF Report
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-4">
          Export functionality coming soon. Your workflow data has been saved automatically.
        </p>
      </div>
    </div>
  );
}
