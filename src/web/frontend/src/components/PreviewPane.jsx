import React from 'react';
import { Minimize2, Layers, Download } from 'lucide-react';

const formatLocation = (loc) => {
    if (!loc) return null;
    if (typeof loc === 'string') return loc;
    return [loc.city, loc.region, loc.countryCode].filter(Boolean).join(', ');
};

const CompactTemplate = ({ data }) => (
    <div className="font-serif text-black p-[10mm]">
        <div className="text-center mb-4">
            <h1 className="text-2xl font-bold uppercase tracking-wide">{data.basics?.name}</h1>
            <div className="text-sm mt-1 space-x-2">
                <span>{data.basics?.phone}</span><span>|</span>
                <a href={`mailto:${data.basics?.email}`} className="text-black">{data.basics?.email}</a><span>|</span>
                <a href={`https://${data.basics?.website}`} className="text-black">{data.basics?.website}</a>
                {formatLocation(data.basics?.location) && <><span>|</span><span>{formatLocation(data.basics?.location)}</span></>}
            </div>
        </div>

        <div className="mb-4">
            <h2 className="font-bold text-sm uppercase border-b border-black mb-2">Education</h2>
            {data.education?.map((edu, i) => (
                <div key={i} className="flex justify-between text-sm">
                    <div><span className="font-bold">{edu.institution}</span> — {edu.area}</div>
                    <div className="font-serif">{edu.startDate} – {edu.endDate}</div>
                </div>
            ))}
        </div>

        <div className="mb-4">
            <h2 className="font-bold text-sm uppercase border-b border-black mb-2">Experience</h2>
            <div className="space-y-3">
                {data.work?.map((job) => (
                    <div key={job.id || Math.random()}>
                        <div className="flex justify-between items-baseline mb-0.5">
                            <div className="text-sm"><span className="font-bold">{job.company}</span> | {job.position}</div>
                            <span className="text-sm font-serif">{job.startDate} – {job.endDate}</span>
                        </div>
                        <ul className="list-disc list-outside ml-5 text-sm leading-snug space-y-0.5">
                            {job.highlights?.map((h, i) => <li key={i}>{h}</li>)}
                        </ul>
                    </div>
                ))}
            </div>
        </div>

        <div>
            <h2 className="font-bold text-sm uppercase border-b border-black mb-2">Technical Skills</h2>
            <div className="text-sm">
                <span className="font-bold">Languages & Tools:</span>
                {data.skills?.map(s => typeof s === 'object' ? (s.keywords?.join(', ') || s.name) : s).join(', ')}
            </div>
        </div>
    </div>
);

