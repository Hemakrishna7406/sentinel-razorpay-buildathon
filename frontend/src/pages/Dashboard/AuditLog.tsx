import { useState } from 'react';
import { Search, Filter, Download } from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';
import type { SentinelDecision } from '../../types';

export default function AuditLog() {
  const { messages } = useWebSocket({ url: '', mock: true });
  const [filter, setFilter] = useState<SentinelDecision | 'ALL'>('ALL');

  const filteredMessages = messages.filter(m => filter === 'ALL' || m.decision === filter);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      
      <header className="flex justify-between items-end">
        <div>
          <h1 className="font-display text-3xl font-bold text-text">Audit Log</h1>
          <p className="text-muted font-mono text-sm mt-1">HISTORICAL DECISION REGISTRY</p>
        </div>
        <div className="flex items-center gap-4">
           <button className="flex items-center gap-2 px-4 py-2 bg-panel border border-muted/20 rounded-md text-sm font-mono text-text hover:bg-muted/10 transition-colors">
              <Download size={16} />
              EXPORT CSV
           </button>
        </div>
      </header>

      <div className="bg-panel border border-muted/20 rounded-xl overflow-hidden flex flex-col h-[calc(100vh-200px)]">
        
        {/* Toolbar */}
        <div className="p-4 border-b border-muted/20 flex justify-between items-center bg-ink/50">
           <div className="relative">
             <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
             <input 
               type="text" 
               placeholder="Search intent ID, agent..." 
               className="pl-10 pr-4 py-2 bg-panel border border-muted/20 rounded-md text-sm text-text focus:outline-none focus:border-signal w-64 transition-colors"
             />
           </div>
           
           <div className="flex items-center gap-2">
             <Filter size={16} className="text-muted" />
             <div className="flex bg-panel rounded-md border border-muted/20 p-1">
               {['ALL', 'ALLOWED', 'CONTAINED'].map((f) => (
                 <button
                   key={f}
                   onClick={() => setFilter(f as any)}
                   className={`px-3 py-1 text-xs font-mono rounded ${filter === f ? 'bg-ink text-text' : 'text-muted hover:text-text'} transition-colors`}
                 >
                   {f}
                 </button>
               ))}
             </div>
           </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-panel border-b border-muted/20 z-10">
              <tr>
                <th className="px-6 py-4 font-mono text-xs text-muted font-medium">TIMESTAMP</th>
                <th className="px-6 py-4 font-mono text-xs text-muted font-medium">INTENT ID</th>
                <th className="px-6 py-4 font-mono text-xs text-muted font-medium">ACTION</th>
                <th className="px-6 py-4 font-mono text-xs text-muted font-medium">RISK SCORE</th>
                <th className="px-6 py-4 font-mono text-xs text-muted font-medium">DECISION</th>
                <th className="px-6 py-4 font-mono text-xs text-muted font-medium">REASON</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-muted/10">
              {filteredMessages.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted font-mono text-sm">
                    No matching records found.
                  </td>
                </tr>
              ) : (
                filteredMessages.map((msg) => (
                  <tr key={msg.id} className="hover:bg-muted/5 transition-colors">
                    <td className="px-6 py-4 text-sm text-muted">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-4 text-sm font-mono text-text">{msg.id}</td>
                    <td className="px-6 py-4 text-sm">{msg.action}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-mono ${msg.riskScore > 75 ? 'bg-contain/20 text-contain' : 'bg-signal/20 text-signal'}`}>
                        {msg.riskScore.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm font-mono font-bold">
                      <span className={msg.decision === 'CONTAINED' ? 'text-contain' : 'text-signal'}>
                        {msg.decision}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-muted max-w-[200px] truncate">
                      {msg.reasons.length > 0 ? msg.reasons.join(', ') : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
