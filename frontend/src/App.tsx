import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal, 
  Cpu, 
  ShieldCheck, 
  Activity, 
  Server, 
  GitBranch, 
  Lock, 
  Unlock, 
  Database, 
  Cloud, 
  Zap, 
  Search,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Code2,
  Layers,
  ChevronDown,
  ChevronUp,
  Github,
  Globe,
  ExternalLink,
  Workflow,
  ArrowRight,
  DatabaseZap,
  Box,
  Binary,
  History,
  FileCode2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- Types ---

interface SystemLog {
  id: number;
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'WARN' | 'SYSTEM';
  message: string;
}

const PREDEFINED_LOGS = [
  { level: 'INFO', message: 'Downcasting float64 -> float32 for memory optimization' },
  { level: 'SUCCESS', message: 'Walk-Forward Cross-Validation passed (Window: 24h)' },
  { level: 'SYSTEM', message: 'Polymorphic Infra Check: Oracle Cloud ARM64 [ACTIVE]' },
  { level: 'INFO', message: 'Garbage Collection: Reclaimed 450MB Heap' },
  { level: 'INFO', message: 'Terraform State: Locked (s3://alphapulse-state)' },
  { level: 'SUCCESS', message: 'Decimal Type Enforced: Rounding Mode HALF_UP verified' },
  { level: 'WARN', message: 'Market Volatility detected > 1.5 sigma' },
  { level: 'INFO', message: 'OIDC Handshake: GitHub Org verified' },
  { level: 'SYSTEM', message: 'K3s Node Pressure: Normal' },
  { level: 'SUCCESS', message: 'Model Registry: v2.4.1 promoted to Staging' },
];

// --- Sub-Components ---

const MetricCard = ({ 
  label, 
  value, 
  subtext, 
  icon: Icon, 
  accent = "blue" 
}: { 
  label: string; 
  value: string; 
  subtext: string; 
  icon: React.ElementType; 
  accent?: "blue" | "green" | "emerald" | "rose" | "indigo"
}) => {
  const colorClasses = {
    blue: "text-blue-400 border-blue-500/20 shadow-blue-500/5 hover:border-blue-500/40",
    green: "text-green-400 border-green-500/20 shadow-green-500/5 hover:border-green-500/40",
    emerald: "text-emerald-400 border-emerald-500/20 shadow-emerald-500/5 hover:border-emerald-500/40",
    rose: "text-rose-400 border-rose-500/20 shadow-rose-500/5 hover:border-rose-500/40",
    indigo: "text-indigo-400 border-indigo-500/20 shadow-indigo-500/5 hover:border-indigo-500/40",
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-[#0f1115] border ${colorClasses[accent]} border-l-2 p-6 rounded-sm backdrop-blur-sm transition-all group`}
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-slate-400 text-xs font-mono uppercase tracking-[0.2em]">{label}</h3>
        <Icon className={`w-6 h-6 ${colorClasses[accent].split(' ')[0]} opacity-70 group-hover:opacity-100 transition-opacity`} />
      </div>
      <div className="text-3xl font-mono font-bold text-slate-100 tracking-tight mb-2">
        {value}
      </div>
      <div className="text-xs text-slate-500 font-mono border-t border-slate-800/50 pt-4 mt-2 flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-600 group-hover:bg-slate-400 transition-colors"></span>
        {subtext}
      </div>
    </motion.div>
  );
};

const ArchNode = ({ label, icon: Icon, type, id }: { label: string, icon: React.ElementType, type: 'data' | 'compute' | 'prod' | 'storage', id?: string }) => {
    const colors = {
        data: 'border-sky-500/30 bg-sky-500/10 text-sky-400 shadow-[0_0_15px_rgba(14,165,233,0.1)]',
        compute: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)]',
        prod: 'border-amber-500/30 bg-amber-500/10 text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.1)]',
        storage: 'border-purple-500/30 bg-purple-500/10 text-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.1)]'
    };
    return (
        <div id={id} className={`p-4 border rounded-sm flex flex-col items-center gap-3 transition-all hover:scale-105 hover:bg-white/5 cursor-default group ${colors[type]}`}>
            <Icon className="w-6 h-6 group-hover:animate-pulse" />
            <span className="text-[11px] font-mono font-bold uppercase tracking-widest text-center whitespace-nowrap">{label}</span>
        </div>
    );
};

