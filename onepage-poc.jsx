import React, { useState, useEffect, useRef } from 'react';
import {
Briefcase, User, Cpu, GitBranch, Save, Wand2, Layout, Plus, Trash2,
GripVertical, ChevronRight, ArrowLeft, CheckCircle2, FileText,
Download, Printer, FileType, Layers, Minimize2, Maximize2
} from 'lucide-react';

// --- Mock Data ---
const INITIAL_DATA = {
basics: {
name: "Shem Yu",
label: "Senior Software Engineer",
email: "shem.yu@example.com",
phone: "+886 912 345 678",
website: "github.com/shemyu",
location: "Taipei, Taiwan",
summary: "Product-minded engineer focused on building high-performance web applications. Expert in optimizing latency
and scaling distributed systems."
},
work: [
{
id: 1,
company: "Tech Corp",
position: "Senior Backend Engineer",
startDate: "2023-01",
endDate: "Present",
summary: "Leading the core infrastructure team to migrate legacy monolith to microservices.",
highlights: [
"Optimized API latency by 50% (200ms → 100ms) through Redis caching strategies and query optimization.",
"Architected and deployed a scalable event-driven notification system handling 1M+ daily events.",
"Mentored 3 junior developers to promotion within 12 months."
]
},
{
id: 2,
company: "Startup Inc",
position: "Full Stack Developer",
startDate: "2020-06",
endDate: "2022-12",
summary: "First engineer hire, built the MVP from scratch to Series A.",
highlights: [
"Built the entire frontend using React/TypeScript and established CI/CD pipelines.",
"Managed AWS infrastructure (ECS, RDS, S3) using Terraform.",
"Reduced build times by 40% by optimizing Webpack configurations."
]
},
{
id: 3,
company: "Legacy Systems",
position: "Junior Engineer",
startDate: "2018-09",
endDate: "2020-05",
summary: "Maintained internal tooling and reporting dashboards.",
highlights: [
"Refactored legacy Java codebase to improve test coverage from 40% to 85%.",
"Automated weekly reporting generation, saving 5 hours of manual work per week."
]
}
],
education: [
{ institution: "National Taiwan University", area: "Computer Science", degree: "B.S.", startDate: "2014", endDate:
"2018" }
],
skills: [
"Python (FastAPI)", "Go", "TypeScript", "React", "Docker", "Kubernetes", "AWS", "PostgreSQL", "Redis", "Terraform"
]
};

// --- Components ---

