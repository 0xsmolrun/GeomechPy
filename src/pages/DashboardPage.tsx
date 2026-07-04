import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAppStore } from '../lib/store';
import {
  CircleDot,
  Plus,
  Activity,
  TrendingUp,
  CheckCircle,
  ArrowRight,
  Loader2,
} from 'lucide-react';

export function DashboardPage() {
  const { user, wells, setWells, loading, setLoading } = useAppStore();

  useEffect(() => {
    async function fetchWells() {
      if (!user) return;
      setLoading(true);
      try {
        const { data, error } = await supabase
          .from('wells')
          .select('*')
          .order('updated_at', { ascending: false })
          .limit(10);

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

  const stats = {
    totalWells: wells.length,
    planning: wells.filter((w) => w.status === 'planning').length,
    drilling: wells.filter((w) => w.status === 'drilling').length,
    completed: wells.filter((w) => w.status === 'completed').length,
  };

  return (
    <div className="p-6 lg:p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600 mt-1">Manage your wellbore stability workflows</p>
        </div>
        <Link to="/wells" className="btn-primary">
          <Plus className="w-4 h-4" />
          New Well
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Wells"
          value={stats.totalWells}
          icon={<CircleDot className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          title="Planning"
          value={stats.planning}
          icon={<Activity className="w-5 h-5" />}
          color="amber"
        />
        <StatCard
          title="Drilling"
          value={stats.drilling}
          icon={<TrendingUp className="w-5 h-5" />}
          color="emerald"
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          icon={<CheckCircle className="w-5 h-5" />}
          color="slate"
        />
      </div>

      {/* Recent Wells */}
      <div className="card">
        <div className="p-4 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Recent Wells</h2>
            <Link to="/wells" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              View all
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
          </div>
        ) : wells.length === 0 ? (
          <div className="text-center p-12">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <CircleDot className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 mb-2">No wells yet</h3>
            <p className="text-slate-600 mb-4">Get started by creating your first well</p>
            <Link to="/wells" className="btn-primary">
              <Plus className="w-4 h-4" />
              Create Well
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {wells.map((well) => (
              <Link
                key={well.id}
                to={`/wells/${well.id}`}
                className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                    <CircleDot className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-slate-900 group-hover:text-primary-600 transition-colors">
                      {well.name}
                    </h3>
                    <p className="text-sm text-slate-500">
                      {well.location || 'No location'} | TVD: {well.tvd_reference.toLocaleString()} ft
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={well.status} />
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickActionCard
          title="Start New Analysis"
          description="Create a new well and begin the wellbore stability workflow"
          to="/wells"
          icon={<Plus className="w-5 h-5" />}
        />
        <QuickActionCard
          title="View All Wells"
          description="Browse and manage your existing wells"
          to="/wells"
          icon={<CircleDot className="w-5 h-5" />}
        />
        <QuickActionCard
          title="Documentation"
          description="Learn about the workflow and calculations"
          to="#"
          icon={<Activity className="w-5 h-5" />}
        />
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'amber' | 'emerald' | 'slate';
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    slate: 'bg-slate-100 text-slate-600',
  };

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <span className="text-2xl font-bold text-slate-900">{value}</span>
      </div>
      <p className="text-sm text-slate-600">{title}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; className: string }> = {
    planning: { label: 'Planning', className: 'status-planning' },
    drilling: { label: 'Drilling', className: 'status-drilling' },
    completed: { label: 'Completed', className: 'status-completed' },
  };

  const config = statusConfig[status] || statusConfig.planning;

  return <span className={config.className}>{config.label}</span>;
}

interface QuickActionCardProps {
  title: string;
  description: string;
  to: string;
  icon: React.ReactNode;
}

function QuickActionCard({ title, description, to, icon }: QuickActionCardProps) {
  return (
    <Link
      to={to}
      className="card-hover p-4 group"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-slate-100 text-slate-600 group-hover:bg-primary-50 group-hover:text-primary-600 transition-colors">
          {icon}
        </div>
        <div>
          <h3 className="font-medium text-slate-900 group-hover:text-primary-600 transition-colors">
            {title}
          </h3>
          <p className="text-sm text-slate-600 mt-0.5">{description}</p>
        </div>
      </div>
    </Link>
  );
}
