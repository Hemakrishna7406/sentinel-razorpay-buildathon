import { Outlet } from 'react-router-dom';
import Sidebar from '../../components/Sidebar/Sidebar';

export default function Dashboard() {
  return (
    <div className="flex h-screen bg-ink text-text overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {/* The Outlet renders the nested dashboard route components (e.g., Overview, Audit) */}
        <Outlet />
      </main>
    </div>
  );
}
