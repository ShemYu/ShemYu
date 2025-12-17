import React, { useState } from 'react';
import { ArrowLeft, GripVertical, Trash2, Eye, EyeOff } from 'lucide-react';

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
    const [editingId, setEditingId] = useState(null);

    // Update Helpers
    const updateBasics = (field, val) => {
        setData(p => ({ ...p, basics: { ...p.basics, [field]: val } }));
        setIsDirty(true);
    };

    const updateItem = (section, id, field, val) => {
        setData(prev => ({
            ...prev,
            [section]: prev[section].map(i => i.id === id ? { ...i, [field]: val } : i)
        }));
        setIsDirty(true);
    };

    const toggleVisibility = (section, id, e) => {
        e.stopPropagation(); // Prevent entering edit mode
        setData(prev => ({
            ...prev,
            [section]: prev[section].map(i => {
                if (i.id === id) {
                    // Default to true if undefined, so toggle makes it false
                    const current = i.visible !== false;
                    return { ...i, visible: !current };
                }
                return i;
            })
        }));
        setIsDirty(true);
    };

    const addItem = (section) => {
        const newItem = { id: Date.now(), visible: true }; // Default visible
        if (section === 'work') newItem.highlights = [];
        if (section === 'projects') newItem.highlights = [];
        if (section === 'skills') { newItem.name = "New Skill"; newItem.keywords = []; }

        setData(prev => ({ ...prev, [section]: [newItem, ...(prev[section] || [])] }));
        setEditingSection(section);
        setEditingId(newItem.id);
        setIsDirty(true);
    };

    const deleteItem = (section, id) => {
        if (!confirm("Delete this item?")) return;
        setData(prev => ({ ...prev, [section]: prev[section].filter(i => i.id !== id) }));
        setEditingId(null);
        setIsDirty(true);
    };

    // Generic Editor Renderers
    const renderEditor = () => {
        if (editingSection === 'basics') return null; // Handled separately

        const list = data[editingSection] || [];
        const item = list.find(i => i.id === editingId);
        if (!item) return <div>Item not found</div>;

        const handleUpdate = (field, val) => updateItem(editingSection, editingId, field, val);

        return (
            <div className="p-8 max-w-2xl mx-auto h-full overflow-y-auto animate-in slide-in-from-right-4">
                <button onClick={() => setEditingId(null)} className="text-zinc-500 hover:text-white flex items-center gap-2 mb-6">
                    <ArrowLeft size={16} /> Back to List
                </button>
                <div className="flex justify-between items-start mb-6">
                    <h2 className="text-xl font-bold text-white capitalize">{editingSection} Item</h2>
                    <button onClick={() => deleteItem(editingSection, editingId)} className="text-red-400 hover:text-red-300 text-xs flex items-center gap-1">
                        <Trash2 size={12} /> Delete
                    </button>
                </div>

                <div className="space-y-6">
                    {/* Work / Experience */}
                    {editingSection === 'work' && (
                        <>
                            <StyledInput label="Company" value={item.company} onChange={e => handleUpdate('company', e.target.value)} />
                            <StyledInput label="Position" value={item.position} onChange={e => handleUpdate('position', e.target.value)} />
                            <div className="grid grid-cols-2 gap-4">
                                <StyledInput label="Start Date" value={item.startDate} placeholder="2023-01" onChange={e => handleUpdate('startDate', e.target.value)} />
                                <StyledInput label="End Date" value={item.endDate} placeholder="Present" onChange={e => handleUpdate('endDate', e.target.value)} />
                            </div>
                            <StyledTextArea label="Summary" value={item.summary} onChange={e => handleUpdate('summary', e.target.value)} />
                            <HighlightEditor highlights={item.highlights} onChange={h => handleUpdate('highlights', h)} />
                        </>
                    )}

                    {/* Education */}
                    {editingSection === 'education' && (
                        <>
                            <StyledInput label="Institution" value={item.institution} onChange={e => handleUpdate('institution', e.target.value)} />
                            <div className="grid grid-cols-2 gap-4">
                                <StyledInput label="Area / Degree" value={item.area} onChange={e => handleUpdate('area', e.target.value)} />
                                <StyledInput label="Study Type" value={item.studyType} placeholder="Bachelor / Master" onChange={e => handleUpdate('studyType', e.target.value)} />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <StyledInput label="Start Date" value={item.startDate} placeholder="2018-09" onChange={e => handleUpdate('startDate', e.target.value)} />
                                <StyledInput label="End Date" value={item.endDate} placeholder="2022-06" onChange={e => handleUpdate('endDate', e.target.value)} />
                            </div>
                            <StyledInput label="Score" value={item.score} placeholder="GPA 3.8 / 4.0" onChange={e => handleUpdate('score', e.target.value)} />
                            <HighlightEditor highlights={item.courses} onChange={h => handleUpdate('courses', h)} />
                        </>
                    )}

                    {/* Projects */}
                    {editingSection === 'projects' && (
                        <>
                            <StyledInput label="Project Name" value={item.name} onChange={e => handleUpdate('name', e.target.value)} />
                            <StyledInput label="Role / Tech" value={item.role || item.keywords} onChange={e => handleUpdate('role', e.target.value)} />
                            <StyledTextArea label="Summary" value={item.summary} onChange={e => handleUpdate('summary', e.target.value)} />
                            <HighlightEditor highlights={item.highlights} onChange={h => handleUpdate('highlights', h)} />
                        </>
                    )}

                    {/* Skills */}
                    {editingSection === 'skills' && (
                        <>
                            <StyledInput label="Category Name" value={item.name} placeholder="e.g. Languages" onChange={e => handleUpdate('name', e.target.value)} />
                            <HighlightEditor highlights={item.keywords} onChange={h => handleUpdate('keywords', h)} />
                        </>
                    )}
                </div>
            </div>
        );
    };

    if (editingId !== null) {
        return renderEditor();
    }

    const SectionList = ({ title, section }) => (
        <div className="space-y-2">
            <div className="flex justify-between items-center mt-8 mb-2">
                <h3 className="text-sm font-bold text-indigo-400 uppercase">{title}</h3>
                <button onClick={() => addItem(section)} className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2 py-1 rounded">
                    + Add
                </button>
            </div>
            {data[section]?.map(item => {
                const isHidden = item.visible === false;
                return (
                    <div key={item.id || Math.random()} onClick={() => { setEditingSection(section); setEditingId(item.id); }}
                        className={`bg-zinc-900 border border-zinc-800 p-4 rounded hover:border-zinc-600 cursor-pointer transition-colors relative group ${isHidden ? 'opacity-50 grayscale' : ''}`}>

                        {/* Visibility Toggle Button */}
                        <button
                            onClick={(e) => toggleVisibility(section, item.id, e)}
                            className="absolute top-3 right-3 text-zinc-600 hover:text-white z-10 p-1 rounded hover:bg-zinc-700 transition-all opacity-0 group-hover:opacity-100"
                            title={isHidden ? "Show Item" : "Hide Item"}
                        >
                            {isHidden ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>

                        <div className="flex justify-between items-start pr-6">
                            <div className="font-bold text-white pr-4">
                                {item.company || item.institution || item.name || "Untitled"}
                            </div>
                            {/* Dates for Work */}
                            {(section === 'work' && item.startDate) && (
                                <div className="text-[10px] font-mono text-zinc-600 bg-zinc-900/50 border border-zinc-800 px-1.5 py-0.5 rounded">
                                    {item.startDate} {item.endDate ? `- ${item.endDate}` : ''}
                                </div>
                            )}
                        </div>

                        {/* Position or Degree */}
                        <div className="text-xs text-zinc-500 mt-1">
                            {item.position || item.studyType || item.area || item.name}
                            {/* Append Area to StudyType if both exist for Education */}
                            {section === 'education' && item.studyType && item.area && ` - ${item.area}`}
                        </div>
                    </div>
                );
            })}
            {(!data[section] || data[section].length === 0) && (
                <div className="text-zinc-600 text-xs italic p-2">No items yet.</div>
            )}
        </div>
    );

    return (
        <div className="p-8 max-w-2xl mx-auto h-full overflow-y-auto">
            <h1 className="text-2xl font-bold text-white mb-8">Data Editor</h1>
            <div className="space-y-6">
                {/* Basics */}
                <StyledInput label="Name" value={data.basics?.name} onChange={e => updateBasics('name', e.target.value)} />
                <StyledInput label="Label" value={data.basics?.label} onChange={e => updateBasics('label', e.target.value)} />
                <StyledTextArea label="Summary" value={data.basics?.summary} onChange={e => updateBasics('summary', e.target.value)} />

                <div className="h-px bg-zinc-800 my-6" />

                {/* Sections */}
                <SectionList title="Work Experience" section="work" />
                <SectionList title="Education" section="education" />
                <SectionList title="Projects" section="projects" />
                <SectionList title="Skills" section="skills" />

                <div className="h-12" /> {/* Spacer */}
            </div>
        </div>
    );
};
