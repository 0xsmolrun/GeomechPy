import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAppStore } from '../lib/store';
import {
  CircleDot,
  MapPin,
  Building2,
  ArrowUpDown,
  Plus,
  Play,
  Trash2,
  Loader2,
  ChevronRight,
  Layers,
} from 'lucide-react';
import type { Database } from '../lib/supabase';
type Formation = Database['public']['Tables']['formations']['Row'];

export function WellDetailPage() {
  const { wellId } = useParams();
  const navigate = useNavigate();
  const { currentWell, setCurrentWell, formations, setFormations } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [showFormationModal, setShowFormationModal] = useState(false);

  useEffect(() => {
    async function fetchWell() {
      if (!wellId) return;
      setLoading(true);
      try {
        const { data: well, error: wellError } = await supabase
          .from('wells')
          .select('*')
          .eq('id', wellId)
          .maybeSingle();

        if (wellError) throw wellError;
        if (!well) {
          navigate('/wells');
          return;
        }

        setCurrentWell(well);

        const { data: formationsData, error: formationsError } = await supabase
          .from('formations')
          .select('*')
          .eq('well_id', wellId)
          .order('top_depth_tvd', { ascending: true });

        if (formationsError) throw formationsError;
        setFormations(formationsData || []);
      } catch (err) {
        console.error('Error fetching well:', err);
        navigate('/wells');
      } finally {
        setLoading(false);
      }
    }

    fetchWell();
  }, [wellId, navigate, setCurrentWell, setFormations]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!currentWell) {
    return null;
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-600">
        <Link to="/wells" className="hover:text-primary-600">Wells</Link>
        <ChevronRight className="w-4 h-4" />
        <span className="text-slate-900 font-medium">{currentWell.name}</span>
      </div>

      {/* Header */}
      <div className="card">
        <div className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary-100 to-cyan-100 flex items-center justify-center">
                <CircleDot className="w-8 h-8 text-primary-600" />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold text-slate-900">{currentWell.name}</h1>
                  <StatusBadge status={currentWell.status} />
                </div>
                <div className="flex items-center gap-4 mt-2 text-slate-600">
                  {currentWell.location && (
                    <div className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      {currentWell.location}
                    </div>
                  )}
                  {currentWell.operator && (
                    <div className="flex items-center gap-1">
                      <Building2 className="w-4 h-4" />
                      {currentWell.operator}
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <ArrowUpDown className="w-4 h-4" />
                    TVD: {currentWell.tvd_reference.toLocaleString()} ft
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link to={`/wells/${wellId}/workflow`} className="btn-primary">
                <Play className="w-4 h-4" />
                Start Workflow
              </Link>
            </div>
          </div>

          {/* Well Info Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-200">
            <InfoItem label="Well Type" value={currentWell.offshore ? 'Offshore' : 'Onshore'} />
            <InfoItem label="Reference TVD" value={`${currentWell.tvd_reference.toLocaleString()} ft`} />
            <InfoItem label="Air Gap" value={`${currentWell.air_gap} ft`} />
            {currentWell.offshore && (
              <InfoItem label="Water Depth" value={`${currentWell.water_depth} ft`} />
            )}
          </div>
        </div>
      </div>

      {/* Formations */}
      <div className="card">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Formations</h2>
          <button onClick={() => setShowFormationModal(true)} className="btn-secondary">
            <Plus className="w-4 h-4" />
            Add Formation
          </button>
        </div>

        {formations.length === 0 ? (
          <div className="text-center p-12">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <Layers className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 mb-2">No formations</h3>
            <p className="text-slate-600 mb-4">Add geological formations to begin analysis</p>
            <button onClick={() => setShowFormationModal(true)} className="btn-primary">
              <Plus className="w-4 h-4" />
              Add Formation
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {formations.map((formation) => (
              <FormationRow key={formation.id} formation={formation} />
            ))}
          </div>
        )}
      </div>

      {/* Formation Modal */}
      {showFormationModal && (
        <FormationModal
          wellId={wellId!}
          onClose={() => setShowFormationModal(false)}
          onSuccess={(formation) => {
            setFormations([...formations, formation]);
            setShowFormationModal(false);
          }}
        />
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    planning: { label: 'Planning', className: 'status-planning' },
    drilling: { label: 'Drilling', className: 'status-drilling' },
    completed: { label: 'Completed', className: 'status-completed' },
  };
  const { label, className } = config[status] || config.planning;
  return <span className={className}>{label}</span>;
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="font-medium text-slate-900">{value}</p>
    </div>
  );
}

function FormationRow({ formation }: { formation: Formation }) {
  const thickness = formation.base_depth_tvd - formation.top_depth_tvd;

  return (
    <div className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
          <Layers className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <h3 className="font-medium text-slate-900">{formation.name}</h3>
          <p className="text-sm text-slate-500">
            {formation.top_depth_tvd.toLocaleString()} - {formation.base_depth_tvd.toLocaleString()} ft ({thickness.toLocaleString()} ft)
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4 text-sm text-slate-600">
        {formation.lithology && (
          <span className="px-2 py-1 bg-slate-100 rounded">{formation.lithology}</span>
        )}
        <span>Ï�: {formation.density} kg/mÂ³</span>
        <span>Ï†: {(formation.porosity * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}

interface FormationModalProps {
  wellId: string;
  onClose: () => void;
  onSuccess: (formation: Formation) => void;
}

function FormationModal({ wellId, onClose, onSuccess }: FormationModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    top_depth_tvd: 0,
    base_depth_tvd: 1000,
    lithology: '',
    density: 2500,
    porosity: 0.20,
    p_wave_velocity: 3000,
    s_wave_velocity: 2000,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { data, error: insertError } = await supabase
        .from('formations')
        .insert({
          ...formData,
          well_id: wellId,
        })
        .select()
        .single();

      if (insertError) throw insertError;
      onSuccess(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create formation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900">Add Formation</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg">
            <Trash2 className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="label">Formation Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              required
              placeholder="e.g., Upper Sandstone"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Top Depth TVD (ft) *</label>
              <input
                type="number"
                value={formData.top_depth_tvd}
                onChange={(e) => setFormData({ ...formData, top_depth_tvd: parseFloat(e.target.value) || 0 })}
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Base Depth TVD (ft) *</label>
              <input
                type="number"
                value={formData.base_depth_tvd}
                onChange={(e) => setFormData({ ...formData, base_depth_tvd: parseFloat(e.target.value) || 0 })}
                className="input"
                required
              />
            </div>
          </div>

          <div>
            <label className="label">Lithology</label>
            <select
              value={formData.lithology}
              onChange={(e) => setFormData({ ...formData, lithology: e.target.value })}
              className="input"
            >
              <option value="">Select lithology</option>
              <option value="sandstone">Sandstone</option>
              <option value="shale">Shale</option>
              <option value="limestone">Limestone</option>
              <option value="dolomite">Dolomite</option>
              <option value="siltstone">Siltstone</option>
              <option value="carbonate">Carbonate</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Density (kg/mÂ³)</label>
              <input
                type="number"
                value={formData.density}
                onChange={(e) => setFormData({ ...formData, density: parseFloat(e.target.value) || 0 })}
                className="input"
              />
            </div>
            <div>
              <label className="label">Porosity (fraction)</label>
              <input
                type="number"
                value={formData.porosity}
                onChange={(e) => setFormData({ ...formData, porosity: parseFloat(e.target.value) || 0 })}
                className="input"
                step="0.01"
                min="0"
                max="1"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">P-Wave Velocity (m/s)</label>
              <input
                type="number"
                value={formData.p_wave_velocity}
                onChange={(e) => setFormData({ ...formData, p_wave_velocity: parseFloat(e.target.value) || 0 })}
                className="input"
              />
            </div>
            <div>
              <label className="label">S-Wave Velocity (m/s)</label>
              <input
                type="number"
                value={formData.s_wave_velocity}
                onChange={(e) => setFormData({ ...formData, s_wave_velocity: parseFloat(e.target.value) || 0 })}
                className="input"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Add Formation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
