import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAppStore } from '../lib/store';
import { CircleDot, Plus, Search, MapPin, Building2, Loader2, X, ArrowRight, MoreVertical, Trash2, FileEdit as Edit } from 'lucide-react';
import type { Database } from '../lib/supabase';

type Well = Database['public']['Tables']['wells']['Row'];

export function WellsPage() {
  const { user, wells, setWells, addWell, deleteWell, loading, setLoading } = useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    async function fetchWells() {
      if (!user) return;
      setLoading(true);
      try {
        const { data, error } = await supabase
          .from('wells')
          .select('*')
          .order('updated_at', { ascending: false });

        if (error) throw error;
        setWells(data || []);
      } catch (err) {
        console.error('Error fetching wells:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchWells();
  }, [user, setWells, setLoading]);

  const filteredWells = wells.filter((well) => {
    const matchesSearch = well.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (well.location?.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || well.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Wells</h1>
          <p className="text-slate-600 mt-1">Manage your wellbore stability projects</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          New Well
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10"
            placeholder="Search wells..."
          />
        </div>
        <div className="flex gap-2">
          {['all', 'planning', 'drilling', 'completed'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === status
                  ? 'bg-slate-900 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Wells Grid */}
      {loading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      ) : filteredWells.length === 0 ? (
        <div className="card text-center p-12">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
            <CircleDot className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">No wells found</h3>
          <p className="text-slate-600 mb-4">
            {searchQuery || statusFilter !== 'all'
              ? 'Try adjusting your filters'
              : 'Get started by creating your first well'}
          </p>
          <button onClick={() => setShowCreateModal(true)} className="btn-primary">
            <Plus className="w-4 h-4" />
            Create Well
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWells.map((well) => (
            <WellCard key={well.id} well={well} onDelete={() => deleteWell(well.id)} />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateWellModal onClose={() => setShowCreateModal(false)} onSuccess={(well) => {
          addWell(well);
          setShowCreateModal(false);
        }} />
      )}
    </div>
  );
}

interface WellCardProps {
  well: Well;
  onDelete: () => void;
}

function WellCard({ well, onDelete }: WellCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this well? This action cannot be undone.')) return;
    setDeleting(true);
    try {
      const { error } = await supabase.from('wells').delete().eq('id', well.id);
      if (error) throw error;
      onDelete();
    } catch (err) {
      console.error('Error deleting well:', err);
      alert('Failed to delete well');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="card-hover p-4 group relative">
      <div className="absolute top-4 right-4">
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="p-1 rounded hover:bg-slate-100 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <MoreVertical className="w-4 h-4 text-slate-400" />
        </button>
        {showMenu && (
          <div className="absolute right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-10 min-w-[120px]">
            <Link
              to={`/wells/${well.id}`}
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              <Edit className="w-4 h-4" />
              Edit
            </Link>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 w-full"
            >
              <Trash2 className="w-4 h-4" />
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        )}
      </div>

      <Link to={`/wells/${well.id}`} className="block">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-cyan-100 flex items-center justify-center">
            <CircleDot className="w-6 h-6 text-primary-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-900 truncate">{well.name}</h3>
            <div className="flex items-center gap-1 text-sm text-slate-500 mt-1">
              <MapPin className="w-3 h-3" />
              <span className="truncate">{well.location || 'No location'}</span>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-slate-600">
            <span>TVD: {well.tvd_reference.toLocaleString()} ft</span>
            {well.operator && (
              <div className="flex items-center gap-1">
                <Building2 className="w-3 h-3" />
                {well.operator}
              </div>
            )}
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-colors" />
        </div>
      </Link>
    </div>
  );
}

interface CreateWellModalProps {
  onClose: () => void;
  onSuccess: (well: Well) => void;
}

function CreateWellModal({ onClose, onSuccess }: CreateWellModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    operator: '',
    tvd_reference: 10000,
    water_depth: 0,
    air_gap: 0,
    offshore: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { data, error: insertError } = await supabase
        .from('wells')
        .insert({
          ...formData,
          status: 'planning',
        })
        .select()
        .single();

      if (insertError) throw insertError;
      onSuccess(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create well');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900">Create New Well</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="label">Well Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              required
              placeholder="e.g., Well-001"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="input"
                placeholder="Field name"
              />
            </div>
            <div>
              <label className="label">Operator</label>
              <input
                type="text"
                value={formData.operator}
                onChange={(e) => setFormData({ ...formData, operator: e.target.value })}
                className="input"
                placeholder="Company"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Reference TVD (ft) *</label>
              <input
                type="number"
                value={formData.tvd_reference}
                onChange={(e) => setFormData({ ...formData, tvd_reference: parseFloat(e.target.value) || 0 })}
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Air Gap (ft)</label>
              <input
                type="number"
                value={formData.air_gap}
                onChange={(e) => setFormData({ ...formData, air_gap: parseFloat(e.target.value) || 0 })}
                className="input"
              />
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 border border-slate-200">
            <input
              type="checkbox"
              id="offshore"
              checked={formData.offshore}
              onChange={(e) => setFormData({ ...formData, offshore: e.target.checked })}
              className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="offshore" className="text-sm text-slate-700">
              Offshore well
            </label>
          </div>

          {formData.offshore && (
            <div>
              <label className="label">Water Depth (ft)</label>
              <input
                type="number"
                value={formData.water_depth}
                onChange={(e) => setFormData({ ...formData, water_depth: parseFloat(e.target.value) || 0 })}
                className="input"
              />
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Well'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
