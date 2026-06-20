import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity, ArrowRight, BookOpen, CalendarDays, CheckCircle2, ChevronLeft, CircleHelp, Clock3, Coins,
  Database, Download, FileDown, FileText, Globe2, Landmark, Layers3, Leaf, Library, LoaderCircle, Menu,
  Microscope, Moon, Newspaper, Printer, Radio, RefreshCw, ScrollText, Search, Send, Settings, ShieldCheck,
  Sparkles, Sun, Target, Upload, UploadCloud, UserRound, X
} from 'lucide-react';
import { api } from './api';

const categories = ['All', 'Polity', 'Governance', 'Economy', 'Environment', 'International Relations', 'Science & Technology', 'Security', 'Social Issues', 'Agriculture', 'Ethics', 'History', 'Geography'];
const categoryIcons = { Polity: Landmark, Governance: ShieldCheck, Economy: Coins, Environment: Leaf, 'Science & Technology': Microscope, 'International Relations': Globe2, Security: ShieldCheck, 'Social Issues': UserRound, Agriculture: Leaf, Ethics: ScrollText, History: ScrollText, Geography: Globe2 };
const categoryClasses = { Polity: 'purple', Governance: 'blue', Economy: 'amber', Environment: 'green', 'Science & Technology': 'blue', 'International Relations': 'cyan', Security: 'rose', 'Social Issues': 'purple', Agriculture: 'green', Ethics: 'amber', History: 'rose', Geography: 'cyan' };
const defaultProfile = { fullName: '', email: '', targetYear: '2027', optionalSubject: '', state: '', examType: 'Civil Services Examination' };

function displayName(profile) { return profile?.fullName?.trim() || 'Aspirant'; }
function initials(profile) {
  const name = displayName(profile);
  return name.split(/\s+/).slice(0, 2).map(x => x[0]).join('').toUpperCase();
}
function todayLabel() { return new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }); }

function Logo() {
  return <div className="logo"><div className="logo-mark flag-mark"><i/><i/><i/></div><div><b>UPSC<span>Brief</span></b><small>AI current affairs</small></div></div>;
}

function Sidebar({ page, setPage, open, close, profile }) {
  const links = [
    ['home', LayoutDashboardIcon, 'Overview'],
    ['dashboard', Newspaper, 'News feed'],
    ['categories', Library, 'Subjects'],
    ['questions', CircleHelp, 'Question bank'],
    ['admin', Upload, 'Admin sync'],
    ['profile', UserRound, 'Profile']
  ];
  return <><div className={`scrim ${open ? 'show' : ''}`} onClick={close}/><aside className={open ? 'open' : ''}>
    <div className="aside-top"><Logo/><button className="icon-btn mobile-only" onClick={close}><X size={20}/></button></div>
    <p className="nav-label">Workspace</p><nav>{links.map(([id, Icon, label]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { setPage(id); close(); }}><Icon size={19}/><span>{label}</span>{id === 'questions' && <i>New</i>}</button>)}</nav>
    <div className="study-card"><span><Target size={18}/></span><b>Daily study goal</b><p>4 of 6 briefs completed</p><div className="progress"><i/></div><small>Keep the momentum going.</small></div>
    <div className="profile"><div>{initials(profile)}</div><span><b>{displayName(profile)}</b><small>{profile.examType || 'UPSC Aspirant'}</small></span><button aria-label="Edit profile" onClick={() => setPage('profile')}><Settings size={17}/></button></div>
  </aside></>;
}

function LayoutDashboardIcon(props) {
  return <Activity {...props}/>;
}

function Header({ dark, toggleDark, search, setSearch, menu }) {
  return <header><button className="icon-btn mobile-only" onClick={menu}><Menu/></button><div className="global-search"><Search size={19}/><input aria-label="Search current affairs" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search news, topics or keywords..."/><kbd>Ctrl K</kbd></div><div className="header-actions"><button className="theme-toggle" aria-label="Toggle theme" onClick={toggleDark}>{dark ? <Sun size={19}/> : <Moon size={19}/>}</button><span className="today"><CalendarDays size={18}/> {todayLabel()}</span></div></header>;
}

function CategoryBadge({ category }) {
  const Icon = categoryIcons[category] || BookOpen;
  return <span className={`badge ${categoryClasses[category] || 'blue'}`}><Icon size={13}/>{category}</span>;
}

