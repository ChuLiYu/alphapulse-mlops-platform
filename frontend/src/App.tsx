import { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Cpu, 
  TrendingUp, 
  Github, 
  Database,
  Cloud,
  ShieldCheck,
  Terminal,
  Layers,
  Activity as Workflow,
  Zap,
  CheckCircle2,
  Code2,
  Globe,
  ExternalLink,
  ChevronUp,
  ChevronDown,
  FileCode2,
  Binary
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { SystemLog } from './types';
import { PREDEFINED_LOGS } from './constants/logs';

// --- Sub-Components ---

const MetricCard = ({ label, value, subtext, icon: Icon, accent = "blue" }: any) => {
  const colorClasses: any = {
    blue: "text-blue-400 border-blue-500/20 shadow-blue-500/5",
    green: "text-green-400 border-green-500/20 shadow-green-500/5",
    emerald: "text-emerald-400 border-emerald-500/20 shadow-emerald-500/5",
    rose: "text-rose-400 border-rose-500/20 shadow-rose-500/5",
    indigo: "text-indigo-400 border-indigo-500/20 shadow-indigo-500/5",
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className={`bg-[#0f1115] border ${colorClasses[accent]} border-l-2 p-6 rounded-sm backdrop-blur-sm group transition-all`}>
      <div className="flex justify-between items-start mb-4 text-slate-400">
        <h3 className="text-xs font-mono uppercase tracking-[0.2em]">{label}</h3>
        <Icon className="w-6 h-6 opacity-70 group-hover:opacity-100 transition-opacity" />
      </div>
      <div className="text-3xl font-mono font-bold text-slate-100 tracking-tight mb-2">{value}</div>
      <div className="text-xs text-slate-500 font-mono border-t border-slate-800/50 pt-4 mt-2 flex items-center gap-2 uppercase tracking-tighter">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-600 group-hover:bg-slate-400"></span>{subtext}
      </div>
    </motion.div>
  );
};

const AdminLink = ({ title, status, icon: Icon, url, delay }: any) => (
  <motion.a href={url} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay, duration: 0.3 }} className="group flex items-center justify-between p-6 bg-slate-900/50 border border-slate-700/50 hover:border-emerald-500/50 hover:bg-slate-800/80 transition-all rounded-sm">
    <div className="flex items-center gap-5">
      <div className="p-3 bg-slate-950 rounded border border-slate-800 group-hover:border-emerald-500/30 group-hover:text-emerald-400 transition-colors"><Icon className="w-7 h-7 text-slate-400" /></div>
      <div><div className="text-base font-bold text-slate-200 group-hover:text-white font-mono">{title}</div><div className="text-xs text-slate-500 font-mono mt-1 tracking-wider uppercase">Protocol: OIDC-PROXY</div></div>
    </div>
    <div className="flex items-center gap-3 text-right">
      <div className="flex items-center gap-2.5 justify-end"><div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.6)]"></div><span className="text-xs font-mono text-emerald-500/80 font-bold uppercase">{status}</span></div>
      <div className="text-[10px] text-slate-600 font-mono tracking-widest uppercase tracking-widest">Encrypted_V3</div>
    </div>
  </motion.a>
);

// --- Main Application ---

