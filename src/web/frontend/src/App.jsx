import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { DataEditor } from './components/DataEditor';
import { PreviewPane } from './components/PreviewPane';
import { TailorModal } from './components/TailorModal';
import { FileText, Save, Wand2, RotateCw } from 'lucide-react';

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
  },
  tailorResume: async (jd_text) => {
    const res = await fetch('/api/tailor', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd_text })
    });
    if (!res.ok) throw new Error("Failed to tailor");
    return res.json();
  }
};

const App = () => {
  // Versions State: Array of { id, name, data, isMaster, timestamp }
  const [versions, setVersions] = useState([]);
  const [activeVersionId, setActiveVersionId] = useState(null);

  const [isTailoring, setIsTailoring] = useState(false);
  const [showTailorModal, setShowTailorModal] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [template, setTemplate] = useState('compact');

  // Helper to get active data
  const activeData = versions.find(v => v.id === activeVersionId)?.data || INITIAL_DATA_TEMPLATE;
  const isMaster = versions.find(v => v.id === activeVersionId)?.isMaster || false;

  // Load Data on Mount
  useEffect(() => {
    API.getProfile().then(prof => {
      // Ensure IDs
      ['work', 'education', 'projects'].forEach(section => {
        if (prof[section]) {
          prof[section] = prof[section].map((item, i) => ({ ...item, id: item.id || i }));
        }
      });

      const masterVersion = {
        id: 'master',
        name: 'Master Profile',
        data: prof,
        isMaster: true,
        timestamp: Date.now()
      };

      setVersions([masterVersion]);
      setActiveVersionId('master');
    }).catch(err => console.error(err));
  }, []);

  // Update active data
  const setData = (newDataOrFn) => {
    setVersions(prev => prev.map(v => {
      if (v.id === activeVersionId) {
        const newData = typeof newDataOrFn === 'function' ? newDataOrFn(v.data) : newDataOrFn;
        return { ...v, data: newData };
      }
      return v;
    }));
    if (isMaster) setIsDirty(true);
  };

  const handleSave = async () => {
    if (!isMaster) return; // Only save master

    await API.saveSection('basics', activeData.basics);
    await API.saveSection('work', activeData.work);
    await API.saveSection('education', activeData.education);
    await API.saveSection('projects', activeData.projects);
    await API.saveSection('skills', activeData.skills);

    setIsDirty(false);
    alert('Saved Master Profile!');
  };

  const handleTailor = async (jd) => {
    setIsTailoring(true);
    try {
      // Use active data as base? Or always Master? Let's use Master as base for consistency.
      // Actually, using current view as base is more flexible but Master is safer. 
      // Let's use User's Master profile as source of truth for tailoring.
      // const masterData = versions.find(v => v.isMaster).data;

      const tailored = await API.tailorResume(jd);

      // Ensure IDs
      ['work', 'education', 'projects'].forEach(section => {
        if (tailored[section]) {
          tailored[section] = tailored[section].map((item, i) => ({ ...item, id: item.id || i }));
        }
      });

      const newVersion = {
        id: Date.now().toString(),
        name: `Tailored Resume ${versions.length}`, // Simple name for now, or extract from JD
        data: tailored,
        isMaster: false,
        timestamp: Date.now()
      };

      setVersions(prev => [...prev, newVersion]);
      setActiveVersionId(newVersion.id);
      setShowTailorModal(false);
      // alert("Resume tailored! Check the sidebar.");
    } catch (e) {
      console.error(e);
      alert("Failed to tailor resume.");
    } finally {
      setIsTailoring(false);
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-200 font-sans overflow-hidden print:overflow-visible print:h-auto">
      <div className="print:hidden">
        <Sidebar
          versions={versions}
          activeVersionId={activeVersionId}
          onSelectVersion={setActiveVersionId}
          onNewTailor={() => setShowTailorModal(true)}
        />
      </div>

      <div className="flex-1 flex flex-col min-w-[500px] border-r border-zinc-800 relative print:hidden">
        <div className="h-12 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-950/50 backdrop-blur">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
            <FileText size={14} />
            <span className={!isMaster ? "text-indigo-400 font-bold" : ""}>
              {versions.find(v => v.id === activeVersionId)?.name || "Loading..."}
            </span>
            {isMaster && isDirty && <span className="text-amber-500 ml-2">* Unsaved</span>}
          </div>

          <div className="flex items-center gap-2">
            {isMaster && isDirty && (
              <button onClick={handleSave} className="text-xs bg-zinc-800 hover:bg-zinc-700 text-white px-3 py-1.5 rounded flex items-center gap-2">
                <Save size={12} /> Save Master
              </button>
            )}
            {!isMaster && (
              <span className="text-xs text-zinc-600 italic">Read Only / Transient</span>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-hidden relative">
          {/* DataEditor always receives active data */}
          <DataEditor data={activeData} setData={setData} setIsDirty={setIsDirty} />
        </div>

        <TailorModal isOpen={showTailorModal} onClose={() => setShowTailorModal(false)} onTailor={handleTailor} isLoading={isTailoring} />
      </div>

      <div className="w-[50%] hidden xl:block print:block print:w-auto print:absolute print:inset-0">
        <PreviewPane data={activeData} template={template} setTemplate={setTemplate} />
      </div>
    </div>
  );
};

export default App;