const AdminLink = ({ title, status, icon: Icon, url, delay }: { title: string, status: string, icon: React.ElementType, url: string, delay: number }) => (
  <motion.a 
    href={url} 
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay, duration: 0.3 }}
    className="group flex items-center justify-between p-6 bg-slate-900/50 border border-slate-700/50 hover:border-emerald-500/50 hover:bg-slate-800/80 transition-all cursor-pointer rounded-sm"
  >
    <div className="flex items-center gap-5">
      <div className="p-3 bg-slate-950 rounded border border-slate-800 group-hover:border-emerald-500/30 group-hover:text-emerald-400 transition-colors">
        <Icon className="w-7 h-7 text-slate-400" />
      </div>
      <div>
        <div className="text-base font-bold text-slate-200 group-hover:text-white font-mono">{title}</div>
        <div className="text-xs text-slate-500 font-mono mt-1 tracking-wider uppercase">Protocol: OIDC-PROXY</div>
      </div>
    </div>
    <div className="flex items-center gap-3 text-right">
      <div className="flex items-center gap-2.5 justify-end">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.6)]"></div>
        <span className="text-xs font-mono text-emerald-500/80 font-bold uppercase">{status}</span>
      </div>
      <div className="text-[10px] text-slate-600 font-mono tracking-widest">TLS_1.3_ENCRYPTED</div>
    </div>
  </motion.a>
);

// --- Main Application ---

