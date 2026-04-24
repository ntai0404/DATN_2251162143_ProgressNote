"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { searchService, adminService } from "@/services/api";
import { 
  Bot, User, Send, Trash2, GraduationCap, University, Scale, 
  Search, CheckCircle2, AlertCircle, Loader2, Settings, FileText, Play, Eye, Database, Filter, ChevronRight
} from "lucide-react";

export default function SmartTutorPage() {
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [adminSearch, setAdminSearch] = useState(""); 
  const [isSearching, setIsSearching] = useState(false);
  const [citations, setCitations] = useState([]);
  const [isOnline, setIsOnline] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  
  // Admin States
  const [adminTab, setAdminTab] = useState("ocr-task"); 
  const [adminFiles, setAdminFiles] = useState([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [selectedOCRMode, setSelectedOCRMode] = useState("chandra"); 
  const [previewContent, setPreviewContent] = useState("");
  const [previewFileName, setPreviewFileName] = useState("");
  const [fileFilter, setFileFilter] = useState("all"); 

  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isSearching]);

  useEffect(() => {
    const init = async () => {
      try {
        const health = await searchService.checkHealth();
        setIsOnline(health.status === "ok");
        if (isAdmin) loadAdminFiles();
      } catch (e) { setIsOnline(false); }
    };
    init();
  }, [isAdmin]);

  const loadAdminFiles = async () => {
    setIsLoadingFiles(true);
    try {
      const files = await adminService.listFiles();
      setAdminFiles(files);
    } catch (e) { console.error(e); }
    finally { setIsLoadingFiles(false); }
  };

  const filteredFiles = useMemo(() => {
    const kw = adminSearch.trim().toLowerCase();
    return adminFiles.filter(f => {
      const matchSearch = !kw || f.name.toLowerCase().includes(kw);
      let matchType = true;
      if (fileFilter === "pdf") matchType = f.type === "PDF";
      else if (fileFilter === "docx") matchType = (f.type === "DOCX" || f.type === "DOC" || f.type === "FILE");
      else if (fileFilter === "ocr-done") matchType = f.has_ocr;
      
      return matchSearch && matchType;
    });
  }, [adminFiles, fileFilter, adminSearch]);

  const handleSend = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!chatInput.trim() || isSearching) return;
    const query = chatInput;
    setChatInput("");
    setMessages((prev) => [...prev, { type: "user", content: query }]);
    setIsSearching(true);
    try {
      const data = await searchService.search(query);
      const results = data.results || [];
      if (results.length === 0) {
        setMessages((prev) => [...prev, { type: "ai", content: "Rất tiếc, tôi không tìm thấy thông tin phù hợp." }]);
        setCitations([]);
      } else {
        const bestHit = results[0];
        const responseText = `**${bestHit.title}**\n\n${bestHit.content}\n\n---\n*Hybrid Score: ${bestHit.score.toFixed(4)}*`;
        setMessages((prev) => [...prev, { type: "ai", content: responseText }]);
        setCitations(results);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { type: "ai", content: "⚠️ Lỗi: Không thể kết nối Search API." }]);
    } finally { setIsSearching(false); }
  };

  const triggerOCR = async (file) => {
    try {
      await adminService.triggerOCR(file.path, selectedOCRMode);
      alert(`Đã kích hoạt [${selectedOCRMode.toUpperCase()}] OCR cho ${file.name}`);
      setTimeout(loadAdminFiles, 1000);
    } catch (e) { alert("Lỗi OCR"); }
  };

  const viewOCR = async (fileName) => {
    try {
      setPreviewFileName(fileName);
      const res = await adminService.getOCRContent(fileName);
      setPreviewContent(res.content);
      setAdminTab("ocr-results");
    } catch (e) { alert("Kết quả OCR chưa được nạp hoặc file đang xử lý."); }
  };

  const triggerEmbed = async (fileName) => {
    try {
      await adminService.triggerEmbed(fileName);
      alert(`Đã bắt đầu nạp tri thức cho file ${fileName}`);
    } catch (e) { alert("Lỗi Embedding"); }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans overflow-hidden">
      {/* Sidebar - Cố định */}
      <aside className="w-64 bg-[#0f172a] text-white flex flex-col shadow-2xl z-20 flex-shrink-0">
        <div className="p-8 border-b border-slate-800 flex items-center gap-3">
          <div className="p-2 bg-blue-500 rounded-lg shadow-lg">
            <GraduationCap size={20} />
          </div>
          <h1 className="text-lg font-black tracking-tight text-white uppercase">Smart Tutor</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2 mt-4 overflow-y-auto">
          <button onClick={() => setIsAdmin(false)} className={`flex items-center gap-3 w-full p-4 text-sm font-bold rounded-2xl transition-all ${!isAdmin ? 'bg-blue-600 shadow-xl text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
            <University size={18} /> Sinh viên tra cứu
          </button>
          <button onClick={() => setIsAdmin(true)} className={`flex items-center gap-3 w-full p-4 text-sm font-bold rounded-2xl transition-all ${isAdmin ? 'bg-emerald-600 shadow-xl text-white' : 'text-slate-400 hover:bg-slate-800'}`}>
            <Settings size={18} /> Quản trị dữ liệu
          </button>
        </nav>
        <div className="p-6 border-t border-slate-800">
           <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              <div className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
              {isOnline ? 'System Online' : 'System Offline'}
           </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col bg-white relative min-w-0">
        <header className="h-16 px-10 flex items-center justify-between border-b border-slate-100 bg-white/80 backdrop-blur-md flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-300">TLU v3.5</span>
            <ChevronRight size={14} className="text-slate-200" />
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">{isAdmin ? adminTab.replace('-', ' ') : 'Search Console'}</span>
          </div>
        </header>

        {isAdmin ? (
          <div className="flex-1 flex flex-col bg-[#f8fafc] overflow-hidden">
            {/* Horizontal Tabs - Luôn cố định phía trên */}
            <div className="px-10 py-4 bg-white border-b border-slate-200 flex flex-wrap items-center justify-between gap-4 flex-shrink-0">
              <div className="flex gap-8">
                <button onClick={() => setAdminTab("ocr-task")} className={`pb-2 text-sm font-bold transition-all border-b-2 ${adminTab === 'ocr-task' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-slate-400 hover:text-slate-600'}`}>1. TASK BẮN FILE OCR</button>
                <button onClick={() => setAdminTab("ocr-results")} className={`pb-2 text-sm font-bold transition-all border-b-2 ${adminTab === 'ocr-results' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-slate-400 hover:text-slate-600'}`}>2. KẾT QUẢ & EMBED</button>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input type="text" placeholder="Tìm file..." className="pl-9 pr-4 py-1.5 bg-slate-50 border-none text-[10px] font-bold text-slate-600 rounded-lg focus:ring-2 focus:ring-emerald-500/20 w-40 md:w-56" value={adminSearch} onChange={(e) => setAdminSearch(e.target.value)} />
                </div>
                <select className="bg-slate-50 border-none text-[10px] font-bold text-slate-600 rounded-lg px-3 py-1.5 focus:ring-0" value={fileFilter} onChange={(e) => setFileFilter(e.target.value)}>
                  <option value="all">TẤT CẢ FILE</option>
                  <option value="pdf">CHỈ PDF</option>
                  <option value="docx">CHỈ DOCX/FILE</option>
                  <option value="ocr-done">ĐÃ OCR</option>
                </select>
              </div>
            </div>

            {/* Content Area - Phải có scroll ở đây */}
            <div className="flex-1 overflow-y-auto p-4 md:p-10">
              {adminTab === "ocr-task" && (
                <div className="max-w-5xl mx-auto space-y-6">
                  <div className="flex flex-wrap justify-between items-center bg-white p-6 rounded-3xl border border-slate-200 shadow-sm gap-4">
                    <h2 className="text-lg font-bold text-slate-800">Cấu hình luồng OCR</h2>
                    <div className="flex bg-slate-100 p-1 rounded-xl">
                      <button onClick={() => setSelectedOCRMode("chandra")} className={`px-4 md:px-6 py-2 text-[10px] font-black rounded-lg transition-all ${selectedOCRMode === "chandra" ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-400'}`}>CHANDRA (ALL)</button>
                      <button onClick={() => setSelectedOCRMode("direct")} className={`px-4 md:px-6 py-2 text-[10px] font-black rounded-lg transition-all ${selectedOCRMode === "direct" ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-400'}`}>DIRECT (PDF)</button>
                    </div>
                  </div>

                  {isLoadingFiles ? (
                    <div className="flex justify-center p-20"><Loader2 className="animate-spin text-slate-300" size={40} /></div>
                  ) : (
                    <div className="grid grid-cols-1 gap-3">
                      {filteredFiles.map((f, i) => (
                        <div key={i} className="group bg-white p-5 border border-slate-200 rounded-3xl flex flex-wrap items-center justify-between hover:border-emerald-200 hover:shadow-xl hover:shadow-emerald-500/5 transition-all gap-4">
                          <div className="flex items-center gap-4">
                            <div className={`p-3 rounded-2xl ${f.type === 'PDF' ? 'bg-blue-50 text-blue-500' : 'bg-orange-50 text-orange-500'}`}>
                              <FileText size={20} />
                            </div>
                            <div>
                              <div className="text-sm font-bold text-slate-800 line-clamp-1">{f.name}</div>
                              <div className="text-[9px] font-black text-slate-300 uppercase tracking-widest">{f.type} • {f.has_ocr ? 'READY' : 'PENDING'}</div>
                            </div>
                          </div>
                          <button onClick={() => triggerOCR(f)} className="px-6 py-2.5 bg-[#0f172a] text-white text-[10px] font-black rounded-xl hover:bg-emerald-600 transition-all flex-shrink-0">BẮN FILE OCR</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {adminTab === "ocr-results" && (
                <div className="max-w-6xl mx-auto h-full flex flex-col">
                   {previewContent ? (
                      <div className="flex-1 flex flex-col bg-white border border-slate-200 rounded-[2rem] overflow-hidden shadow-2xl min-h-[500px]">
                        <div className="px-8 py-4 bg-[#0f172a] text-white flex flex-wrap justify-between items-center gap-4">
                          <span className="text-xs font-bold font-mono truncate max-w-xs md:max-w-md">FILE: {previewFileName}.md</span>
                          <div className="flex gap-4">
                             <button onClick={() => triggerEmbed(previewFileName)} className="px-4 py-1.5 bg-emerald-500 text-[10px] font-bold rounded-lg hover:bg-emerald-400 transition-all flex items-center gap-2"><Database size={12}/> EMBED</button>
                             <button onClick={() => setPreviewContent("")} className="text-slate-400 hover:text-white text-xs font-bold">ĐÓNG</button>
                          </div>
                        </div>
                        <textarea readOnly className="flex-1 p-10 text-sm font-mono bg-slate-50/50 text-slate-700 outline-none resize-none leading-loose" value={previewContent} />
                      </div>
                   ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredFiles.filter(f => f.has_ocr).map((f, i) => (
                          <div key={i} className="bg-white p-6 border border-slate-200 rounded-[1.5rem] flex flex-col gap-4 hover:shadow-lg transition-all group">
                            <div className="flex items-center justify-between gap-4">
                              <span className="text-sm font-bold text-slate-800 truncate flex-1">{f.name}</span>
                              <span className="text-[9px] font-black bg-emerald-50 text-emerald-600 px-2 py-1 rounded-md flex-shrink-0">OCR DONE</span>
                            </div>
                            <button onClick={() => viewOCR(f.name)} className="w-full py-3 bg-slate-50 group-hover:bg-blue-600 group-hover:text-white text-slate-400 text-[10px] font-bold rounded-xl transition-all flex items-center justify-center gap-2 flex-shrink-0"><Eye size={14} /> XEM & EMBED</button>
                          </div>
                        ))}
                        {filteredFiles.filter(f => f.has_ocr).length === 0 && (
                          <div className="col-span-full p-20 text-center text-slate-300 font-bold uppercase tracking-widest">Chưa có kết quả OCR nào được nạp.</div>
                        )}
                      </div>
                   )}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* USER VIEW */
          <div className="flex-1 flex overflow-hidden">
            <div className="flex-1 flex flex-col bg-white">
              <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 md:p-12 space-y-8 bg-[#fcfcfc]">
                {messages.length === 0 && (
                  <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
                    <University size={64} className="mb-4 text-slate-200" />
                    <p className="text-sm font-bold italic text-slate-400 tracking-widest uppercase">Smart Tutor Hybrid System</p>
                  </div>
                )}
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[85%] md:max-w-[75%] p-6 rounded-[1.5rem] shadow-sm leading-relaxed ${
                      msg.type === "user" ? "bg-[#0f172a] text-white rounded-tr-none shadow-xl shadow-slate-900/10" : "bg-white border border-slate-100 text-slate-800 rounded-tl-none"
                    }`}>
                      <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  </div>
                ))}
                {isSearching && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-slate-50 p-6 rounded-[1.5rem] rounded-tl-none flex items-center gap-4 shadow-sm">
                      <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-xs font-black text-slate-300 uppercase tracking-widest">Searching...</span>
                    </div>
                  </div>
                )}
              </div>
              <footer className="p-4 md:p-8 bg-white border-t border-slate-50 flex-shrink-0">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto relative group">
                  <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Hỏi về quy chế, học bổng, nội quy..." className="w-full pl-6 md:pl-8 pr-16 py-4 md:py-5 bg-slate-100/50 border-none rounded-3xl focus:outline-none focus:ring-4 focus:ring-blue-500/5 text-sm font-bold transition-all placeholder:text-slate-300 group-hover:bg-slate-100" />
                  <button type="submit" className="absolute right-2 top-2 p-3 md:p-4 bg-[#0f172a] text-white rounded-[1.2rem] shadow-2xl hover:bg-blue-600 transition-all active:scale-95"><Send size={20} /></button>
                </form>
              </footer>
            </div>
            <aside className="hidden lg:flex w-96 bg-slate-50/50 border-l border-slate-100 flex-col flex-shrink-0">
              <div className="p-8 border-b border-slate-100 bg-white">
                 <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Minh chứng lai</h4>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {citations.map((cite, i) => (
                  <div key={i} className="bg-white p-6 rounded-[1.8rem] border border-slate-100 shadow-sm hover:shadow-xl transition-all duration-300 group">
                    <div className="flex items-center gap-2 mb-4">
                       <div className="w-6 h-6 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center text-[10px] font-black">{i+1}</div>
                    </div>
                    <p className="text-xs text-slate-600 italic mb-4 leading-relaxed line-clamp-4 group-hover:line-clamp-none transition-all">"{cite.content}"</p>
                    <div className="grid grid-cols-3 gap-2 border-t border-slate-50 pt-4">
                       <div className="text-center"><p className="text-[8px] text-slate-300 font-bold uppercase">BM25</p><p className="text-[10px] font-black text-slate-800">{cite.bm25_score.toFixed(1)}</p></div>
                       <div className="text-center"><p className="text-[8px] text-slate-300 font-bold uppercase">Dense</p><p className="text-[10px] font-black text-slate-800">{cite.dense_score.toFixed(2)}</p></div>
                       <div className="text-center bg-blue-50 rounded-lg p-1"><p className="text-[8px] text-blue-400 font-bold uppercase">Vote</p><p className="text-[10px] font-black text-blue-600">{cite.score.toFixed(3)}</p></div>
                    </div>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