function ArticleCard({ article, onOpen }) {
  return <article className="article-card" onClick={() => onOpen(article)} tabIndex="0">
    <div className="card-top"><CategoryBadge category={article.category}/><span className="read-time"><Clock3 size={13}/> 4 min read</span></div>
    <h3>{article.title}</h3><p>{article.shortSummary || article.summary}</p>
    <div className="keywords">{(article.keywords || []).slice(0, 3).map(k => <span key={k}>#{k.replaceAll(' ', '')}</span>)}</div>
    <div className="card-footer"><span><b>{article.source}</b><small>{new Date(article.date + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</small></span><button aria-label="Read summary"><ArrowRight size={18}/></button></div>
  </article>;
}

function EmptyState() { return <div className="empty"><Search size={34}/><h3>No briefs found</h3><p>Try a different keyword or category.</p></div>; }

function SectionTitle({ title, subtitle, action }) {
  return <div className="section-title"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action && <button onClick={action}>View all <ArrowRight size={16}/></button>}</div>;
}

function Home({ articles, stats, openArticle, setPage, profile }) {
  const featured = articles[0];
  return <div className="page"><section className="welcome"><div><span className="eyebrow"><Sparkles size={14}/> AI-curated for UPSC</span><h1>Good evening, {displayName(profile)}</h1><p>Here's what matters today, distilled, classified, and ready to revise.</p></div><div className="streak"><span>7</span><div><b>day streak</b><small>Personal best: 12 days</small></div></div></section>
    <section className="metrics"><Metric icon={Newspaper} tone="blue" value={stats.todayArticles || stats.articles || articles.length} label="Today's briefs" note="Live"/><Metric icon={CircleHelp} tone="purple" value={stats.questions || 0} label="Practice questions" note="Ready"/><Metric icon={FileText} tone="green" value={stats.pdfUploads || 0} label="PDF uploads" note="Parsed"/><Metric icon={Layers3} tone="amber" value={Object.keys(stats.categories || {}).length} label="Subjects covered" note="Balanced"/></section>
    {featured && <section className="featured"><div className="featured-copy"><span className="section-kicker">Editor's pick</span><CategoryBadge category={featured.category}/><h2>{featured.title}</h2><p>{featured.shortSummary || featured.summary}</p><button className="primary" onClick={() => openArticle(featured)}>Read complete brief <ArrowRight size={17}/></button></div><div className="feature-visual"><Globe2/><div className="orbit one"/><div className="orbit two"/><span>AI<br/>BRIEF</span></div></section>}
    <SectionTitle title="Latest current affairs" subtitle="Fresh briefs selected for your syllabus" action={() => setPage('dashboard')}/><div className="article-grid">{articles.slice(1, 4).map(a => <ArticleCard key={a._id} article={a} onOpen={openArticle}/>)}</div>
  </div>;
}

function Metric({ icon: Icon, tone, value, label, note }) {
  return <div><span className={`metric-icon ${tone}`}><Icon/></span><div><b>{value}</b><small>{label}</small></div><em>{note}</em></div>;
}

function Dashboard({ articles, category, setCategory, date, setDate, openArticle }) {
  return <div className="page"><div className="page-heading"><span className="eyebrow"><Newspaper size={14}/> Daily intelligence</span><h1>News dashboard</h1><p>High-signal current affairs mapped to the Civil Services syllabus.</p></div><div className="filter-row"><div className="chips">{categories.map(c => <button className={category === c ? 'active' : ''} onClick={() => setCategory(c)} key={c}>{c}</button>)}</div><label className="date-filter"><CalendarDays size={16}/><input type="date" aria-label="Archive date" value={date} onChange={e => setDate(e.target.value)}/></label></div><div className="results-label"><b>{articles.length} briefs</b><span>Sorted by latest</span></div>{articles.length ? <div className="article-grid">{articles.map(a => <ArticleCard key={a._id} article={a} onOpen={openArticle}/>)}</div> : <EmptyState/>}</div>;
}

function Categories({ articles, setCategory, setPage }) {
  return <div className="page"><div className="page-heading"><span className="eyebrow"><Library size={14}/> GS syllabus map</span><h1>Explore by subject</h1><p>Build depth one General Studies theme at a time.</p></div><div className="category-grid">{categories.slice(1).map(category => { const Icon = categoryIcons[category] || BookOpen; const count = articles.filter(a => a.category === category).length; return <button key={category} onClick={() => { setCategory(category); setPage('dashboard'); }} className={`category-tile ${categoryClasses[category] || 'blue'}`}><span><Icon/></span><div><h3>{category}</h3><p>{count} curated brief{count !== 1 ? 's' : ''}</p></div><ArrowRight/></button>; })}</div></div>;
}

function Questions({ articles }) {
  const [selected, setSelected] = useState(null);
  const questions = articles.flatMap(a => (a.mcqs || []).map((q, i) => ({ ...q, article: a, id: `${a._id}-${i}` })));
  return <div className="page"><div className="page-heading"><span className="eyebrow"><CircleHelp size={14}/> Active recall</span><h1>Question bank</h1><p>Prelims, Mains, and PYQ links generated from daily news and uploaded PDFs.</p></div><div className="export-row"><a className="download" href="/api/question-bank/export?format=pdf"><Download size={16}/> Export PDF</a><a className="download" href="/api/question-bank/export?format=word"><FileDown size={16}/> Export Word</a><button className="download" onClick={() => window.open('/api/question-bank/export?format=print', '_blank')}><Printer size={16}/> Print</button></div><div className="question-layout"><div className="question-list">{questions.map((q, i) => <article className="question-card" key={q.id}><div><span>{q.type || `Question ${i + 1}`}</span><CategoryBadge category={q.article.category}/></div><h3>{q.question}</h3><div className="options">{(q.options || []).map(opt => <button className={selected?.id === q.id ? (opt === q.answer ? 'correct' : 'muted') : ''} onClick={() => setSelected(q)} key={opt}>{opt}</button>)}</div>{selected?.id === q.id && <p className="explanation"><CheckCircle2 size={17}/><span><b>Answer: {q.answer}</b>{q.explanation}</span></p>}</article>)}</div><aside className="practice-panel"><Target/><h3>Mains practice</h3><p>Answer in 150 or 250 words. Focus on directive, structure, and a forward-looking conclusion.</p>{articles.slice(0, 3).map(a => <div key={a._id}><CategoryBadge category={a.category}/><p>{(a.mainsQuestions?.[0]?.question) || a.practiceQuestions?.[0]}</p></div>)}</aside></div></div>;
}

function Detail({ article, back }) {
  if (!article) return null;
  const entities = [['Schemes', article.governmentSchemes], ['Articles', article.constitutionalArticles], ['Committees', article.committees], ['Reports', article.reports], ['Organizations', article.internationalOrganizations]];
  return <div className="page detail"><button className="back" onClick={back}><ChevronLeft/> Back to briefs</button><div className="detail-head"><CategoryBadge category={article.category}/><h1>{article.title}</h1><div><b>{article.source}</b><span>|</span><span>{new Date(article.date + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</span><span>|</span><span>{article.sourceType || 'news'}</span></div><a className="download" href={`/api/articles/${article._id}/pdf`}><FileDown size={17}/> Download PDF</a></div><div className="detail-layout"><main><section className="summary-box"><span><Sparkles/> 100-word summary</span><p>{article.shortSummary || article.summary}</p></section><section className="content-section"><h2>Detailed summary</h2><p>{article.detailedSummary || article.content}</p></section><section className="content-section"><h2>Key facts</h2><ul className="fact-list">{(article.keyFacts || []).map(f => <li key={f}>{f}</li>)}</ul></section><section className="content-section"><h2>Terms and entities</h2><div className="entity-grid">{entities.map(([label, values]) => <div key={label}><b>{label}</b>{values?.length ? values.map(v => <span key={v}>{v}</span>) : <small>Not detected</small>}</div>)}</div></section><section className="content-section"><h2>Related PYQs</h2>{(article.pyqs || []).map(q => <p className="mini-q" key={`${q.year}-${q.question}`}><b>UPSC {q.year}</b> {q.question}<br/><small>{q.answerHint}</small></p>)}</section></main><aside className="exam-panel"><span><Target/> Exam lens</span><h3>Mains questions</h3>{(article.mainsQuestions || []).map(q => <p className="mini-q" key={q.question}><b>{q.paper} | {q.directive} | {q.wordLimit} words</b>{q.question}</p>)}<hr/><h3>Quick revision</h3><div className="keyword-cloud">{(article.importantTerms || article.keywords || []).map(k => <span key={k}>{k}</span>)}</div></aside></div></div>;
}

function ProfilePage({ profile, setProfile, setPage }) {
  const [draft, setDraft] = useState(profile);
  const [status, setStatus] = useState(null);
  useEffect(() => setDraft(profile), [profile]);
  async function save(e) {
    e.preventDefault();
    setStatus({ type: 'loading', message: 'Saving profile...' });
    try {
      const saved = await api('/profile', { method: 'PUT', body: JSON.stringify(draft) });
      localStorage.setItem('profile', JSON.stringify(saved));
      setProfile(saved);
      setStatus({ type: 'success', message: 'Profile updated across the app.' });
      setPage('home');
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    }
  }
  return <div className="page"><div className="page-heading"><span className="eyebrow"><UserRound size={14}/> Editable profile</span><h1>Aspirant profile</h1><p>Your name and exam details power the dashboard, sidebar, and generated study context.</p></div><div className="admin-layout"><form className="upload-form profile-form" onSubmit={save}><div className="profile-avatar">{initials(draft)}</div><label>Full name<input value={draft.fullName || ''} onChange={e => setDraft({ ...draft, fullName: e.target.value })} placeholder="Aspirant"/></label><label>Email address<input type="email" value={draft.email || ''} onChange={e => setDraft({ ...draft, email: e.target.value })} placeholder="you@example.com"/></label><div className="form-row"><label>UPSC target year<input value={draft.targetYear || ''} onChange={e => setDraft({ ...draft, targetYear: e.target.value })} placeholder="2027"/></label><label>Optional subject<input value={draft.optionalSubject || ''} onChange={e => setDraft({ ...draft, optionalSubject: e.target.value })} placeholder="e.g. PSIR"/></label></div><div className="form-row"><label>State<input value={draft.state || ''} onChange={e => setDraft({ ...draft, state: e.target.value })} placeholder="e.g. Karnataka"/></label><label>Exam type<input value={draft.examType || ''} onChange={e => setDraft({ ...draft, examType: e.target.value })} placeholder="Civil Services Examination"/></label></div><button className="primary submit"><CheckCircle2 size={16}/> Save profile</button>{status && <p className={`ingestion-status ${status.type}`}>{status.type === 'loading' ? <LoaderCircle className="spin"/> : status.type === 'success' ? <CheckCircle2/> : <X/>}{status.message}</p>}</form><aside className="pipeline"><h3>Profile preview</h3><div><span>{initials(draft)}</span><p><b>{displayName(draft)}</b><small>{draft.examType || 'UPSC Aspirant'}</small></p></div><div><span>TY</span><p><b>{draft.targetYear || '2027'}</b><small>Target year</small></p></div><div><span>OP</span><p><b>{draft.optionalSubject || 'Not set'}</b><small>Optional subject</small></p></div></aside></div></div>;
}

function Admin({ onCreated, stats, refreshStats }) {
  const today = new Date().toISOString().slice(0, 10);
  const [tab, setTab] = useState('pdf');
  const [manual, setManual] = useState({ title: '', source: '', date: today, content: '' });
  const [pdf, setPdf] = useState({ file: null, source: '', date: today });
  const [syncDate, setSyncDate] = useState(today);
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState(null);
  useEffect(() => { api('/ingestion/status').then(setConfig).catch(() => {}); }, []);

  async function submitManual(e) {
    e.preventDefault(); setStatus({ type: 'loading', message: 'Analysing article...' });
    try { const result = await api('/articles', { method: 'POST', body: JSON.stringify(manual) }); setStatus({ type: 'success', message: 'Brief created successfully.' }); onCreated(result); refreshStats(); }
    catch (err) { setStatus({ type: 'error', message: err.message }); }
  }
  async function submitPdf(e) {
    e.preventDefault();
    if (!pdf.file) { setStatus({ type: 'error', message: 'Choose a newspaper PDF first.' }); return; }
    setStatus({ type: 'loading', message: 'Extracting and analysing the newspaper...' });
    const body = new FormData(); body.append('newspaper', pdf.file); body.append('source', pdf.source); body.append('date', pdf.date);
    try { const response = await fetch('/api/ingestion/pdf', { method: 'POST', body }); const result = await response.json(); if (!response.ok) throw new Error(result.error); setStatus({ type: 'success', message: `${result.createdCount} briefs created from ${result.pages} pages using ${result.engine}.` }); onCreated(result.created); refreshStats(); }
    catch (err) { setStatus({ type: 'error', message: err.message }); }
  }
  async function syncNews() {
    setStatus({ type: 'loading', message: 'Collecting news, removing duplicates, and generating briefs...' });
    try { const result = await api('/ingestion/news', { method: 'POST', body: JSON.stringify({ date: syncDate }) }); setConfig(result.syncStatus || config); setStatus({ type: 'success', message: `${result.createdCount} new briefs added; ${result.skippedCount} duplicates or irrelevant items skipped.` }); onCreated(result.created); refreshStats(); }
    catch (err) { setStatus({ type: 'error', message: err.message }); }
  }

  return <div className="page"><div className="page-heading"><span className="eyebrow"><Upload size={14}/> Automated ingestion</span><h1>Build today's briefing</h1><p>Import a full newspaper, sync current affairs, or add one article manually.</p></div>
    <section className="monitor-grid"><Metric icon={Database} tone="blue" value={stats.articles || 0} label="Total articles" note="DB"/><Metric icon={Newspaper} tone="purple" value={stats.todayArticles || 0} label="Today's articles" note="Daily"/><Metric icon={CircleHelp} tone="green" value={stats.questions || 0} label="Questions generated" note="AI"/><Metric icon={Activity} tone="amber" value={config?.status || stats.sync?.status || 'idle'} label="Sync status" note="API"/></section>
    <div className="ingestion-tabs">{[['pdf', UploadCloud, 'Newspaper PDF'], ['sync', Radio, 'Daily news sync'], ['manual', FileText, 'Single article']].map(([id, Icon, label]) => <button className={tab === id ? 'active' : ''} onClick={() => { setTab(id); setStatus(null); }} key={id}><Icon/>{label}</button>)}</div>
    <div className="admin-layout"><div className="upload-form">
      {tab === 'pdf' && <form onSubmit={submitPdf}><div className="drop-zone"><UploadCloud/><h3>Upload the complete newspaper</h3><p>Searchable PDF up to {config?.pdfLimitMb || 25} MB</p><label className="file-picker"><input type="file" accept="application/pdf,.pdf" onChange={e => setPdf({ ...pdf, file: e.target.files[0] })}/>{pdf.file ? pdf.file.name : 'Choose PDF file'}</label></div><div className="form-row"><label>Newspaper name<input required value={pdf.source} onChange={e => setPdf({ ...pdf, source: e.target.value })} placeholder="e.g. The Hindu"/></label><label>Edition date<input type="date" value={pdf.date} onChange={e => setPdf({ ...pdf, date: e.target.value })}/></label></div><div className="form-help"><Sparkles/><p><b>One PDF becomes many briefs</b><br/>Stories are detected, classified, summarized, and turned into Prelims, Mains, and PYQ material.</p></div><button className="primary submit" disabled={status?.type === 'loading'}><UploadCloud/> Process newspaper</button></form>}
      {tab === 'sync' && <div className="sync-panel"><span className={`connection ${config?.apiConfigured || config?.sampleMode ? 'connected' : ''}`}><i/>{config?.apiConfigured ? 'Provider connected' : 'Sample sync mode'}</span><h2>Daily current-affairs collection</h2><p>The server retries failed sources, continues when one source fails, removes duplicates, and stores sync telemetry.</p><label>News date<input type="date" value={syncDate} onChange={e => setSyncDate(e.target.value)}/></label><div className="schedule-card"><RefreshCw/><span><b>Automatic schedule</b><small>{config?.dailySyncEnabled ? `Runs daily at ${config.schedule}` : `Manual mode. Next scheduled slot: ${config?.nextScheduledSync || 'not set'}`}</small></span></div><button className="primary submit" disabled={status?.type === 'loading'} onClick={syncNews}><RefreshCw/> Sync news now</button><SyncStatus config={config}/></div>}
      {tab === 'manual' && <form onSubmit={submitManual}><label>Article title<input required value={manual.title} onChange={e => setManual({ ...manual, title: e.target.value })} placeholder="Enter a clear headline"/></label><div className="form-row"><label>Source<input required value={manual.source} onChange={e => setManual({ ...manual, source: e.target.value })} placeholder="Publication name"/></label><label>Publication date<input type="date" value={manual.date} onChange={e => setManual({ ...manual, date: e.target.value })}/></label></div><label>Full article content<textarea required minLength="80" rows="12" value={manual.content} onChange={e => setManual({ ...manual, content: e.target.value })} placeholder="Paste the article text here..."/></label><button className="primary submit" disabled={status?.type === 'loading'}><Send/> Generate one brief</button></form>}
      {status && <p className={`ingestion-status ${status.type}`}>{status.type === 'loading' ? <LoaderCircle className="spin"/> : status.type === 'success' ? <CheckCircle2/> : <X/>}{status.message}</p>}
    </div><div className="pipeline"><h3>Automated pipeline</h3>{[['01', 'Extract', 'Reads articles from API or PDF'], ['02', 'Screen', 'Keeps syllabus-relevant news'], ['03', 'Classify', 'Maps each story to a GS subject'], ['04', 'Summarise', 'Creates concise revision notes'], ['05', 'Question', 'Frames MCQs, Mains prompts and PYQ links']].map(x => <div key={x[0]}><span>{x[0]}</span><p><b>{x[1]}</b><small>{x[2]}</small></p></div>)}</div></div></div>;
}

function SyncStatus({ config }) {
  if (!config) return null;
  return <div className="sync-status"><p><b>Last sync</b><span>{config.lastSyncTime || 'Never'}</span></p><p><b>Articles fetched</b><span>{config.articlesFetched || 0}</span></p><p><b>Next sync</b><span>{config.nextScheduledSync || 'Not scheduled'}</span></p>{(config.sourceResults || []).slice(0, 6).map(source => <p key={source.source}><b>{source.source}</b><span>{source.status} / {source.created || 0} created</span></p>)}</div>;
}

export default function App() {
  const [page, setPage] = useState('home'), [previous, setPrevious] = useState('dashboard'), [selected, setSelected] = useState(null), [articles, setArticles] = useState([]), [stats, setStats] = useState({}), [search, setSearch] = useState(''), [category, setCategory] = useState('All'), [date, setDate] = useState(''), [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark'), [menu, setMenu] = useState(false), [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(() => { try { return { ...defaultProfile, ...JSON.parse(localStorage.getItem('profile') || '{}') }; } catch { return defaultProfile; } });
  const refreshStats = () => api('/stats').then(setStats).catch(() => {});
  useEffect(() => { Promise.all([api('/articles'), api('/stats'), api('/profile')]).then(([a, s, p]) => { setArticles(a); setStats(s); setProfile({ ...defaultProfile, ...p }); localStorage.setItem('profile', JSON.stringify({ ...defaultProfile, ...p })); }).finally(() => setLoading(false)); }, []);
  useEffect(() => { document.documentElement.dataset.theme = dark ? 'dark' : 'light'; localStorage.setItem('theme', dark ? 'dark' : 'light'); }, [dark]);
  const filtered = useMemo(() => articles.filter(a => (category === 'All' || a.category === category) && (!date || a.date === date) && (!search || (`${a.title} ${a.summary} ${(a.keywords || []).join(' ')}`).toLowerCase().includes(search.toLowerCase()))), [articles, category, date, search]);
  function openArticle(a) { setPrevious(page); setSelected(a); setPage('detail'); window.scrollTo(0, 0); }
  function created(a) { if (Array.isArray(a)) { setArticles(x => [...a, ...x]); return; } setArticles(x => [a, ...x]); setSelected(a); setPrevious('admin'); setPage('detail'); }
  let view = loading ? <div className="loading"><LoaderCircle className="spin"/><p>Preparing your daily briefing...</p></div> : page === 'home' ? <Home articles={filtered} stats={stats} openArticle={openArticle} setPage={setPage} profile={profile}/> : page === 'dashboard' ? <Dashboard articles={filtered} category={category} setCategory={setCategory} date={date} setDate={setDate} openArticle={openArticle}/> : page === 'categories' ? <Categories articles={articles} setCategory={setCategory} setPage={setPage}/> : page === 'questions' ? <Questions articles={filtered}/> : page === 'admin' ? <Admin onCreated={created} stats={stats} refreshStats={refreshStats}/> : page === 'profile' ? <ProfilePage profile={profile} setProfile={setProfile} setPage={setPage}/> : <Detail article={selected} back={() => setPage(previous)}/>;
  return <div className="app"><Sidebar page={page} setPage={setPage} open={menu} close={() => setMenu(false)} profile={profile}/><div className="shell"><Header dark={dark} toggleDark={() => setDark(!dark)} search={search} setSearch={setSearch} menu={() => setMenu(true)}/>{view}<footer><Logo/><p>Built for serious preparation, one brief at a time.</p><span>(c) 2026 UPSCBrief</span></footer></div></div>;
}