const Sidebar = ({ activeTab, setActiveTab, isDirty }) => {
const navItems = [
{ id: 'editor', icon: Layout, label: 'Editor' },
{ id: 'ai', icon: Wand2, label: 'AI Tailor' },
{ id: 'settings', icon: GitBranch, label: 'Version Control' },
];

return (
<div
    className="w-16 flex flex-col items-center py-6 bg-zinc-950 border-r border-zinc-800 h-screen select-none z-20 print:hidden">
    <div className="mb-8 p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg shadow-indigo-500/20">
        <span className="font-mono font-bold text-white text-lg">SY</span>
    </div>
    <div className="flex flex-col gap-4 w-full px-2">
        {navItems.map((item) => (
        <button key={item.id} onClick={()=> setActiveTab(item.id)}
            className={`
            p-3 rounded-xl transition-all duration-200 group relative flex justify-center
            ${activeTab === item.id
            ? 'bg-zinc-800 text-white'
            : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'}
            `}
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

// ... (Input Components remain same as v1) ...
const StyledInput = ({ label, value, onChange, placeholder, className = "" }) => (
<div className={`flex flex-col gap-1.5 ${className}`}>
    <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider font-mono">{label}</label>
    <input type="text" value={value} onChange={onChange} placeholder={placeholder}
        className="bg-zinc-900 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all placeholder-zinc-600 font-sans" />
</div>
);
const StyledTextArea = ({ label, value, onChange, placeholder, rows = 3 }) => (
<div className="flex flex-col gap-1.5">
    <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider font-mono">{label}</label>
    <textarea value={value} onChange={onChange} placeholder={placeholder} rows={rows}
        className="bg-zinc-900 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all placeholder-zinc-600 font-sans resize-none" />
</div>
);
const HighlightEditor = ({ highlights, onChange }) => {
const handleChange = (index, value) => { const newH = [...highlights]; newH[index] = value; onChange(newH); };
const handleKeyDown = (e, index) => {
if (e.key === 'Enter') { e.preventDefault(); const newH = [...highlights]; newH.splice(index + 1, 0, "");
onChange(newH); setTimeout(() => document.getElementById(`h-${index + 1}`)?.focus(), 0); }
else if (e.key === 'Backspace' && highlights[index] === "" && highlights.length > 1) { e.preventDefault(); const newH =
[...highlights]; newH.splice(index, 1); onChange(newH); setTimeout(() => document.getElementById(`h-${index -
1}`)?.focus(), 0); }
};
return (
<div className="flex flex-col gap-2 mt-2">
    <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider font-mono">Highlights
        (Enter/Backspace)</label>
    <div className="space-y-1">
        {highlights.map((point, index) => (
        <div key={index} className="flex items-start gap-2 group">
            <GripVertical size={14} className="mt-2.5 text-zinc-600 cursor-grab" />
            <input id={`h-${index}`} type="text" value={point} onChange={(e)=> handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, index)} className="flex-1 bg-transparent border-b border-zinc-800/50
            focus:border-indigo-500 py-2 px-1 text-sm text-zinc-300 focus:outline-none" />
            <button onClick={()=> {const newH = highlights.filter((_, i) => i !== index); onChange(newH)}}
                className="mt-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100">
                <Trash2 size={14} />
            </button>
        </div>
        ))}
    </div>
</div>
);
};

// --- Editor Section ---
const DataEditor = ({ data, setData, setIsDirty }) => {
// ... (Same logic as v1, abbreviated for brevity)
const [editingSection, setEditingSection] = useState('basics');
const [editingWorkId, setEditingWorkId] = useState(null);

if (editingSection === 'work' && editingWorkId !== null) {
const job = data.work.find(j => j.id === editingWorkId);
const updateJob = (field, val) => {
setData(prev => ({...prev, work: prev.work.map(i => i.id === job.id ? {...i, [field]: val} : i)})); setIsDirty(true);
};
return (
<div className="p-8 max-w-2xl mx-auto h-full overflow-y-auto animate-in slide-in-from-right-4">
    <button onClick={()=> setEditingWorkId(null)} className="text-zinc-500 hover:text-white flex items-center gap-2
        mb-6">
        <ArrowLeft size={16} /> Back
    </button>
    <div className="space-y-6">
        <StyledInput label="Company" value={job.company} onChange={e=> updateJob('company', e.target.value)} />
            <div className="grid grid-cols-2 gap-4">
                <StyledInput label="Position" value={job.position} onChange={e=> updateJob('position', e.target.value)}
                    /><StyledInput label="Dates" value={job.startDate} onChange={e=> updateJob('startDate',
                        e.target.value)} />
            </div>
            <StyledTextArea label="Summary" value={job.summary} onChange={e=> updateJob('summary', e.target.value)} />
                <HighlightEditor highlights={job.highlights} onChange={h=> updateJob('highlights', h)} />
    </div>
</div>
)
}

return (
<div className="p-8 max-w-2xl mx-auto h-full overflow-y-auto">
    <h1 className="text-2xl font-bold text-white mb-8">Data Editor</h1>
    <div className="space-y-6">
        <StyledInput label="Name" value={data.basics.name} onChange={e=> {setData(p=>({...p, basics: {...p.basics, name:
            e.target.value}})); setIsDirty(true)}} />
            <StyledTextArea label="Summary" value={data.basics.summary} onChange={e=> {setData(p=>({...p, basics:
                {...p.basics, summary: e.target.value}})); setIsDirty(true)}} />
                <div className="h-px bg-zinc-800" />
                <div className="flex justify-between items-center">
                    <h3 className="text-sm font-bold text-indigo-400 uppercase">Work Experience</h3><button
                        onClick={()=> {setEditingSection('work'); setEditingWorkId(null)}} className="text-xs
                        bg-zinc-800 px-3 py-1 rounded hover:text-white">Edit List</button>
                </div>
                {data.work.map(j => (
                <div key={j.id} onClick={()=> {setEditingSection('work'); setEditingWorkId(j.id)}}
                    className="bg-zinc-900 border border-zinc-800 p-4 rounded hover:border-zinc-600 cursor-pointer">
                    <div className="font-bold text-white">{j.company}</div>
                    <div className="text-xs text-zinc-500">{j.position}</div>
                </div>
                ))}
    </div>
</div>
);
};

// --- NEW: AI Tailor with Multi-Output Concept ---
const AITailor = ({ onApply }) => {
const [jd, setJd] = useState('');
const [step, setStep] = useState('input'); // input, processing, review
const [mode, setMode] = useState('tailor'); // tailor, condense

const handleProcess = () => {
if (!jd) return;
setStep('processing');
setTimeout(() => {
setStep('review');
}, 2000);
};

return (
<div className="p-8 max-w-2xl mx-auto h-full flex flex-col">
    <div className="mb-6">
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Wand2 className="text-indigo-500" /> AI Command Center
        </h1>
        <p className="text-zinc-500 text-sm mt-1">Paste a JD to generate tailored content and optimized layouts.</p>
    </div>

    {step === 'input' && (
    <div className="flex-1 flex flex-col gap-4 animate-in fade-in">
        <div className="flex gap-4 mb-2">
            <button onClick={()=> setMode('tailor')}
                className={`flex-1 py-3 rounded-lg border text-sm font-medium transition-all ${mode === 'tailor' ?
                'bg-indigo-500/10 border-indigo-500 text-indigo-400' : 'bg-zinc-900 border-zinc-800 text-zinc-500
                hover:border-zinc-700'}`}
                >
                <Wand2 size={16} className="inline mr-2 mb-0.5" />
                Tailor to Keywords
            </button>
            <button onClick={()=> setMode('condense')}
                className={`flex-1 py-3 rounded-lg border text-sm font-medium transition-all ${mode === 'condense' ?
                'bg-indigo-500/10 border-indigo-500 text-indigo-400' : 'bg-zinc-900 border-zinc-800 text-zinc-500
                hover:border-zinc-700'}`}
                >
                <Minimize2 size={16} className="inline mr-2 mb-0.5" />
                Auto-Fit Single Page
            </button>
        </div>

        <textarea value={jd} onChange={(e)=> setJd(e.target.value)}
            placeholder="Paste raw Job Description text here..."
            className="flex-1 w-full bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-sm text-zinc-300 focus:ring-2 focus:ring-indigo-500 resize-none font-mono"
          />
          <button
            onClick={handleProcess}
            disabled={!jd}
            className="w-full py-4 bg-white text-black rounded-lg font-bold hover:bg-zinc-200 transition-colors shadow-lg shadow-white/10"
          >
            Generate Optimized Resume
          </button>
        </div>
      )}

      {step === 'processing' && (
        <div className="flex-1 flex flex-col items-center justify-center gap-6 animate-in fade-in">
            <div className="w-16 h-16 border-4 border-zinc-800 border-t-indigo-500 rounded-full animate-spin"></div>
            <div className="text-center space-y-2">
                <h3 className="text-white font-bold text-lg">Analyzing Requirements...</h3>
                <p className="text-zinc-500 text-sm">Matching keywords: "Distributed Systems", "Redis", "Leadership"</p>
                <p className="text-zinc-500 text-sm">Refactoring bullet points for impact...</p>
            </div>
        </div>
      )}

      {step === 'review' && (
        <div className="flex-1 flex flex-col animate-in slide-in-from-bottom-4">
           <div className="bg-zinc-900/50 border border-green-900/50 rounded-lg p-6 mb-6">
             <div className="flex items-center gap-2 text-green-400 mb-4">
                <CheckCircle2 size={20} />
                <span className="font-bold text-lg">Optimization Complete</span>
             </div>
             <div className="space-y-3 text-sm text-zinc-400">
                <p>• Rewrote summary to emphasize <span className="text-green-400">Microservices migration</span>.</p>
                <p>• Prioritized "Tech Corp" highlights regarding latency reduction.</p>
                {mode === 'condense' && <p>• Trimmed 4 bullet points to fit "Bible Format" (1 Page).</p>}
             </div>
           </div>
           
           <div className="mt-auto flex flex-col gap-3">
              <p className="text-center text-zinc-500 text-xs">Check the Preview Pane to switch between layouts.</p>
              <div className="flex gap-3">
                <button onClick={onApply} className="flex-1 bg-green-600 hover:bg-green-500 text-white py-3 rounded-lg font-bold transition-colors">Apply to Editor</button>
                <button onClick={() => setStep('input')} className="px-6 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium">Discard</button>
              </div>
           </div>
        </div>
      )}
    </div>
  );
};

// --- Templates ---

// 1. Template: Compact (Engineering Bible / Jake's Resume Style)
const CompactTemplate = ({ data }) => (
  <div className="font-serif text-black p-[10mm]">
    {/* Header */}
    <div className="text-center mb-4">
      <h1 className="text-2xl font-bold uppercase tracking-wide">{data.basics.name}</h1>
      <div className="text-sm mt-1 space-x-2">
        <span>{data.basics.phone}</span><span>|</span>
        <a href={`mailto:${data.basics.email}`} className="text-black">{data.basics.email}</a><span>|</span>
        <a href={`https://${data.basics.website}`} className="text-black">{data.basics.website}</a>
        {data.basics.location && <><span>|</span><span>{data.basics.location}</span></>}
      </div>
    </div>

    {/* Education */}
    <div className="mb-4">
      <h2 className="font-bold text-sm uppercase border-b border-black mb-2">Education</h2>
      {data.education.map((edu, i) => (
         <div key={i} className="flex justify-between text-sm">
            <div><span className="font-bold">{edu.institution}</span> — {edu.area}</div>
            <div className="font-serif">{edu.startDate} – {edu.endDate}</div>
         </div>
      ))}
    </div>

    {/* Experience */}
    <div className="mb-4">
      <h2 className="font-bold text-sm uppercase border-b border-black mb-2">Experience</h2>
      <div className="space-y-3">
        {data.work.map((job) => (
          <div key={job.id}>
            <div className="flex justify-between items-baseline mb-0.5">
              <div className="text-sm"><span className="font-bold">{job.company}</span> | {job.position}</div>
              <span className="text-sm font-serif">{job.startDate} – {job.endDate}</span>
            </div>
            <ul className="list-disc list-outside ml-5 text-sm leading-snug space-y-0.5">
              {job.highlights.map((h, i) => <li key={i}>{h}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </div>

    {/* Skills */}
    <div>
       <h2 className="font-bold text-sm uppercase border-b border-black mb-2">Technical Skills</h2>
       <p className="text-sm"><span className="font-bold">Languages & Tools:</span> {data.skills.join(', ')}</p>
    </div>
  </div>
);

// 2. Template: Modern (Comprehensive)
const ModernTemplate = ({ data }) => (
  <div className="font-sans text-gray-800 p-[15mm]">
    <header className="border-b-2 border-gray-800 pb-6 mb-8">
      <h1 className="text-5xl font-bold text-gray-900 tracking-tight mb-2">{data.basics.name}</h1>
      <p className="text-xl text-indigo-700 font-medium">{data.basics.label}</p>
      <div className="flex gap-4 mt-4 text-sm text-gray-600 font-mono">
        <span>{data.basics.email}</span>
        <span>•</span>
        <span>{data.basics.phone}</span>
        <span>•</span>
        <span>{data.basics.website}</span>
      </div>
    </header>

    <div className="grid grid-cols-[2fr_1fr] gap-10">
      <main>
        <section className="mb-8">
          <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4 flex items-center gap-2">
            <span className="w-2 h-2 bg-indigo-500 rounded-full"></span> Professional Experience
          </h2>
          <div className="space-y-8">
            {data.work.map((job) => (
              <div key={job.id} className="relative pl-6 border-l-2 border-gray-100">
                <div className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-gray-300"></div>
                <div className="mb-2">
                  <h3 className="font-bold text-lg text-gray-900">{job.position}</h3>
                  <div className="text-indigo-600 font-medium">{job.company}</div>
                  <div className="text-xs text-gray-500 font-mono mt-1">{job.startDate} – {job.endDate}</div>
                </div>
                <p className="text-sm text-gray-600 mb-3 italic">{job.summary}</p>
                <ul className="space-y-2">
                  {job.highlights.map((point, idx) => (
                    <li key={idx} className="text-sm text-gray-700 leading-relaxed flex items-start gap-2">
                       <span className="text-indigo-400 mt-1.5 text-[8px]">▶</span>
                       {point}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </main>

      <aside>
         <section className="mb-8">
           <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">About</h2>
           <p className="text-sm text-gray-600 leading-relaxed">{data.basics.summary}</p>
         </section>
         <section>
           <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">Stack</h2>
           <div className="flex flex-wrap gap-2">
             {data.skills.map((skill, i) => (
               <span key={i} className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-xs font-bold border border-gray-200">
                 {skill}
               </span>
             ))}
           </div>
         </section>
      </aside>
    </div>
  </div>
);

// --- Preview Pane with Template Switcher ---
const PreviewPane = ({ data, template, setTemplate }) => {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="bg-zinc-900 h-full flex flex-col border-l border-zinc-800 relative">
      {/* Top Toolbar */}
      <div className="h-12 border-b border-zinc-800 flex items-center justify-between px-4 bg-zinc-950/80 backdrop-blur print:hidden">
        <div className="flex items-center gap-1 bg-zinc-900 rounded p-1 border border-zinc-800">
            <button 
              onClick={() => setTemplate('compact')}
              className={`flex items-center gap-2 px-3 py-1 rounded text-xs font-medium transition-all ${template === 'compact' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
                <Minimize2 size={12} /> The Bible (Compact)
            </button>
            <button 
              onClick={() => setTemplate('modern')}
              className={`flex items-center gap-2 px-3 py-1 rounded text-xs font-medium transition-all ${template === 'modern' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
                <Layers size={12} /> Modern Full
            </button>
        </div>
        <button 
            onClick={handlePrint}
            className="flex items-center gap-2 text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded transition-colors shadow-lg shadow-indigo-500/20"
        >
            <Download size={12} /> Download PDF
        </button>
      </div>
      
      {/* Scrollable Area */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-8 flex justify-center bg-zinc-900 scrollbar-hide">
        {/* A4 Container */}
        <div className="print:w-full print:h-full print:absolute print:top-0 print:left-0 print:m-0 print:z-50 print:block">
            <div 
                className="bg-white shadow-2xl transition-all duration-300 print:shadow-none"
                style={{ 
                    width: '210mm', 
                    minHeight: '297mm',
                    // Scale handled by CSS/Parent in screen view, reset in print view
                }}
            >
                {template === 'compact' ? <CompactTemplate data={data} /> : <ModernTemplate data={data} />}
            </div>
        </div>
      </div>
    </div>
  );
};

// --- Main App ---
const App = () => {
  const [data, setData] = useState(INITIAL_DATA);
  const [activeTab, setActiveTab] = useState('editor');
  const [isDirty, setIsDirty] = useState(false);
  const [template, setTemplate] = useState('compact'); // 'compact' or 'modern'

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-200 font-sans overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} isDirty={isDirty} />
      
      <div className="flex-1 flex flex-col min-w-[500px] border-r border-zinc-800 relative print:hidden">
        {/* Editor Header */}
        <div className="h-12 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-950/50 backdrop-blur">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
            <FileText size={14} /> <span>resume.yaml</span> {isDirty && <span className="text-amber-500 ml-2">* Modified</span>}
          </div>
          {isDirty && <button onClick={() => setIsDirty(false)} className="text-xs bg-zinc-800 hover:bg-zinc-700 text-white px-3 py-1.5 rounded flex items-center gap-2"><Save size={12} /> Save</button>}
        </div>

        <div className="flex-1 overflow-hidden relative">
          {activeTab === 'editor' && <DataEditor data={data} setData={setData} setIsDirty={setIsDirty} />}
          {activeTab === 'ai' && <AITailor onApply={() => { setActiveTab('editor'); setIsDirty(true); }} />}
          {activeTab === 'settings' && <div className="p-10 text-center text-zinc-500">Git Integration Mockup</div>}
        </div>
      </div>

      <div className="w-[50%] hidden xl:block print:block print:w-auto print:absolute print:inset-0">
        <PreviewPane data={data} template={template} setTemplate={setTemplate} />
      </div>
      
      {/* Global CSS for Print specific overrides */}
      <style>{`
        @media print {
            body * { visibility: hidden; }
            .print\\:block, .print\\:block * { visibility: visible; }
            .print\\:hidden { display: none !important; }
            .print\\:absolute { position: absolute; left: 0; top: 0; width: 100%; }
        }
      `}</style>
    </div>
  );
};

export default App;