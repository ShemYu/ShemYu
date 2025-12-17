import React from 'react';
import { Layout, Wand2, GitBranch } from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab, isDirty }) => {
    const navItems = [
        { id: 'editor', icon: Layout, label: 'Editor' },
        { id: 'ai', icon: Wand2, label: 'AI Tailor' },
        { id: 'settings', icon: GitBranch, label: 'Version Control' },
    ];

    return (
        <div className="w-16 flex flex-col items-center py-6 bg-zinc-950 border-r border-zinc-800 h-screen select-none z-20 print:hidden">
            <div className="mb-8 p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg shadow-indigo-500/20">
                <span className="font-mono font-bold text-white text-lg">SY</span>
            </div>
            <div className="flex flex-col gap-4 w-full px-2">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => setActiveTab(item.id)}
                        className={`p-3 rounded-xl transition-all duration-200 group relative flex justify-center 
              ${activeTab === item.id ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'}`}
                        title={item.label}
                    >
                        <item.icon size={20} />
                        {item.id === 'settings' && isDirty && (
                            <span className="absolute top-2 right-2 w-2 h-2 bg-amber-500 rounded-full border border-zinc-950"></span>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};
