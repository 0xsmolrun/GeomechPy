import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAppStore } from '../lib/store';
import {
  Activity,
  LogOut,
  Plus,
  ChevronLeft,
  ChevronRight,
  Settings,
  HelpCircle,
  CircleDot,
} from 'lucide-react';

export function Layout() {
  const { user, sidebarOpen, setSidebarOpen, wells } = useAppStore();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 bg-slate-900 transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-16'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-cyan-400 flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              {sidebarOpen && (
                <span className="text-white font-semibold">GeomechPy</span>
              )}
            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1 text-slate-400 hover:text-white transition-colors"
            >
              {sidebarOpen ? (
                <ChevronLeft className="w-5 h-5" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto scrollbar-thin">
            <NavItem
              to="/"
              icon={<Activity className="w-5 h-5" />}
              label="Dashboard"
              collapsed={!sidebarOpen}
            />
            <NavItem
              to="/wells"
              icon={<CircleDot className="w-5 h-5" />}
              label="Wells"
              collapsed={!sidebarOpen}
            />

            {sidebarOpen && wells.length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-700">
                <p className="px-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Recent Wells
                </p>
                <div className="mt-2 space-y-1">
                  {wells.slice(0, 5).map((well) => (
                    <NavLink
                      key={well.id}
                      to={`/wells/${well.id}`}
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                          isActive
                            ? 'bg-slate-800 text-white'
                            : 'text-slate-400 hover:text-white hover:bg-slate-800'
                        }`
                      }
                    >
                      <span className="truncate">{well.name}</span>
                    </NavLink>
                  ))}
                </div>
              </div>
            )}
          </nav>

          {/* Bottom Section */}
          <div className="p-2 border-t border-slate-700 space-y-1">
            <NavLink
              to="/wells"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <Plus className="w-5 h-5" />
              {sidebarOpen && <span className="text-sm">New Well</span>}
            </NavLink>
            <NavLink
              to="#"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <Settings className="w-5 h-5" />
              {sidebarOpen && <span className="text-sm">Settings</span>}
            </NavLink>
            <NavLink
              to="#"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <HelpCircle className="w-5 h-5" />
              {sidebarOpen && <span className="text-sm">Help</span>}
            </NavLink>
          </div>

          {/* User */}
          <div className="p-2 border-t border-slate-700">
            <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-800">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-cyan-400 flex items-center justify-center text-white text-sm font-medium">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              {sidebarOpen && (
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{user?.email}</p>
                </div>
              )}
              {sidebarOpen && (
                <button
                  onClick={handleSignOut}
                  className="p-1 text-slate-400 hover:text-white transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={`flex-1 transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-16'
        }`}
      >
        <div className="page-transition">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  collapsed: boolean;
}

function NavItem({ to, icon, label, collapsed }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
          isActive
            ? 'bg-slate-800 text-white'
            : 'text-slate-400 hover:text-white hover:bg-slate-800'
        }`
      }
    >
      {icon}
      {!collapsed && <span className="text-sm font-medium">{label}</span>}
    </NavLink>
  );
}
