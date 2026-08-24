import { Activity, ShieldAlert, Settings, LayoutDashboard } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { name: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Audit Log', path: '/dashboard/audit', icon: Activity },
    { name: 'Policies', path: '/dashboard/policies', icon: ShieldAlert },
    { name: 'Settings', path: '/dashboard/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 h-screen bg-panel border-r border-muted/20 flex flex-col">
      <div className="p-6">
        <Link to="/" className="font-mono text-sm tracking-widest text-text font-bold">
          SENTINEL
        </Link>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive 
                  ? 'bg-signal/10 text-signal' 
                  : 'text-muted hover:text-text hover:bg-muted/10'
              }`}
            >
              <item.icon size={18} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-muted/20">
        <div className="flex items-center gap-3 px-3 py-2 text-xs text-muted font-mono">
          <div className="w-2 h-2 rounded-full bg-signal animate-pulse"></div>
          ENGINE ACTIVE
        </div>
      </div>
    </aside>
  );
}
