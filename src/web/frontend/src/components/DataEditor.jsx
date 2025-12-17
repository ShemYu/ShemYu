import React, { useState } from 'react';
import { ArrowLeft, GripVertical, Trash2 } from 'lucide-react';

const StyledInput = ({ label, value, onChange, placeholder, className = "" }) => (
    <div className={`flex flex-col gap-1.5 ${className}`}>
        <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider font-mono">{label}</label>
        <input type="text" value={value || ''} onChange={onChange} placeholder={placeholder}
            className="bg-zinc-900 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all placeholder-zinc-600 font-sans" />
    </div>
);

const StyledTextArea = ({ label, value, onChange, placeholder, rows = 3 }) => (
    <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider font-mono">{label}</label>
        <textarea value={value || ''} onChange={onChange} placeholder={placeholder} rows={rows}
            className="bg-zinc-900 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all placeholder-zinc-600 font-sans resize-none" />
    </div>
);

const HighlightEditor = ({ highlights, onChange }) => {
    const list = highlights || [];
    const handleChange = (index, value) => { const newH = [...list]; newH[index] = value; onChange(newH); };

    // Add new item
    const add = () => onChange([...list, ""]);

    // Remove
    const remove = (index) => onChange(list.filter((_, i) => i !== index));

    return (
        <div className="flex flex-col gap-2 mt-2">
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider font-mono">Highlights</label>
            <div className="space-y-1">
                {list.map((point, index) => (
                    <div key={index} className="flex items-start gap-2 group">
                        <GripVertical size={14} className="mt-2.5 text-zinc-600 cursor-grab" />
                        <input
                            type="text"
                            value={point}
                            onChange={(e) => handleChange(index, e.target.value)}
                            className="flex-1 bg-transparent border-b border-zinc-800/50 focus:border-indigo-500 py-2 px-1 text-sm text-zinc-300 focus:outline-none"
                        />
                        <button onClick={() => remove(index)} className="mt-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100">
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>
            <button onClick={add} className="text-xs text-indigo-400 hover:text-indigo-300 mt-2 text-left">+ Add Highlight</button>
        </div>
    );
};

export const DataEditor = ({ data, setData, setIsDirty }) => {
    const [editingSection, setEditingSection] = useState('basics');
    const [editingWorkId, setEditingWorkId] = useState(null);

    // Update Helpers
    const updateBasics = (field, val) => {
        setData(p => ({ ...p, basics: { ...p.basics, [field]: val } }));
        setIsDirty(true);
    };

    // Work Editor Logic
    if (editingSection === 'work' && editingWorkId !== null) {
        const job = data.work.find(j => j.id === editingWorkId);
        if (!job) return <div>Job not found</div>;

        const updateJob = (field, val) => {
            setData(prev => ({
                ...prev,
                work: prev.work.map(i => i.id === job.id ? { ...i, [field]: val } : i)
            }));
            setIsDirty(true);
        };

        return (
            <div className="p-8 max-w-2xl mx-auto h-full overflow-y-auto animate-in slide-in-from-right-4">
                <button onClick={() => setEditingWorkId(null)} className="text-zinc-500 hover:text-white flex items-center gap-2 mb-6">
                    <ArrowLeft size={16} /> Back to List
                </button>
                <div className="space-y-6">
                    <StyledInput label="Company" value={job.company} onChange={e => updateJob('company', e.target.value)} />
                    <div className="grid grid-cols-2 gap-4">
                        <StyledInput label="Position" value={job.position} onChange={e => updateJob('position', e.target.value)} />
                        <StyledInput label="Dates" value={job.startDate} placeholder="2023-01 / Present" onChange={e => updateJob('startDate', e.target.value)} />
                    </div>
                    <StyledTextArea label="Summary" value={job.summary} onChange={e => updateJob('summary', e.target.value)} />
                    <HighlightEditor highlights={job.highlights} onChange={h => updateJob('highlights', h)} />
                </div>
            </div>
        )
    }

    return (
        <div className="p-8 max-w-2xl mx-auto h-full overflow-y-auto">
            <h1 className="text-2xl font-bold text-white mb-8">Data Editor</h1>
            <div className="space-y-6">
                {/* Basics */}
                <StyledInput label="Name" value={data.basics?.name} onChange={e => updateBasics('name', e.target.value)} />
                <StyledInput label="Label" value={data.basics?.label} onChange={e => updateBasics('label', e.target.value)} />
                <StyledTextArea label="Summary" value={data.basics?.summary} onChange={e => updateBasics('summary', e.target.value)} />

                <div className="h-px bg-zinc-800" />

                {/* Work List */}
                <div className="flex justify-between items-center">
                    <h3 className="text-sm font-bold text-indigo-400 uppercase">Work Experience</h3>
                </div>
                {data.work?.map(j => (
                    <div key={j.id || Math.random()} onClick={() => { setEditingSection('work'); setEditingWorkId(j.id); }}
                        className="bg-zinc-900 border border-zinc-800 p-4 rounded hover:border-zinc-600 cursor-pointer transition-colors">
                        <div className="font-bold text-white">{j.company}</div>
                        <div className="text-xs text-zinc-500">{j.position}</div>
                    </div>
                ))}

                {/* TODO: Add Projects / Education / Skills sections if needed */}
                <div className="text-zinc-600 text-xs italic text-center mt-8">
                    (More sections can be added here...)
                </div>
            </div>
        </div>
    );
};
