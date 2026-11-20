import { ReactNode } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  FileText,
  UploadCloud,
  Layers,
  Search,
  GitCompare,
  Sliders,
  CheckSquare,
  BarChart3,
  History,
  Users,
  Settings,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface AppShellProps {
  children: ReactNode;
}

export const AppShell = ({ children }: AppShellProps) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Regulatory Documents', path: '/documents', icon: FileText },
    { label: 'Upload Document', path: '/upload', icon: UploadCloud },
    { label: 'Obligation Explorer', path: '/obligations', icon: Search },
    { label: 'Evidence Review', path: '/evidence', icon: Layers },
    { label: 'Version Comparison', path: '/compare', icon: GitCompare },
    { label: 'Control Mapping', path: '/controls', icon: Sliders },
    { label: 'Human Review Queue', path: '/review-queue', icon: CheckSquare },
    { label: 'Impact Reports', path: '/reports', icon: BarChart3 },
    { label: 'Audit Ledger', path: '/audit', icon: History },
    { label: 'User Management', path: '/users', icon: Users, adminOnly: true },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];


  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const roleColors: Record<string, string> = {
    admin: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
    compliance_officer: 'bg-teal-500/15 text-teal-300 border-teal-500/30',
    reviewer: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    management: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  };

  const getPageTitle = () => {
    const matched = navItems.find((item) =>
      item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path)
    );
    return matched ? matched.label : 'ROIS';
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-navy-950 border-r border-slate-800 flex flex-col flex-shrink-0">
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400 shadow-sm">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white">ROIS</span>
                <span className="text-[10px] bg-teal-500/10 text-teal-300 border border-teal-500/30 px-1.5 py-0.2 rounded font-mono">
                  IFSCA
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Regulatory Intelligence</p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => {
            if (item.adminOnly && user?.role !== 'admin') {
              return null;
            }

            const Icon = item.icon;
            const isActive =
              item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-teal-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Card in Footer */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/60">
          <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
            <div className="flex items-center justify-between mb-1.5">
              <div className="truncate pr-2">
                <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'Authorized User'}</p>
                <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
                title="Sign Out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-[10px]">
              <span className="text-slate-500">Role:</span>
              <span className={`px-2 py-0.5 rounded-full border text-[10px] font-medium capitalize ${roleColors[user?.role || 'compliance_officer']}`}>
                {user?.role?.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-14 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-bold text-white tracking-tight">{getPageTitle()}</h1>
            <span className="text-slate-600">|</span>
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse"></span>
              IFSCA Scope Active (GIFT IFSC)
            </span>
          </div>

        </header>

        {/* Main Content Body */}
        <main className="flex-1 overflow-y-auto bg-slate-950 p-6">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
};
