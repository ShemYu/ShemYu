import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { DataEditor } from './components/DataEditor';
import { PreviewPane } from './components/PreviewPane';
import { FileText, Save } from 'lucide-react';

const INITIAL_DATA_TEMPLATE = {
  basics: { name: "", label: "", summary: "", email: "", phone: "", website: "" },
  work: [],
  education: [],
  skills: [],
  projects: []
};

// Simple API Layer
const API = {
  getProfile: async () => {
    const res = await fetch('/api/profile');
    if (!res.ok) throw new Error("Failed to fetch");
    return res.json();
  },
  saveSection: async (section, data) => {
    await fetch(`/api/profile/${section}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data })
    });
  }
};

const App = () => {
  const [data, setData] = useState(INITIAL_DATA_TEMPLATE);
  const [activeTab, setActiveTab] = useState('editor');
  const [isDirty, setIsDirty] = useState(false);
  const [template, setTemplate] = useState('compact');

  // Load Data on Mount
  useEffect(() => {
    // We need to map the flat API response to our UI structure
    // API returns { basics: {}, work: [], ... } which matches mostly
    API.getProfile().then(prof => {
      // Add 'id' to list items for React keys/editing if missing
      ['work', 'education', 'projects'].forEach(section => {
        if (prof[section]) {
          prof[section] = prof[section].map((item, i) => ({ ...item, id: item.id || i }));
        }
      });
      console.log("Loaded Profile:", prof); // Debug
      setData(prev => ({ ...prev, ...prof }));
    }).catch(err => console.error(err));
  }, []);

  const handleSave = async () => {
    // Save all modified sections
    await API.saveSection('basics', data.basics);
    await API.saveSection('work', data.work);
    await API.saveSection('education', data.education);
    await API.saveSection('projects', data.projects);
    // Skills are usually a flat list of objects or strings in our data model
    // But verify structure. Backend expects list of objects for saving as individual files?
    // Actually loader.save_section saves a list of generic items. 
    // Skills might be special if they are in one file? 
    // Checking loader.py: generic save_section saves list as separate files 00_item.yaml etc.
    // Existing data structure: data/skills/*.yaml. So it matches.
    await API.saveSection('skills', data.skills);

    setIsDirty(false);
    alert('Saved!');
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-200 font-sans overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} isDirty={isDirty} />

      <div className="flex-1 flex flex-col min-w-[500px] border-r border-zinc-800 relative print:hidden">
        <div className="h-12 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-950/50 backdrop-blur">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
            <FileText size={14} /> <span>resume.yaml</span>
            <span className="text-xs text-green-500 ml-2">Work Items: {data.work?.length}</span>
            {isDirty && <span className="text-amber-500 ml-2">* Unsaved</span>}
          </div>
          {isDirty && (
            <button onClick={handleSave} className="text-xs bg-zinc-800 hover:bg-zinc-700 text-white px-3 py-1.5 rounded flex items-center gap-2">
              <Save size={12} /> Save
            </button>
          )}
        </div>

        <div className="flex-1 overflow-hidden relative">
          {activeTab === 'editor' && <DataEditor data={data} setData={setData} setIsDirty={setIsDirty} />}
          {activeTab === 'settings' && <div className="p-10 text-center text-zinc-500">Git Integration Coming Soon</div>}
        </div>
      </div>

      <div className="w-[50%] hidden xl:block print:block print:w-auto print:absolute print:inset-0">
        <PreviewPane data={data} template={template} setTemplate={setTemplate} />
      </div>
    </div>
  );
};

export default App;
