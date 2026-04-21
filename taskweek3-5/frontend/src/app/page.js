"use client";

import { useState, useEffect, useRef } from "react";
import { searchService } from "@/services/api";
import { 
  Bot, 
  User, 
  Send, 
  Trash2, 
  GraduationCap, 
  University, 
  Scale, 
  Briefcase, 
  FileText, 
  Search,
  CheckCircle2,
  AlertCircle,
  Loader2
} from "lucide-react";

export default function SmartTutorPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [citations, setCitations] = useState([]);
  const [isOnline, setIsOnline] = useState(true);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isSearching]);

  useEffect(() => {
    const check = async () => {
      try {
        const health = await searchService.checkHealth();
        setIsOnline(health.status === "ok");
      } catch (e) {
        setIsOnline(false);
      }
    };
    check();
  }, []);

  const handleSend = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!input.trim() || isSearching) return;

    const query = input;
    setInput("");
    setMessages((prev) => [...prev, { type: "user", content: query }]);
    setIsSearching(true);

    try {
      const data = await searchService.search(query);
      const results = data.results || [];

      if (results.length === 0) {
        setMessages((prev) => [...prev, { 
          type: "ai", 
          content: "Rất tiếc, tôi không tìm thấy thông tin chính xác trong hệ thống quy chế hiện có." 
        }]);
        setCitations([]);
      } else {
        const bestHit = results[0];
        // Clean up the text for better display
        const cleanContent = bestHit.content.replace(/dạng ảnh, cần OCR\.*/gi, "").trim();
        
        const responseText = `**${bestHit.title}**\n\n${cleanContent.substring(0, 450)}...\n\n---\n*Ghi chú: Thông tin trên được trích xuất từ quy chế chính thức của TLU.*`;
        
        setMessages((prev) => [...prev, { type: "ai", content: responseText }]);
        setCitations(results);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { type: "ai", content: "⚠️ Lỗi: Không thể kết nối Backend." }]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-white border-r border-slate-200 hidden md:flex flex-col">
        <div className="p-6 border-b border-slate-100 flex items-center gap-3 text-blue-600">
          <GraduationCap size={28} />
          <h1 className="text-xl font-bold">Smart Tutor</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <div className="text-[10px] uppercase font-bold text-slate-400 px-2">Knowledge Rings</div>
          <button className="flex items-center gap-3 w-full p-3 text-sm font-semibold text-blue-600 bg-blue-50 rounded-xl">
            <University size={18} /> Quy chế TLU
          </button>
          <button className="flex items-center gap-3 w-full p-3 text-sm font-semibold text-slate-500 hover:bg-slate-50 rounded-xl">
            <Scale size={18} /> Luật Giáo dục
          </button>
        </nav>
        <div className="p-4 border-t border-slate-100 italic text-[10px] text-slate-400 text-center">
          TLU Project v3.5
        </div>
      </aside>

      {/* Chat Area */}
      <main className="flex-1 flex flex-col bg-white">
        <header className="h-16 px-8 flex items-center justify-between border-b border-slate-100 shadow-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
              {isOnline ? 'System Online' : 'System Offline'}
            </span>
          </div>
          <button onClick={() => setMessages([])} className="p-2 text-slate-400 hover:text-red-500"><Trash2 size={18} /></button>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto p-8 space-y-6 bg-[#fcfcfc]">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <Search className="text-slate-200 mb-4" size={64} />
              <h3 className="text-xl font-bold text-slate-400 italic">Bạn cần tra cứu quy chế gì?</h3>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"} animate-fade-in`}>
              <div className={`max-w-[80%] p-4 rounded-2xl shadow-sm ${
                msg.type === "user" ? "bg-blue-600 text-white rounded-tr-none" : "bg-white border border-slate-200 text-slate-800 rounded-tl-none"
              }`}>
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
              </div>
            </div>
          ))}
          {isSearching && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 p-4 rounded-2xl rounded-tl-none flex items-center gap-3">
                <Loader2 size={16} className="animate-spin text-blue-600" />
                <span className="text-xs italic text-slate-500">Đang lục tìm quy chế...</span>
              </div>
            </div>
          )}
        </div>

        <footer className="p-6 border-t border-slate-100">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto relative">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Nhập câu hỏi tại đây..."
              className="w-full pl-6 pr-14 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm font-medium"
            />
            <button type="submit" className="absolute right-2 top-2 p-3 bg-blue-600 text-white rounded-xl shadow-lg shadow-blue-100">
              <Send size={18} />
            </button>
          </form>
        </footer>
      </main>

      {/* Citation Sidebar */}
      <aside className="w-80 bg-slate-50 border-l border-slate-200 hidden lg:flex flex-col">
        <div className="p-6 border-b border-slate-200 bg-white font-black text-[10px] text-slate-400 uppercase tracking-widest">
          Minh chứng pháp lý
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {citations.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center opacity-20"><AlertCircle size={40} /></div>
          ) : (
            citations.map((cite, i) => (
              <div key={i} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="text-[10px] font-bold text-blue-600 mb-2 uppercase tracking-tighter">Tri thức #{i+1}</div>
                <p className="text-[11px] text-slate-600 italic line-clamp-3 mb-3">"{cite.content}"</p>
                <div className="flex justify-between border-t pt-2 text-[10px] font-black text-slate-400">
                  <span>TRANG {cite.page || 'N/A'}</span>
                  <span className="text-blue-500">ĐIỀU {cite.article_id || 'N/A'}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </aside>
    </div>
  );
}