const App = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [showArch, setShowArch] = useState(false);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [btcPrice, setBtcPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);
  const [memUsed, setMemUsed] = useState<number>(12.42);
  const [latency, setLatency] = useState<number>(112);
  const [sentiment, setSentiment] = useState<number>(0.74);
  const [modelHealth, setModelHealth] = useState<number>(0.024);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Real-time Fetch (BTC Price)
  useEffect(() => {
    const fetchPrice = async () => {
      try {
        const res = await fetch('https://api.coinbase.com/v2/prices/BTC-USD/spot');
        const d = await res.json();
        const p = parseFloat(d.data.amount);
        setBtcPrice(prev => {
          if (prev !== 0) setPriceChange(parseFloat(((p - prev) / prev * 100).toFixed(3)));
          return p;
        });
      } catch (e) { console.error(e); }
    };
    fetchPrice();
    const i = setInterval(fetchPrice, 1000);
    return () => clearInterval(i);
  }, []);

  // Latency Jitter (Independent)
  useEffect(() => {
    const i = setInterval(() => {
      setLatency(prev => {
        const jitter = (Math.random() - 0.5) * 4;
        const next = prev + jitter;
        return next < 102 ? 105 : next > 128 ? 122 : next;
      });
    }, 800);
    return () => clearInterval(i);
  }, []);

  // Sentiment Drift (Independent)
  useEffect(() => {
    const i = setInterval(() => {
      setSentiment(prev => {
        const drift = (Math.random() - 0.5) * 0.015;
        const next = prev + drift;
        return next < 0.62 ? 0.64 : next > 0.88 ? 0.85 : next;
      });
    }, 4000);
    return () => clearInterval(i);
  }, []);

  const getSentimentText = (val: number) => {
    if (val > 0.82) return "Extreme Greed";
    if (val > 0.75) return "Strong Bullish";
    if (val > 0.68) return "Bullish Pulse";
    return "Neutral Consensus";
  };

  // Memory Jitter (Independent)
  useEffect(() => {
    const i = setInterval(() => {
      setMemUsed(prev => {
        const n = prev + (Math.random() - 0.5) * 0.4;
        return n < 11.8 ? 11.95 : n > 16.2 ? 16.05 : n;
      });
    }, 1200);
    return () => clearInterval(i);
  }, []);

  // Model Health Jitter (Independent)
  useEffect(() => {
    const i = setInterval(() => {
      setModelHealth(prev => {
        const n = prev + (Math.random() - 0.5) * 0.001;
        return n < 0.021 ? 0.022 : n > 0.028 ? 0.027 : n;
      });
    }, 4500);
    return () => clearInterval(i);
  }, []);

  // Logs
  useEffect(() => {
    const initial = PREDEFINED_LOGS.slice(0, 6).map((l, i) => ({
      id: i, timestamp: new Date(Date.now() - (6-i)*1000).toISOString().split('T')[1].slice(0, 8), level: l.level, message: l.message
    }));
    setLogs(initial);
    const i = setInterval(() => {
      const log = PREDEFINED_LOGS[Math.floor(Math.random() * PREDEFINED_LOGS.length)];
      setLogs(p => [...p.slice(-49), { id: Date.now(), timestamp: new Date().toISOString().split('T')[1].slice(0, 8), level: log.level, message: log.message }]);
    }, 2000);
    return () => clearInterval(i);
  }, []);

  useEffect(() => {
    if (logsContainerRef.current) logsContainerRef.current.scrollTo({ top: logsContainerRef.current.scrollHeight, behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-300 font-sans overflow-x-hidden selection:bg-emerald-500/30">
      
      {/* 1. Header */}
      <header className="border-b border-slate-800/80 bg-[#050507]/90 backdrop-blur-md sticky top-0 z-50 shadow-2xl">
        <div className="max-w-[1600px] mx-auto px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3 group cursor-pointer">
              <Activity className="w-6 h-6 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
              <span className="font-bold text-2xl tracking-[0.25em] text-slate-100 uppercase">Alpha<span className="font-light text-slate-400">Pulse</span></span>
            </div>
            <div className="hidden md:flex items-center gap-3 px-4 py-1.5 bg-emerald-950/30 border border-emerald-500/20 rounded-full">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,1)]"></div>
              <span className="text-xs font-mono text-emerald-400 font-bold tracking-widest uppercase">System Operational</span>
            </div>
          </div>

          <div className="flex items-center gap-8 text-xs font-mono font-bold tracking-widest uppercase">
            <nav className="hidden lg:flex items-center gap-12 text-slate-400">
              <a href="https://chainy.luichu.dev/QV65eSp" target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400 flex items-center gap-2 group transition-all">
                <Github className="w-5 h-5 group-hover:scale-110" /> <span className="border-b border-transparent group-hover:border-emerald-500/50 pb-1">Docs_Repo</span>
              </a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-8 py-12 space-y-12">
        
        {/* 2. KPIs */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          <MetricCard label="FinOps (Oracle Free)" value="$0.00/mo" subtext="100% Opex Savings" icon={Cloud} accent="emerald" />
          <MetricCard label="Architecture" value="ARM64 / A1" subtext="Polymorphic Infra" icon={Cpu} accent="indigo" />
          <MetricCard label="Social Sentiment" value={(sentiment > 0 ? "+" : "") + sentiment.toFixed(2)} subtext={getSentimentText(sentiment)} icon={TrendingUp} accent="blue" />
          <MetricCard label="Memory Load" value={`${memUsed.toFixed(2)}GB / 24GB`} subtext="Chunked Ingestion Active" icon={Database} accent="blue" />
          <MetricCard label="Model Health" value={modelHealth.toFixed(3) + " PSI"} subtext="Gates: Stable (PASSED)" icon={ShieldCheck} accent="rose" />
        </section>

        {/* 2.5 System Blueprint */}
        <section className="border border-slate-800 rounded-sm bg-[#0f1115]/40 overflow-hidden shadow-2xl">
            <button onClick={() => setShowArch(!showArch)} className="w-full flex items-center justify-between p-6 hover:bg-white/5 transition-colors group text-slate-200 uppercase font-mono">
                <div className="flex items-center gap-5">
                    <Workflow className={`w-7 h-7 transition-colors ${showArch ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span className="font-bold text-sm tracking-[0.3em]">System Blueprint & Architecture Decision Records (ADRs)</span>
                </div>
                {showArch ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5 group-hover:text-emerald-400" />}
            </button>
            <AnimatePresence>
                {showArch && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="border-t border-slate-800 p-12 bg-black/60">
                        <div className="flex justify-center mb-16">
                            <div className="max-w-5xl w-full bg-[#0a0a0c] p-10 border border-slate-800 rounded shadow-2xl">
                                <img src="https://mermaid.ink/img/graph%20TD%0A%20%20%20%20subgraph%20Data_Hub%20%5B%221.%20Ingestion%20Layer%22%5D%0A%20%20%20%20%20%20%20%20S1(Binance%20API)%0A%20%20%20%20%20%20%20%20S2(News%20Feeds)%0A%20%20%20%20%20%20%20%20FS%5B(Feature%20Store)%5D%0A%20%20%20%20end%0A%20%20%20%20subgraph%20MLOps_Engine%20%5B%222.%20Training%20Core%22%5D%0A%20%20%20%20%20%20%20%20T1%7B%7BAirflow%7D%7D%0A%20%20%20%20%20%20%20%20T2%5B%5BTrainer%5D%5D%0A%20%20%20%20%20%20%20%20T3%7BMLflow%7D%0A%20%20%20%20%20%20%20%20T4%3EOptuna%5D%0A%20%20%20%20end%0A%20%20%20%20subgraph%20Prod_Cluster%20%5B%223.%20Production%20ARM64%22%5D%0A%20%20%20%20%20%20%20%20P1%5BFastAPI%5D%0A%20%20%20%20%20%20%20%20P3(%5BInference%5D)%0A%20%20%20%20%20%20%20%20P2%5BDashboard%5D%0A%20%20%20%20end%0A%20%20%20%20S1%20%26%20S2%20%3D%3D%3E%20FS%0A%20%20%20%20FS%20%3D%3D%3E%20T1%0A%20%20%20%20T1%20--%3E%20T2%0A%20%20%20%20T2%20%3C--%3E%20T4%0A%20%20%20%20T2%20--%3E%20T3%0A%20%20%20%20T3%20-.-%3E%20P1%0A%20%20%20%20P1%20--%3E%20P3%0A%20%20%20%20P3%20--%3E%20P2?theme=dark" alt="Architecture" className="w-full h-auto opacity-90 hover:opacity-100 transition-opacity" />
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 border-t border-slate-800 pt-16 uppercase font-mono tracking-widest text-xs">
                            <div className="space-y-4">
                                <h4 className="text-emerald-400 font-bold flex items-center gap-3"><FileCode2 className="w-5 h-5"/> ADR-007: Polymorphism</h4>
                                <p className="text-slate-400 leading-relaxed tracking-tighter">Terraform interfaces allow seamless Oracle/AWS compute migration via single variable toggle.</p>
                            </div>
                            <div className="space-y-4 border-x border-slate-800/50 px-8">
                                <h4 className="text-emerald-400 font-bold flex items-center gap-3"><Binary className="w-5 h-5"/> ADR-008: Optimization</h4>
                                <p className="text-slate-400 leading-relaxed tracking-tighter">Chunked SQL loading + float32 downcasting reduces memory footprint by 50% for 8y history.</p>
                            </div>
                            <div className="space-y-4 px-4">
                                <h4 className="text-emerald-400 font-bold flex items-center gap-3"><ShieldCheck className="w-5 h-5"/> ADR-009: Precision</h4>
                                <p className="text-slate-400 leading-relaxed tracking-tighter">Strict Python Decimal enforcement eliminates floating-point drift across all financial boundaries.</p>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </section>

        {/* 3. Main Dashboard */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          
          {/* BTC/USD Area - Custom SVG Chart */}
          <div className="lg:col-span-2 bg-[#0f1115] border border-slate-800 rounded-sm p-8 flex flex-col shadow-2xl relative overflow-hidden min-h-[600px] lg:h-[750px]">
            
            {/* 1. Header (Labels & Specs) */}
            <div className="relative z-20 mb-12">
              <div className="flex flex-col gap-6">
                <div>
                  <div className="flex items-center gap-4 sm:gap-6 flex-wrap">
                    <h2 className="text-xl sm:text-2xl font-bold text-white tracking-widest flex items-center gap-4 font-mono uppercase">
                      BTC/USD
                    </h2>
                    <span className="text-3xl sm:text-5xl font-mono text-emerald-400 tracking-tighter font-bold">
                      ${btcPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className={`text-sm sm:text-base font-mono flex items-center gap-2 px-3 py-1 rounded-sm ${priceChange >= 0 ? 'text-emerald-500 bg-emerald-500/10' : 'text-rose-500 bg-rose-500/10'}`}>
                      <TrendingUp className={`w-4 h-4 sm:w-5 sm:h-5 ${priceChange < 0 ? 'rotate-180' : ''}`} /> 
                      {priceChange >= 0 ? '+' : ''}{priceChange}%
                    </span>

                    {/* Market Status Indicator - Integrated into flow */}
                    <div className="flex items-center gap-3 bg-emerald-500/5 px-3 py-1.5 border border-emerald-500/20 rounded-sm ml-auto sm:ml-0">
                        <span className="text-[10px] font-mono text-emerald-500 font-bold tracking-[0.2em] uppercase">Market_Live</span>
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 shadow-[0_0_8px_#10b981]"></span>
                        </span>
                    </div>
                  </div>
                  
                  {/* Condensed Tech Specs */}
                  <div className="mt-8 flex flex-wrap gap-4 uppercase font-mono tracking-widest text-[10px]">
                    <span className="text-slate-500 flex items-center gap-2"><Zap className="w-3 h-3 text-blue-500" /> Latency: {latency.toFixed(0)}ms</span>
                    <span className="text-slate-500 flex items-center gap-2"><Cpu className="w-3 h-3 text-emerald-500" /> Node: ARM64_A1</span>
                    <span className="text-slate-500 flex items-center gap-2"><CheckCircle2 className="w-3 h-3 text-amber-500" /> Precision: Decimal_V2</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. The Custom SVG Chart Area */}
            <div className="flex-1 relative z-10 w-full min-h-[350px]">
                {/* Grid Background */}
                <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'linear-gradient(rgba(30, 41, 59, 0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(30, 41, 59, 0.5) 1px, transparent 1px)', backgroundSize: '60px 60px' }}></div>
                
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 1000 400">
                    <defs>
                        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
                            <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                        </linearGradient>
                        <filter id="svgGlow" x="-20%" y="-20%" width="140%" height="140%">
                            <feGaussianBlur stdDeviation="6" result="blur" />
                            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                        </filter>
                    </defs>
                    
                    {/* Animated Wave Area */}
                    <motion.path 
                        initial={{ pathLength: 0, opacity: 0 }} 
                        animate={{ pathLength: 1, opacity: 1 }} 
                        transition={{ duration: 2.5, ease: "easeInOut" }}
                        d="M0,350 C100,320 200,380 300,280 C400,180 500,250 600,120 C700,20 800,80 900,40 C1000,-10 1100,20 1200,-30 L1200,400 L0,400 Z" 
                        fill="url(#chartGradient)" 
                    />
                    
                    {/* Animated Main Line */}
                    <motion.path 
                        initial={{ pathLength: 0 }} 
                        animate={{ pathLength: 1 }} 
                        transition={{ duration: 3, ease: "easeInOut" }}
                        d="M0,350 C100,320 200,380 300,280 C400,180 500,250 600,120 C700,20 800,80 900,40 C1000,-10 1100,20 1200,-30" 
                        fill="none" 
                        stroke="#10b981" 
                        strokeWidth="4" 
                        filter="url(#svgGlow)"
                    />
                </svg>
            </div>

            {/* Axis Labels */}
            <div className="relative h-12 border-t border-slate-800 bg-[#0f1115] flex items-center justify-between px-10 text-xs font-mono text-slate-600 uppercase tracking-[0.2em] z-20">
                <span>00:00 UTC</span>
                <span>08:00</span>
                <span>16:00</span>
                <span className="text-emerald-500/40 animate-pulse">Syncing_Inference_Engine...</span>
            </div>
          </div>

          {/* Right Panel: Logs */}
          <div className="bg-black border border-slate-800 rounded-sm flex flex-col shadow-inner relative overflow-hidden h-[600px] lg:h-[750px]">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 bg-[#0f1115]">
              <span className="text-slate-400 text-sm font-mono flex items-center gap-3 uppercase tracking-widest"><Terminal className="w-5 h-5 text-blue-500" /> Pipeline_Stdout</span>
              <div className="flex gap-2"><div className="w-3 h-3 rounded-full bg-slate-800 border border-slate-700"></div><div className="w-3 h-3 rounded-full bg-slate-800 border border-slate-700"></div><div className="w-3 h-3 rounded-full bg-emerald-900 border border-emerald-700/50 shadow-[0_0_10px_#10b981]"></div></div>
            </div>
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 opacity-20"></div>
            <div ref={logsContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-800 font-mono text-[14px] leading-relaxed">
              {logs.map((log) => (
                <div key={log.id} className="flex gap-5 animate-in fade-in duration-300">
                  <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                  <div className="flex flex-col">
                    <span className={`font-bold uppercase tracking-tighter ${
                      log.level === 'INFO' ? 'text-blue-400' : 
                      log.level === 'SUCCESS' ? 'text-emerald-400' : 
                      log.level === 'WARN' ? 'text-amber-400' : 
                      log.level === 'ERROR' ? 'text-rose-400' :
                      log.level === 'DEBUG' ? 'text-slate-400' :
                      'text-purple-400'
                    }`}>{log.level}</span>
                    <span className="text-slate-300 break-words">{log.message}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-900 bg-[#0a0a0c] text-slate-500 text-xs font-mono flex items-center gap-4 tracking-widest uppercase">
              <span className="w-2 h-5 bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]"></span>PID_ACTIVE_4421
            </div>
          </div>
        </section>

        {/* Commander Mode */}
        <AnimatePresence>
        {isAdmin && (
            <motion.section initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.4 }} className="border border-slate-800 bg-[#0f1115] rounded-sm overflow-hidden shadow-2xl">
            <div className="p-6 bg-slate-900/50 border-b border-slate-800 flex items-center justify-between font-mono">
                <div className="flex items-center gap-5">
                <ShieldCheck className="w-7 h-7 text-emerald-500" /><h3 className="font-bold tracking-[0.3em] text-slate-100 uppercase text-lg">Commander Mode <span className="font-normal text-emerald-500/80 text-xs ml-4 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 tracking-widest">SSO_AUTH_SUCCESS</span></h3>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500 font-bold uppercase"><span className="w-3 h-3 rounded-full bg-emerald-500 shadow-glow"></span>Secure_Node_Online</div>
            </div>
            <div className="p-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 uppercase font-mono">
                <AdminLink title="Airflow Orchestrator" status="14 Online" icon={Workflow} url="http://localhost:8080" delay={0.1} />
                <AdminLink title="MLflow Registry" status="v2.4 Ready" icon={Layers} url="http://localhost:5000" delay={0.2} />
                <AdminLink title="Evidently AI Monitor" status="Active" icon={Activity} url="http://localhost:8000/dashboard" delay={0.3} />
                <AdminLink title="FastAPI Interactive" status="v1_Stable" icon={Zap} url="/api/docs" delay={0.4} />
                <AdminLink title="Grafana Metrics" status="Operational" icon={TrendingUp} url="http://localhost:3000" delay={0.5} />
                <AdminLink title="GitHub CI/CD" status="Passing" icon={Github} url="https://chainy.luichu.dev/QV65eSp" delay={0.6} />
            </div>
            </motion.section>
        )}
        </AnimatePresence>

        {/* Footer */}
        <footer className="border-t border-slate-800/50 pt-20 pb-20 mt-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-end">
            <div className="space-y-8">
                <div className="flex items-center gap-6">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-glow transition-transform hover:scale-110"><Code2 className="w-8 h-8 text-emerald-400" /></div>
                    <div><h4 className="text-white font-bold text-2xl tracking-tight">Lui Chu</h4><p className="text-slate-500 text-sm font-mono uppercase tracking-[0.25em] mt-1">Full-Stack & MLOps Architect</p></div>
                </div>
                <div className="flex flex-wrap items-center gap-8 font-bold font-mono text-sm tracking-widest uppercase">
                    <a href="https://luichu.dev/" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 text-slate-400 hover:text-emerald-400 transition-all border-b border-transparent hover:border-emerald-500/30 pb-1"><Globe className="w-5 h-5" /> Site</a>
                    <a href="https://chainy.luichu.dev/QV65eSp" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 text-slate-400 hover:text-emerald-400 transition-all border-b border-transparent hover:border-emerald-500/30 pb-1"><Github className="w-5 h-5" /> Repo</a>
                    <a href="mailto:contact@luichu.dev" className="flex items-center gap-3 text-slate-400 hover:text-emerald-400 transition-all border-b border-transparent hover:border-emerald-500/30 pb-1"><ExternalLink className="w-5 h-5" /> Mail</a>
                </div>
            </div>
            <div className="text-right space-y-4 border-r-4 border-emerald-500/20 pr-8 font-mono">
                <p className="text-slate-600 text-xs tracking-[0.3em] uppercase font-bold">
                    AlphaPulse Engine v2.4.1 
                    <button 
                        onClick={() => setIsAdmin(!isAdmin)} 
                        className="mx-4 text-slate-800 hover:text-emerald-900 transition-colors cursor-default"
                    >
                        |
                    </button> 
                    Region: ap-chuncheon-1 (Oracle)
                </p>
                <p className="text-slate-500 text-xs max-w-xl ml-auto leading-relaxed uppercase tracking-tight">Built with rigid Python Decimal precision, polymorphic Terraform infrastructure, and automated Optuna tuning. Optimized for Zero-Cost compute architectures and production stability.</p>
            </div>
          </div>
        </footer>

      </main>
    </div>
  );
};

export default App;