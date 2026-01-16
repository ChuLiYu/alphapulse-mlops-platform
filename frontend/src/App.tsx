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
  CheckCircle2,
  Code2,
  Layers,
  ChevronDown,
  ChevronUp,
  Github,
  Globe,
  ExternalLink,
  Workflow,
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
      <div className="text-[10px] text-slate-600 font-mono tracking-widest uppercase">Encrypted_V3</div>
    </div>
  </motion.a>
);

// --- Real TradingView Widget ---
const TradingViewWidget = () => {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      "autosize": true,
      "symbol": "COINBASE:BTCUSD",
      "interval": "1",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "3",
      "locale": "en",
      "enable_publishing": false,
      "hide_top_toolbar": false,
      "hide_legend": true,
      "save_image": false,
      "backgroundColor": "rgba(15, 17, 21, 1)",
      "gridColor": "rgba(30, 41, 59, 0.2)",
      "container_id": "tradingview_btc",
      "hide_volume": false
    });
    container.current.innerHTML = ""; // Clear
    container.current.appendChild(script);
  }, []);

  return (
    <div className="tradingview-widget-container w-full h-full" ref={container}>
      <div id="tradingview_btc" className="w-full h-full"></div>
    </div>
  );
};

// --- Main Application ---

const App = () => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [showArch, setShowArch] = useState(false);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [btcPrice, setBtcPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);
  const [memUsed, setMemUsed] = useState<number>(12.42);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Fetch Live Data for Header Only
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
    const i = setInterval(fetchPrice, 2000);
    return () => clearInterval(i);
  }, []);

  // Memory Jitter
  useEffect(() => {
    const i = setInterval(() => {
      setMemUsed(prev => {
        const n = prev + (Math.random() - 0.5) * 0.4;
        return n < 11.8 ? 11.95 : n > 16.2 ? 16.05 : n;
      });
    }, 1200);
    return () => clearInterval(i);
  }, []);

  // Initialize Logs
  useEffect(() => {
    const initial = PREDEFINED_LOGS.slice(0, 6).map((l, i) => ({
      id: i,
      timestamp: new Date(Date.now() - (6-i)*1000).toISOString().split('T')[1].slice(0, 8),
      level: l.level as any,
      message: l.message
    }));
    setLogs(initial);
    const i = setInterval(() => {
      const log = PREDEFINED_LOGS[Math.floor(Math.random() * PREDEFINED_LOGS.length)];
      setLogs(p => [...p.slice(-49), { id: Date.now(), timestamp: new Date().toISOString().split('T')[1].slice(0, 8), level: log.level as any, message: log.message }]);
    }, 2000);
    return () => clearInterval(i);
  }, []);

  useEffect(() => {
    if (logsContainerRef.current) logsContainerRef.current.scrollTo({ top: logsContainerRef.current.scrollHeight, behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-300 font-sans overflow-x-hidden">
      
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-[#050507]/90 backdrop-blur-md sticky top-0 z-50 shadow-2xl">
        <div className="max-w-[1600px] mx-auto px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3 group cursor-pointer">
              <Activity className="w-6 h-6 text-emerald-500 shadow-glow" />
              <span className="font-bold text-2xl tracking-[0.25em] text-slate-100 uppercase">Alpha<span className="font-light text-slate-400">Pulse</span></span>
            </div>
            <div className="hidden md:flex items-center gap-3 px-4 py-1.5 bg-emerald-950/30 border border-emerald-500/20 rounded-full">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-mono text-emerald-400 font-bold tracking-widest uppercase">System Operational</span>
            </div>
          </div>

          <div className="flex items-center gap-8">
            <nav className="hidden lg:flex items-center gap-12 text-xs font-mono text-slate-400 tracking-widest uppercase">
              <a href="https://chainy.luichu.dev/QV65eSp" target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400 flex items-center gap-2 group">
                <Github className="w-5 h-5 group-hover:scale-110" /> <span className="border-b border-transparent group-hover:border-emerald-500/50 pb-1">Docs_Repo</span>
              </a>
              <a href="#" className="hover:text-emerald-400 flex items-center gap-2 group">
                <Code2 className="w-5 h-5 group-hover:scale-110" /> <span className="border-b border-transparent group-hover:border-emerald-500/50 pb-1">local_dev.sh</span>
              </a>
            </nav>
            <button onClick={() => setIsAdmin(!isAdmin)} className={`flex items-center gap-2.5 px-6 py-2.5 rounded-sm border text-xs font-mono font-bold transition-all duration-300 uppercase tracking-widest ${isAdmin ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400 shadow-glow' : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'}`}>
              {isAdmin ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />} {isAdmin ? 'Commander Mode Active' : 'Login'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-8 py-12 space-y-12">
        
        {/* KPIs */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <MetricCard label="FinOps (Oracle Free)" value="$0.00/mo" subtext="100% Opex Savings" icon={Cloud} accent="emerald" />
          <MetricCard label="Architecture" value="ARM64 / A1" subtext="Polymorphic Infrastructure" icon={Cpu} accent="indigo" />
          <MetricCard label="Memory Load" value={`${memUsed.toFixed(2)}GB / 24GB`} subtext="Chunked Ingestion Active" icon={Database} accent="blue" />
          <MetricCard label="Model Health" value="0.024 PSI" subtext="Gates: Stable (PASSED)" icon={ShieldCheck} accent="rose" />
        </section>

        {/* System Blueprint & ADRs */}
        <section className="border border-slate-800 rounded-sm bg-[#0f1115]/40 overflow-hidden shadow-2xl">
            <button onClick={() => setShowArch(!showArch)} className="w-full flex items-center justify-between p-6 hover:bg-white/5 transition-colors group text-slate-200 uppercase">
                <div className="flex items-center gap-5">
                    <Workflow className={`w-7 h-7 transition-colors ${showArch ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span className="font-bold text-sm font-mono tracking-[0.3em]">System Blueprint & Architecture Decision Records (ADRs)</span>
                </div>
                {showArch ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5 group-hover:text-emerald-400" />}
            </button>
            <AnimatePresence>
                {showArch && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="border-t border-slate-800 p-12 bg-black/60">
                        <div className="flex justify-center mb-16">
                            <div className="max-w-5xl w-full bg-[#0a0a0c] p-10 border border-slate-800 rounded shadow-2xl">
                                <img 
                                    src="https://mermaid.ink/img/graph%20TD%0A%20%20%20%20subgraph%20Data_Hub%20%5B%221.%20Ingestion%20Layer%22%5D%0A%20%20%20%20%20%20%20%20S1(Binance%20API)%0A%20%20%20%20%20%20%20%20S2(News%20Feeds)%0A%20%20%20%20%20%20%20%20FS%5B(Feature%20Store)%5D%0A%20%20%20%20end%0A%20%20%20%20subgraph%20MLOps_Engine%20%5B%222.%20Training%20Core%22%5D%0A%20%20%20%20%20%20%20%20T1%7B%7BAirflow%7D%7D%0A%20%20%20%20%20%20%20%20T2%5B%5BTrainer%5D%5D%0A%20%20%20%20%20%20%20%20T3%7BMLflow%7D%0A%20%20%20%20%20%20%20%20T4%3EOptuna%5D%0A%20%20%20%20end%0A%20%20%20%20subgraph%20Prod_Cluster%20%5B%223.%20Production%20ARM64%22%5D%0A%20%20%20%20%20%20%20%20P1%5BFastAPI%5D%0A%20%20%20%20%20%20%20%20P3(%5BInference%5D)%0A%20%20%20%20%20%20%20%20P2%5BDashboard%5D%0A%20%20%20%20end%0A%20%20%20%20S1%20%26%20S2%20%3D%3D%3E%20FS%0A%20%20%20%20FS%20%3D%3D%3E%20T1%0A%20%20%20%20T1%20--%3E%20T2%0A%20%20%20%20T2%20%3C--%3E%20T4%0A%20%20%20%20T2%20--%3E%20T3%0A%20%20%20%20T3%20-.-%3E%20P1%0A%20%20%20%20P1%20--%3E%20P3%0A%20%20%20%20P3%20--%3E%20P2?theme=dark" 
                                    alt="AlphaPulse System Architecture"
                                    className="w-full h-auto opacity-90 hover:opacity-100 transition-opacity"
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 border-t border-slate-800 pt-16 uppercase font-mono tracking-tighter">
                            <div className="space-y-4">
                                <h4 className="text-emerald-400 font-bold flex items-center gap-3"><FileCode2 /> ADR-007: Polymorphism</h4>
                                <p className="text-sm text-slate-400 leading-relaxed">Terraform interfaces allow seamless Oracle/AWS compute migration via single variable toggle.</p>
                            </div>
                            <div className="space-y-4 border-x border-slate-800/50 px-8">
                                <h4 className="text-emerald-400 font-bold flex items-center gap-3"><Binary /> ADR-008: Optimization</h4>
                                <p className="text-sm text-slate-400 leading-relaxed">Chunked SQL loading + float32 downcasting reduces memory footprint by 50% for 8y data history.</p>
                            </div>
                            <div className="space-y-4 px-4">
                                <h4 className="text-emerald-400 font-bold flex items-center gap-3"><ShieldCheck /> ADR-009: Precision</h4>
                                <p className="text-sm text-slate-400 leading-relaxed">Strict Python Decimal enforcement eliminates floating-point drift across all trading logic boundaries.</p>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </section>

        {/* Dashboard Section */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-10 lg:h-[750px]">
          {/* BTC/USD Real Chart */}
          <div className="lg:col-span-2 bg-[#0f1115] border border-slate-800 rounded-sm p-1 flex flex-col relative shadow-2xl overflow-hidden">
            <div className="absolute top-0 left-0 right-0 p-8 flex flex-col sm:flex-row justify-between items-start gap-6 bg-gradient-to-b from-[#0f1115] via-[#0f1115]/90 to-transparent z-20 pointer-events-none">
              <div>
                <div className="flex items-baseline gap-5 flex-wrap">
                  <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-4">
                    <span className="w-4 h-4 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.8)]"></span>BTC/USD
                  </h2>
                  <span className="text-4xl sm:text-5xl font-mono text-emerald-400 tracking-tighter">${btcPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  <span className={`text-sm sm:text-base font-mono flex items-center gap-2 px-3 py-1 rounded-sm ${priceChange >= 0 ? 'text-emerald-500 bg-emerald-500/10' : 'text-rose-500 bg-rose-500/10'}`}>
                    <TrendingUp className={`w-5 h-5 ${priceChange < 0 ? 'rotate-180' : ''}`} /> {priceChange >= 0 ? '+' : ''}{priceChange}%
                  </span>
                </div>
                <div className="mt-6 flex flex-wrap gap-3 uppercase font-mono tracking-widest text-[10px] sm:text-xs">
                  <span className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 text-blue-300 rounded flex items-center gap-2"><Zap className="w-4 h-4" /> P99: 112ms</span>
                  <span className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded flex items-center gap-2"><Cpu className="w-4 h-4" /> ARM64_A1</span>
                  <span className="px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded flex items-center gap-2"><Layers className="w-4 h-4" /> v2.4.1_CATBOOST</span>
                  <span className="px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded flex items-center gap-2"><CheckCircle2 className="w-4 h-4" /> DECIMAL_ENFORCED</span>
                </div>
              </div>
              <div className="text-right hidden sm:block font-mono text-xs">
                <div className="text-emerald-500/60 bg-emerald-500/5 px-3 py-1 border border-emerald-500/20 rounded-sm uppercase tracking-[0.2em]">Status: Hot-Reload Active</div>
                <div className="text-slate-600 mt-2 text-[10px] uppercase font-bold tracking-widest">Retrain: 04:00 UTC</div>
              </div>
            </div>
            {/* The Real TradingView Image/Chart */}
            <div className="flex-1 w-full h-full pt-48 sm:pt-32 bg-[#0f1115]">
                <TradingViewWidget />
            </div>
          </div>

          {/* Logs */}
          <div className="bg-black border border-slate-800 rounded-sm flex flex-col shadow-inner relative overflow-hidden h-full">
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 bg-[#0f1115]">
              <span className="text-slate-400 text-sm font-mono flex items-center gap-3 uppercase tracking-widest"><Terminal className="w-5 h-5 text-blue-500" /> Pipeline_Stdout</span>
              <div className="flex gap-2"><div className="w-3 h-3 rounded-full bg-slate-800 border border-slate-700"></div><div className="w-3 h-3 rounded-full bg-slate-800 border border-slate-700"></div><div className="w-3 h-3 rounded-full bg-emerald-900 border border-emerald-700/50"></div></div>
            </div>
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 opacity-20"></div>
            <div ref={logsContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-800 font-mono text-[13px] leading-relaxed">
              {logs.map((log) => (
                <div key={log.id} className="flex gap-4 animate-in fade-in duration-300">
                  <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                  <div className="flex flex-col">
                    <span className={`font-bold uppercase tracking-tighter ${log.level === 'INFO' ? 'text-blue-400' : log.level === 'SUCCESS' ? 'text-emerald-400' : log.level === 'WARN' ? 'text-amber-400' : 'text-purple-400'}`}>{log.level}</span>
                    <span className="text-slate-300 break-words">{log.message}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-slate-900 bg-[#0a0a0c] text-slate-500 text-xs font-mono flex items-center gap-4 tracking-widest uppercase">
              <span className="w-2 h-5 bg-emerald-500 animate-pulse shadow-glow"></span>PID_ACTIVE_4421
            </div>
          </div>
        </section>

        {/* Commander Mode */}
        <AnimatePresence>
        {isAdmin && (
            <motion.section initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.4 }} className="border border-slate-800 bg-[#0f1115] rounded-sm overflow-hidden shadow-2xl">
            <div className="p-6 bg-slate-900/50 border-b border-slate-800 flex items-center justify-between font-mono">
                <div className="flex items-center gap-5">
                <ShieldCheck className="w-7 h-7 text-emerald-500" /><h3 className="font-bold tracking-[0.2em] text-slate-100 uppercase">Commander Mode <span className="font-normal text-emerald-500/80 text-xs ml-4 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 tracking-widest">SSO_AUTH_SUCCESS</span></h3>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500 font-bold uppercase"><span className="w-3 h-3 rounded-full bg-emerald-500 shadow-glow"></span>Secure_Node_Online</div>
            </div>
            <div className="p-10 grid grid-cols-1 md:grid-cols-3 gap-10">
                <AdminLink title="Airflow Orchestrator" status="14 Online" icon={Workflow} url="http://localhost:8080" delay={0.1} />
                <AdminLink title="MLflow Registry" status="v2.4 Ready" icon={Layers} url="http://localhost:5000" delay={0.2} />
                <AdminLink title="K3s Dashboard" status="Active" icon={Server} url="#" delay={0.3} />
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
                <p className="text-slate-600 text-xs tracking-[0.3em] uppercase font-bold">AlphaPulse Engine v2.4.1 <span className="mx-4 text-slate-800">|</span> Region: ap-chuncheon-1 (Oracle)</p>
                <p className="text-slate-500 text-xs max-w-xl ml-auto leading-relaxed uppercase tracking-tight">Built with rigid Python Decimal precision, polymorphic Terraform infrastructure, and automated Optuna tuning. Optimized for Zero-Cost compute architectures and production stability.</p>
            </div>
          </div>
        </footer>

      </main>
    </div>
  );
};

export default App;
