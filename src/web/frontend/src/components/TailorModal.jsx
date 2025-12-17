import React, { useState } from 'react';
import { Wand2, X, Loader2 } from 'lucide-react';

export const TailorModal = ({ isOpen, onClose, onTailor, isLoading }) => {
    const [jd, setJd] = useState('');

    if (!isOpen) return null;

    const handleSubmit = () => {
        if (!jd.trim()) return;
        onTailor(jd);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
                <div className="p-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-950/50">
                    <div className="flex items-center gap-2 text-indigo-400 font-bold">
                        <Wand2 size={18} />
                        <h3>AI Resume Tailor</h3>
                    </div>
                    <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors">
                        <X size={18} />
                    </button>
                </div>

                <div className="p-6 flex-1 overflow-y-auto">
                    <p className="text-zinc-400 text-sm mb-4">
                        Paste the <strong>Job Description</strong> below. AI will adapt your summary, experiences, and skills to match the keywords.
                    </p>
                    <textarea
                        className="w-full h-64 bg-zinc-950 border border-zinc-800 rounded-lg p-4 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500 transition-all resize-none placeholder-zinc-700 font-mono"
                        placeholder="Paste Job Description here..."
                        value={jd}
                        onChange={(e) => setJd(e.target.value)}
                        disabled={isLoading}
                    />
                </div>

                <div className="p-4 border-t border-zinc-800 bg-zinc-950/50 flex justify-end gap-3">
                    <button onClick={onClose} disabled={isLoading}
                        className="px-4 py-2 text-xs font-medium text-zinc-400 hover:text-white transition-colors">
                        Cancel
                    </button>
                    <button onClick={handleSubmit} disabled={isLoading || !jd.trim()}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold rounded flex items-center gap-2 transition-all shadow-lg shadow-indigo-900/20">
                        {isLoading ? <Loader2 size={14} className="animate-spin" /> : <Wand2 size={14} />}
                        {isLoading ? 'Tailoring...' : 'Generate Tailored Resume'}
                    </button>
                </div>
            </div>
        </div>
    );
};