const ModernTemplate = ({ data }) => {
    // Helper to flatten skills for display
    const flatSkills = React.useMemo(() => {
        if (!data.skills) return [];
        return data.skills.flatMap(s => {
            if (typeof s === 'string') return [s];
            return s.keywords || [s.name];
        });
    }, [data.skills]);

    return (
        <div className="font-sans text-gray-800 p-[15mm]">
            <header className="border-b-2 border-gray-800 pb-6 mb-8">
                <h1 className="text-5xl font-bold text-gray-900 tracking-tight mb-2">{data.basics?.name}</h1>
                <p className="text-xl text-indigo-700 font-medium">{data.basics?.label}</p>
                <div className="flex gap-4 mt-4 text-sm text-gray-600 font-mono">
                    <span>{data.basics?.email}</span>
                    <span>•</span>
                    <span>{data.basics?.phone}</span>
                    <span>•</span>
                    <span>{data.basics?.website}</span>
                </div>
            </header>

            <div className="grid grid-cols-[2fr_1fr] gap-10">
                <main>
                    <section className="mb-8">
                        <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 bg-indigo-500 rounded-full"></span> Professional Experience
                        </h2>
                        <div className="space-y-8">
                            {data.work?.map((job) => (
                                <div key={job.id || Math.random()} className="relative pl-6 border-l-2 border-gray-100">
                                    <div className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-gray-300"></div>
                                    <div className="mb-2">
                                        <h3 className="font-bold text-lg text-gray-900">{job.position}</h3>
                                        <div className="text-indigo-600 font-medium">{job.company}</div>
                                        <div className="text-xs text-gray-500 font-mono mt-1">{job.startDate} – {job.endDate}</div>
                                    </div>
                                    <p className="text-sm text-gray-600 mb-3 italic">{job.summary}</p>
                                    <ul className="space-y-2">
                                        {job.highlights?.map((point, idx) => (
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

                    {
                        data.education && data.education.length > 0 && (
                            <section className="mb-8">
                                <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span> Education
                                </h2>
                                <div className="space-y-6">
                                    {data.education.map((edu, i) => (
                                        <div key={i} className="relative pl-6 border-l-2 border-gray-100">
                                            <div className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-gray-300"></div>
                                            <div>
                                                <h3 className="font-bold text-lg text-gray-900">{edu.institution}</h3>
                                                <div className="text-indigo-600 font-medium">{edu.studyType} in {edu.area}</div>
                                                <div className="text-xs text-gray-500 font-mono mt-1">{edu.startDate} – {edu.endDate}</div>
                                                {edu.score && <div className="text-sm text-gray-600 mt-1">Score: {edu.score}</div>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )
                    }
                </main >

                <aside>
                    <section className="mb-8">
                        <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">About</h2>
                        <p className="text-sm text-gray-600 leading-relaxed">{data.basics?.summary}</p>
                    </section>
                    <section>
                        <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">Stack</h2>
                        <div className="flex flex-wrap gap-2">
                            {flatSkills.map((skill, i) => (
                                <span key={i} className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-xs font-bold border border-gray-200">
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </section>
                </aside>
            </div >
        </div >
    );
};

export const PreviewPane = ({ data, template, setTemplate, onDownloadPDF }) => {
    const handlePrint = () => {
        window.print();
    };

    return (
        <div className="bg-zinc-900 h-full flex flex-col border-l border-zinc-800 relative print:border-none">
            <div className="h-12 border-b border-zinc-800 flex items-center justify-between px-4 bg-zinc-950/80 backdrop-blur print:hidden">
                <div className="flex items-center gap-1 bg-zinc-900 rounded p-1 border border-zinc-800">
                    <button onClick={() => setTemplate('compact')}
                        className={`flex items-center gap-2 px-3 py-1 rounded text-xs font-medium transition-all ${template === 'compact' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>
                        <Minimize2 size={12} /> Compact
                    </button>
                    <button onClick={() => setTemplate('modern')}
                        className={`flex items-center gap-2 px-3 py-1 rounded text-xs font-medium transition-all ${template === 'modern' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>
                        <Layers size={12} /> Modern
                    </button>
                </div>
                <button onClick={onDownloadPDF || handlePrint}
                    className="flex items-center gap-2 text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded transition-colors shadow-lg shadow-indigo-500/20">
                    <Download size={12} /> PDF
                </button>
            </div>

            <div className="flex-1 overflow-y-auto overflow-x-hidden p-8 flex justify-center bg-zinc-900 scrollbar-hide print:p-0 print:overflow-visible">
                <div className="print:fixed print:top-0 print:left-0 print:w-screen print:h-screen print:z-[9999] print:bg-white print:block">
                    <div className="bg-white shadow-2xl transition-all duration-300 print:shadow-none relative"
                        style={{ width: '210mm', minHeight: '297mm' }}>

                        {/* A4 Limit Guide - Visible in Preview, Hidden in Print */}
                        <div className="absolute top-[297mm] left-0 w-full border-b border-red-400 border-dashed opacity-50 pointer-events-none print:hidden flex items-end justify-end pb-1 pr-2">
                            <span className="text-[10px] text-red-400 font-mono uppercase">A4 Page Limit</span>
                        </div>

                        {template === 'compact' ? <CompactTemplate data={data} /> : <ModernTemplate data={data} />}
                    </div>
                </div>
            </div>
        </div>
    );
};
