import React from 'react';
import { Layout, Wand2, GitBranch } from 'lucide-react';

export const Sidebar = ({ versions, activeVersionId, onSelectVersion, onNewTailor }) => {
    return (
        <div className="w-64 flex flex-col bg-zinc-950 border-r border-zinc-800 h-screen select-none print:hidden">
            {/* Header */}
            <div className="p-4 border-b border-zinc-800 flex items-center gap-3">
                <div className="p-1.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded shadow-lg shadow-indigo-500/20">
                    <span className="font-mono font-bold text-white text-sm">SY</span>
                </div>
                <span className="font-bold text-zinc-200">ShemYu Resume</span>
            </div>

            {/* Version List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
                <div className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2 px-2 mt-2">Versions</div>

                {versions.map((v) => (
                    <button
                        key={v.id}
                        onClick={() => onSelectVersion(v.id)}
                        className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200 flex items-center gap-3 group
                        ${activeVersionId === v.id
                                ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-zinc-700'
                                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50'}`}
                    >
                        {/* Icon */}
                        {v.id === 'master' ? (
                            <Layout size={16} className={activeVersionId === v.id ? "text-indigo-400" : "text-zinc-500"} />
                        ) : (
                            <GitBranch size={16} className={activeVersionId === v.id ? "text-purple-400" : "text-zinc-500 group-hover:text-purple-400"} />
                        )}

                        <div className="truncate flex-1">
                            {v.name}
                            {v.id !== 'master' && <div className="text-[10px] text-zinc-600 font-mono mt-0.5">{new Date(v.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>}
                        </div>
                    </button>
                ))}
            </div>

            {/* Action Area */}
            <div className="p-4 border-t border-zinc-800 bg-zinc-900/30">
                <button
                    onClick={onNewTailor}
                    className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg text-sm font-medium transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 group"
                >
                    <Wand2 size={16} className="group-hover:animate-pulse" />
                    <span>New AI Resume</span>
                </button>
            </div>
        </div>
    );
};