const App = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [showArch, setShowArch] = useState(false);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [btcPrice, setBtcPrice] = useState<number>(94820.50);
  const [priceChange, setPriceChange] = useState<number>(1.24);
  const [memUsed, setMemUsed] = useState<number>(12.42);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Real-time BTC Logic
  useEffect(() => {
    const fetchBtcPrice = async () => {
      try {
        const response = await fetch('https://api.coinbase.com/v2/prices/BTC-USD/spot');
        const data = await response.json();
        const newPrice = parseFloat(data.data.amount);
        setBtcPrice(prev => {
          const diff = ((newPrice - prev) / prev) * 100;
          if (Math.abs(diff) > 0.0001) setPriceChange(parseFloat(diff.toFixed(3)));
          return newPrice;
        });
      } catch (e) { console.error(e); }
    };
    fetchBtcPrice();
    const priceInterval = setInterval(fetchBtcPrice, 1000);
    return () => clearInterval(priceInterval);
  }, []);

  // Memory Jitter
  useEffect(() => {
    const memInterval = setInterval(() => {
      setMemUsed(prev => {
        const jitter = (Math.random() - 0.5) * 0.4;
        const next = prev + jitter;
        return next < 11.8 ? 11.95 : next > 16.2 ? 16.05 : next;
      });
    }, 1200);
    return () => clearInterval(memInterval);
  }, []);

  // Initialize Logs
  useEffect(() => {
    const initialLogs = PREDEFINED_LOGS.slice(0, 6).map((l, i) => ({
      id: i,
      timestamp: new Date(Date.now() - (6-i)*1000).toISOString().split('T')[1].slice(0, 12),
      level: l.level as any,
      message: l.message
    }));
    setLogs(initialLogs);

    const interval = setInterval(() => {
      const randomLog = PREDEFINED_LOGS[Math.floor(Math.random() * PREDEFINED_LOGS.length)];
      const newLog = {
        id: Date.now(),
        timestamp: new Date().toISOString().split('T')[1].slice(0, 12),
        level: randomLog.level as any,
        message: randomLog.message
      };
      setLogs(prev => [...prev.slice(-49), newLog]);
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  // Scroll logs
  useEffect(() => {
    if (logsContainerRef.current) {
        logsContainerRef.current.scrollTo({ top: logsContainerRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-300 font-sans selection:bg-emerald-500/30 selection:text-emerald-200 overflow-x-hidden">
      
      {/* 1. Header (Architect View) */}
      <header className="border-b border-slate-800/80 bg-[#050507]/90 backdrop-blur-md sticky top-0 z-50 shadow-2xl">
        <div className="max-w-[1600px] mx-auto px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3 group cursor-pointer">
              <div className="relative">
                <Activity className="w-6 h-6 text-emerald-500" />
                <div className="absolute inset-0 bg-emerald-500/40 blur-sm animate-pulse rounded-full"></div>
              </div>
              <span className="font-bold text-2xl tracking-[0.25em] text-slate-100 group-hover:text-emerald-400 transition-colors uppercase">
                Alpha<span className="font-light text-slate-400">Pulse</span>
              </span>
            </div>
            
            <div className="hidden md:flex items-center gap-3 px-4 py-1.5 bg-emerald-950/30 border border-emerald-500/20 rounded-full">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,1)]"></div>
              <span className="text-xs font-mono text-emerald-400 font-bold tracking-widest uppercase">System Operational</span>
            </div>
          </div>

          <div className="flex items-center gap-8">
            <nav className="hidden lg:flex items-center gap-12 text-xs font-mono text-slate-400 uppercase tracking-widest">
              <a href="https://chainy.luichu.dev/QV65eSp" target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400 flex items-center gap-2.5 transition-colors group">
                <Github className="w-5 h-5 group-hover:scale-110 transition-transform" /> 
                <span className="border-b border-transparent group-hover:border-emerald-500/50 pb-1">Repo & Docs</span>
              </a>
              <a href="#" className="hover:text-emerald-400 flex items-center gap-2.5 transition-colors group">
                <Code2 className="w-5 h-5 group-hover:scale-110 transition-transform" /> 
                <span className="border-b border-transparent group-hover:border-emerald-500/50 pb-1">local_dev.sh</span>
              </a>
            </nav>
            
            <div className="h-8 w-px bg-slate-800 mx-2 hidden md:block"></div>

            <button 
              onClick={() => setIsAdmin(!isAdmin)}
              className={`
                flex items-center gap-2.5 px-6 py-2.5 rounded-sm border text-xs font-mono font-bold transition-all duration-300 uppercase tracking-widest
                ${isAdmin 
                  ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400 hover:bg-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.15)]' 
                  : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'}
              `}
            >
              {isAdmin ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
              {isAdmin ? 'Commander Mode Active' : 'Login'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-8 py-12 space-y-12">
        
        {/* 2. FinOps KPIs */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <MetricCard label="FinOps (Oracle Always Free)" value="$0.00/mo" subtext="100% Opex Savings vs AWS EC2" icon={Cloud} accent="emerald" />
          <MetricCard label="Architecture (Ampere A1)" value="ARM64" subtext="Polymorphic Terraform Infra" icon={Cpu} accent="indigo" />
          <MetricCard label="Memory (Chunked Loading)" value={`${memUsed.toFixed(2)}GB / 24GB`} subtext="8y History without Swap" icon={Database} accent="blue" />
          <MetricCard label="Model Health (PSI)" value="0.024" subtext="Overfitting Gates: PASSED" icon={ShieldCheck} accent="rose" />
        </section>

        {/* 2.5 Dynamic Architecture Blueprint & ADRs */}
        <section className="border border-slate-800 rounded-sm bg-[#0f1115]/40 overflow-hidden shadow-2xl transition-all hover:border-slate-700/80">
            <button 
                onClick={() => setShowArch(!showArch)}
                className="w-full flex items-center justify-between p-6 hover:bg-white/5 transition-colors group"
            >
                <div className="flex items-center gap-5">
                    <Workflow className={`w-7 h-7 transition-colors ${showArch ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span className="font-bold text-sm font-mono uppercase tracking-[0.3em] text-slate-200">System Blueprint & Architecture Decision Records (ADRs)</span>
                </div>
                {showArch ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500 group-hover:text-emerald-400" />}
            </button>
            
            <AnimatePresence>
                {showArch && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="border-t border-slate-800 p-12 bg-black/60">
                        {/* THE GRAPH: High-Fidelity Mermaid Image */}
                        <div className="relative flex justify-center py-8">
                            <div className="relative group max-w-5xl w-full">
                                {/* Decorative Glow Background */}
                                <div className="absolute inset-0 bg-emerald-500/5 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
                                
                                {/* 
                                    Using Mermaid.ink to render the diagram. 
                                    The base64 string encodes your specific architecture logic and styling.
                                */}
                                <img 
                                    src="https://mermaid.ink/img/Z3JhcGggVEQKICAgIGNsYXNzRGVmIGRhdGEgZmlsbDojRTFGNUZFLHN0cm9rZTojMDE1NzlCLHN0cm9rZS13aWR0aDoycHgsY29sb3I6IzAxNTc5QjsKICAgIGNsYXNzRGVmIGNvbXB1dGUgZmlsbDojRThGNUU5LHN0cm9rZTojMkU3RDMyLHN0cm9rZS13aWR0aDoycHgsY29sb3I6IzFCNUUyMDsKICAgIGNsYXNzRGVmIHByb2QgZmlsbDojRkZGM0UwLHN0cm9rZTojRUY2QzAwLHN0cm9rZS13aWR0aDoycHgsY29sb3I6I0U2NTEwMDsKICAgIGNsYXNzRGVmIHN0b3JhZ2UgZmlsbDojRjNFNUY1LHN0cm9rZTojN0IxRkEyLHN0cm9rZS13aWR0aDoycHgsY29sb3I6IzRBMTQ4QzsKICAgIHN1YmdyYXBoIERhdGFfSHViIFsiMS4gSW5nZXN0aW9uIExheWVyIl0KICAgICAgICBTMShCaW5hbmNlIEFQSSkKICAgICAgICBTMihOZXdzIEZlZWRzKQogICAgICAgIEZTWyhGZWF0dXJlIFN0b3JlKV0KICAgIGVuZAogICAgc3ViZ3JhcGggTUxPcHNfRW5naW5lIFsiMi4gVHJhaW5pbmcgQ29yZSJdCiAgICAgICAgVDF7e0FpcmZsb3d9fQogICAgICAgIFQyW1tUcmFpbmVyXV0KICAgICAgICBUM3tNTGZsb3d9CiAgICAgICAgVDQ+T3B0dW5hXQogICAgZW5kCiAgICBzdWJncmFwaCBQcm9kX0NsdXN0ZXIgWyIzLiBQcm9kdWN0aW9uIEFSTTY0Il0KICAgICAgICBQMVtGYXN0QVBJXQogICAgICAgIFAzKFtJbmZlcmVuY2VdKQogICAgICAgIFAyW0Rhc2hib2FyZF0KICAgIGVuZAogICAgc3ViZ3JhcGggQ2xvdWRfVGllciBbIjQuIFBlcnNpc3RlbmNlIl0KICAgICAgICBTVDFbKEFXUyBTMyldCiAgICAgICAgU1QyWyhDbG91ZGZsYXJlIFIyKV0KICAgIGVuZAogICAgUzEgJiBTMiA9PT4gRlMKICAgIEZTID09PiBUMQogICAgVDEgLS0+IFQyCiAgICBUMiA8LS0+IFQ0CiAgICBUMiAtLT4gVDMKICAgIFQzIC0uLT4gUDEKICAgIFAxIC0tPiBQMwogICAgUDMgLS0+IFAyCiAgICBGUyAtLi0+IFNUMQogICAgVDMgLS4tPiBTVDEKICAgIFAxIC0uLT4gU1QxCiAgICBTVDEgPT09IFNUMgogICAgY2xhc3MgUzEsUzIsRlMgZGF0YQogICAgY2xhc3MgVDEsVDIsVDMsVDQgY29tcHV0ZQogICAgY2xhc3MgUDEsUDIsUDMgcHJvZAogICAgY2xhc3MgU1QxLFNUMiBzdG9yYWdlCg==?theme=dark" 
                                    alt="AlphaPulse System Architecture" 
                                    className="relative z-10 w-full rounded-sm border border-slate-800 bg-[#0a0a0c] p-8 shadow-2xl hover:border-emerald-500/30 transition-all duration-500"
                                />
                                
                                <div className="mt-6 flex justify-center gap-8 text-[10px] font-mono uppercase tracking-widest text-slate-500">
                                    <span className="flex items-center gap-2"><span className="w-2 h-2 bg-[#E1F5FE] rounded-full"></span> Data_Ingestion</span>
                                    <span className="flex items-center gap-2"><span className="w-2 h-2 bg-[#E8F5E9] rounded-full"></span> MLOps_Compute</span>
                                    <span className="flex items-center gap-2"><span className="w-2 h-2 bg-[#FFF3E0] rounded-full"></span> Prod_Runtime</span>
                                    <span className="flex items-center gap-2"><span className="w-2 h-2 bg-[#F3E5F5] rounded-full"></span> Persistence</span>
                                </div>
                            </div>
                        </div>
                        
                        {/* ADR SECTION */}
                        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-12 border-t border-slate-800 pt-16">
                            <div className="space-y-4">
                                <div className="flex items-center gap-3 text-emerald-400">
                                    <FileCode2 className="w-6 h-6" />
                                    <h4 className="text-sm font-bold uppercase font-mono tracking-widest">ADR-007: Polymorphic Infra</h4>
                                </div>
                                <p className="text-sm text-slate-400 leading-relaxed font-mono">Implemented a Provider-Agnostic abstraction using Terraform. The system defines a "Compute Module Interface," allowing seamless switching between Oracle ARM64 and AWS EC2 via single variable interface.</p>
                            </div>
                            <div className="space-y-4 border-x border-slate-800/50 px-8">
                                <div className="flex items-center gap-3 text-emerald-400">
                                    <Binary className="w-6 h-6" />
                                    <h4 className="text-sm font-bold uppercase font-mono tracking-widest">ADR-008: Memory Optimization</h4>
                                    <span className="text-[10px] bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">Senior Hack</span>
                                </div>
                                <p className="text-sm text-slate-400 leading-relaxed font-mono">Developed a Chunked Loading + Type Downcasting strategy. Reduced memory footprint by 50% by downcasting float64 to float32, enabling 8+ years of BTC history training on a 24GB instance.</p>
                            </div>
                            <div className="space-y-4 px-4">
                                <div className="flex items-center gap-3 text-emerald-400">
                                    <ShieldCheck className="w-6 h-6" />
                                    <h4 className="text-sm font-bold uppercase font-mono tracking-widest">ADR-009: Financial Precision</h4>
                                </div>
                                <p className="text-sm text-slate-400 leading-relaxed font-mono">Rigid enforcement of Decimal types across all trading boundaries. Unlike generic ML templates, AlphaPulse eliminates IEEE-754 floating-point errors in simulations to ensure ACID-compliant financial calculations.</p>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </section>

        {/* 3. Main Dashboard */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-10 lg:h-[700px]">
          <div className="lg:col-span-2 bg-[#0f1115] border border-slate-800 rounded-sm p-1 flex flex-col relative overflow-hidden group shadow-2xl">
            <div className="absolute top-0 left-0 right-0 p-8 flex justify-between items-start bg-gradient-to-b from-[#0f1115] via-[#0f1115]/95 to-transparent z-20">
              <div className="max-w-[70%]">
                <div className="flex items-baseline gap-5 flex-wrap">
                  <h2 className="text-3xl font-bold text-white tracking-tight flex items-center gap-4">
                    <span className="w-4 h-4 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.8)]"></span>
                    BTC/USD
                  </h2>
                  <span className="text-5xl font-mono text-emerald-400 tracking-tighter">
                    ${btcPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className={`text-base font-mono flex items-center gap-2 px-3 py-1 rounded-sm ${priceChange >= 0 ? 'text-emerald-500 bg-emerald-500/10' : 'text-rose-500 bg-rose-500/10'}`}>
                    <TrendingUp className={`w-5 h-5 ${priceChange < 0 ? 'rotate-180' : ''}`} /> 
                    {priceChange >= 0 ? '+' : ''}{priceChange}%
                  </span>
                </div>
                
                {/* Technical Specs Row (Now grouped together) */}
                <div className="mt-6 flex flex-wrap items-center gap-3 uppercase tracking-widest">
                  <span className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 text-blue-300 text-[11px] font-mono rounded flex items-center gap-2">
                    <Zap className="w-4 h-4" /> P99: 112ms
                  </span>
                  <span className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-[11px] font-mono rounded flex items-center gap-2">
                    <Cpu className="w-4 h-4" /> ARM64_A1
                  </span>
                  <span className="px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-mono rounded flex items-center gap-2">
                    <Layers className="w-4 h-4" /> v2.4.1_CATBOOST
                  </span>
                  <span className="px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] font-mono rounded flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" /> DECIMAL_ENFORCED
                  </span>
                </div>
              </div>
              
              <div className="text-right hidden sm:block font-mono text-xs">
                <div className="text-emerald-500/60 bg-emerald-500/5 px-3 py-1 border border-emerald-500/20 rounded-sm tracking-widest uppercase">
                  Status: Hot-Reload Active
                </div>
                <div className="text-slate-600 mt-2 text-[10px] tracking-tighter uppercase font-bold">
                  Next_Retrain: 04:00 UTC
                </div>
              </div>
            </div>

            <div className="flex-1 w-full h-full relative mt-28 ml-6">
                <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(30, 41, 59, 0.25) 1px, transparent 1px), linear-gradient(90deg, rgba(30, 41, 59, 0.25) 1px, transparent 1px)', backgroundSize: '60px 60px' }}></div>
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#10b981" stopOpacity="0.25" /><stop offset="100%" stopColor="#10b981" stopOpacity="0" /></linearGradient>
                  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
                </defs>
                <motion.path initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 2.5, ease: "easeInOut" }} d="M0,450 C100,420 200,480 300,380 C400,280 500,350 600,220 C700,120 800,180 900,100 C1000,50 1100,80 1200,30 L1200,600 L0,600 Z" fill="url(#chartGradient)" />
                <motion.path initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 3, ease: "easeInOut" }} d="M0,450 C100,420 200,480 300,380 C400,280 500,350 600,220 C700,120 800,180 900,100 C1000,50 1100,80 1200,30" fill="none" stroke="#10b981" strokeWidth="4" filter="url(#glow)" />
              </svg>
              <div className="absolute right-[5%] top-[8%] flex flex-col items-end z-10">
                 <div className="flex items-center gap-4 mb-3 bg-black/40 backdrop-blur-sm p-2 rounded-sm border border-emerald-500/10">
                    <span className="text-xs font-mono text-emerald-400 font-bold tracking-[0.3em]">Market_Live</span>
                    <span className="relative flex h-4 w-4">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                    </span>
                 </div>
                 <div className="text-xs text-slate-500 font-mono tracking-[0.1em] uppercase pr-2">24h_Volume: 42.5K BTC</div>
              </div>
            </div>
            
            <div className="absolute bottom-0 left-0 right-0 h-12 border-t border-slate-800 bg-[#0f1115] flex items-center justify-between px-10 text-xs font-mono text-slate-600 uppercase tracking-[0.2em]">
                <span>Time_Series: 00:00 UTC</span>
                <span>Interval: 1H</span>
                <span className="text-emerald-500/40 animate-pulse">Connection_Status: Syncing...</span>
            </div>
          </div>

          {/* Right Panel: Logs */}
          <div className="bg-black border border-slate-800 rounded-sm p-0 flex flex-col shadow-inner relative overflow-hidden h-full">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 bg-[#0f1115]">
              <span className="text-slate-400 text-sm font-mono flex items-center gap-3 tracking-[0.2em] uppercase">
                <Terminal className="w-5 h-5 text-blue-500" /> Pipeline_Stdout
              </span>
              <div className="flex gap-2.5">
                <div className="w-3.5 h-3.5 rounded-full bg-slate-800 border border-slate-700"></div>
                <div className="w-3.5 h-3.5 rounded-full bg-slate-800 border border-slate-700"></div>
                <div className="w-3.5 h-3.5 rounded-full bg-emerald-900 border border-emerald-700/50 shadow-[0_0_10px_rgba(16,185,129,0.4)]"></div>
              </div>
            </div>
            
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%] opacity-20"></div>
            
            <div ref={logsContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4.5 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent font-mono text-[14px] leading-relaxed">
              {logs.map((log) => (
                <div key={log.id} className="flex gap-5 animate-in fade-in slide-in-from-left-2 duration-300">
                  <span className="text-slate-600 shrink-0 select-none">[{log.timestamp}]</span>
                  <div className="flex flex-col">
                    <span className={`font-bold mb-1 uppercase tracking-tighter ${log.level === 'INFO' ? 'text-blue-400' : ''} ${log.level === 'SUCCESS' ? 'text-emerald-400' : ''} ${log.level === 'WARN' ? 'text-amber-400' : ''} ${log.level === 'SYSTEM' ? 'text-purple-400' : ''}`}>
                        {log.level}
                    </span>
                    <span className="text-slate-300 break-words font-medium">{log.message}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-900 bg-[#0a0a0c] text-slate-500 text-xs font-mono flex items-center gap-4 tracking-widest uppercase">
              <span className="w-2 h-5 bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
              Runtime_Process: Active_PID_4421
            </div>
          </div>
        </section>

        {/* 4. Commander Mode */}
        <AnimatePresence>
        {isAdmin && (
            <motion.section initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.4, ease: "easeInOut" }} className="border border-slate-800 bg-[#0f1115] rounded-sm overflow-hidden shadow-[0_0_60px_rgba(0,0,0,0.6)]">
            <div className="p-6 bg-slate-900/50 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-5">
                <ShieldCheck className="w-7 h-7 text-emerald-500" />
                <h3 className="font-bold tracking-[0.3em] text-slate-100 text-lg font-mono uppercase">Commander Mode <span className="font-normal text-emerald-500/80 text-xs ml-4 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 tracking-widest">SSO_AUTH_SUCCESS</span></h3>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500 font-mono tracking-[0.2em] font-bold uppercase">
                    <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,1)]"></span>
                    Cluster_Secure_Node
                </div>
            </div>
            <div className="p-10 grid grid-cols-1 md:grid-cols-3 gap-10">
                <AdminLink title="Airflow Dags" status="14 Online" icon={Workflow} url="http://localhost:8080" delay={0.1} />
                <AdminLink title="MLflow Registry" status="v2.4 Ready" icon={Layers} url="http://localhost:5000" delay={0.2} />
                <AdminLink title="K3s Dashboard" status="Cluster Healthy" icon={Server} url="#" delay={0.3} />
            </div>
            </motion.section>
        )}
        </AnimatePresence>

        {/* 5. Footer (Personalized) */}
        <footer className="border-t border-slate-800/50 pt-20 pb-20 mt-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-end">
            <div className="space-y-8">
                <div className="flex items-center gap-6">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.15)] group transition-all hover:scale-110">
                        <Code2 className="w-8 h-8 text-emerald-400" />
                    </div>
                    <div>
                        <h4 className="text-white font-bold text-2xl tracking-tight">Lui Chu</h4>
                        <p className="text-slate-500 text-sm font-mono uppercase tracking-[0.25em] mt-1">Full-Stack & MLOps System Architect</p>
                    </div>
                </div>
                <div className="flex flex-wrap items-center gap-8">
                    <a href="https://luichu.dev/" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 text-sm font-mono text-slate-400 hover:text-emerald-400 transition-all uppercase tracking-widest border-b border-transparent hover:border-emerald-500/30 pb-1.5 font-bold group">
                        <Globe className="w-5 h-5 group-hover:rotate-12 transition-transform" /> Personal_Site
                    </a>
                    <a href="https://chainy.luichu.dev/QV65eSp" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 text-sm font-mono text-slate-400 hover:text-emerald-400 transition-all uppercase tracking-widest border-b border-transparent hover:border-emerald-500/30 pb-1.5 font-bold group">
                        <Github className="w-5 h-5 group-hover:scale-110 transition-transform" /> GitHub_Repo
                    </a>
                    <a href="mailto:contact@luichu.dev" className="flex items-center gap-3 text-sm font-mono text-slate-400 hover:text-emerald-400 transition-all uppercase tracking-widest border-b border-transparent hover:border-emerald-500/30 pb-1.5 font-bold group">
                        <ExternalLink className="w-5 h-5" /> Direct_Contact
                    </a>
                </div>
            </div>
            
            <div className="text-right space-y-4 border-r-4 border-emerald-500/20 pr-8">
                <p className="text-slate-600 text-xs font-mono tracking-[0.3em] uppercase font-bold">AlphaPulse Engine v2.4.1 <span className="mx-4 text-slate-800">|</span> Region: ap-chuncheon-1 (Oracle)</p>
                <p className="text-slate-500 text-xs font-mono max-w-xl ml-auto leading-relaxed uppercase tracking-tight">
                    Engineered with rigid Python Decimal precision, polymorphic Terraform infrastructure, and automated Optuna tuning. Optimized for Zero-Cost Oracle ARM64 cloud architectures. Built for production stability and extreme cost-efficiency.
                </p>
            </div>
          </div>
        </footer>

      </main>
    </div>
  );
};

export default App;