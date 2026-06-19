import React, { useState, useEffect, useRef } from 'react';
import {
  Send, Copy, Check, Plus, Trash2, LogOut, ChevronDown,
  AlertCircle, MessageSquare, Sparkles, FileText, Mail, Lightbulb, Bot,
  Image, Paperclip, Mic, ArrowUp, Compass, Download
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { showToast } from '../components/ProtectedRoute';

/* ─────────────── TYPING INDICATOR ─────────────── */
const TypingIndicator = ({ isImage }) => (
  <div className="flex items-start gap-3 bubble-enter">
    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shrink-0 shadow-saas-sm">
      <Bot className="w-3.5 h-3.5 text-white" />
    </div>
    <div className="bg-white border border-border-light rounded-2xl rounded-tl-sm px-4 py-3 shadow-saas-sm">
      <div className="flex items-center gap-2 mb-1.5">
        <div className="flex gap-1">
          <span className="w-2 h-2 rounded-full bg-primary dot-1 inline-block" />
          <span className="w-2 h-2 rounded-full bg-blue-400 dot-2 inline-block" />
          <span className="w-2 h-2 rounded-full bg-primary dot-3 inline-block" />
        </div>
        <span className="text-xs text-text-muted font-medium">
          {isImage ? 'Generating image...' : 'Thinking...'}
        </span>
      </div>
      <div className="h-1.5 rounded-full shimmer-bg w-32" />
    </div>
  </div>
);

/* ─────────────── PROVIDER DATA ─────────────── */
const providerLabels = {
  gemini: 'Gemini', groq: 'Groq', openrouter: 'OpenRouter',
  cerebras: 'Cerebras', mistral: 'Mistral', pollinations: 'Pollinations',
};
// Badge colors per provider
const providerColors = {
  gemini:     'bg-blue-50   text-blue-600   border-blue-200',
  groq:       'bg-purple-50 text-purple-600 border-purple-200',
  openrouter: 'bg-orange-50 text-orange-600 border-orange-200',
  cerebras:   'bg-pink-50   text-pink-600   border-pink-200',
  mistral:    'bg-cyan-50   text-cyan-600   border-cyan-200',
  pollinations: 'bg-emerald-50 text-emerald-600 border-emerald-200',
};

/* ─────────────── PILL SELECT ─────────────── */
function PillSelect({ label, value, options, onChange, optionLabel }) {
  return (
    <div className="flex items-center gap-1">
      {label && <span className="text-xs text-text-muted font-medium hidden sm:block">{label}:</span>}
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="appearance-none provider-pill py-0.5 pl-2 text-[10px] font-semibold cursor-pointer outline-none"
          style={{ paddingRight: '22px' }}
        >
          {options.map((o) => (
            <option key={o} value={o}>{optionLabel ? optionLabel(o) : o}</option>
          ))}
        </select>
        <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-2.5 h-2.5 text-primary pointer-events-none" />
      </div>
    </div>
  );
}

/* ─────────────── CHAT MESSAGE ─────────────── */
function ChatMessage({ msg, user, onCopy, copiedId }) {
  const isUser = msg.role === 'user';
  const initials = user?.name ? user.name.charAt(0).toUpperCase() : 'U';
  const badgeClass = providerColors[msg.provider] || 'bg-gray-50 text-gray-500 border-gray-200';

  return (
    <div className={`flex items-end gap-2.5 bubble-enter ${isUser ? 'justify-end' : 'justify-start'}`}>

      {/* AI avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shrink-0 mb-1 shadow-saas-sm">
          <Bot className="w-3.5 h-3.5 text-white" />
        </div>
      )}

      <div className="flex flex-col gap-1 max-w-[75%] sm:max-w-[65%]">
        {/* Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-gradient-to-br from-primary to-blue-600 text-white rounded-br-sm shadow-saas-md user-bubble'
              : 'bg-white text-text-primary border border-border-light rounded-bl-sm shadow-saas-sm assistant-bubble'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{msg.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none break-words prose-gray">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  img: ({ node, ...props }) => (
                    <div className="relative group/image my-2 rounded-lg overflow-hidden border border-slate-200 shadow-sm max-w-[280px] sm:max-w-[360px] w-full bg-slate-50">
                      <img
                        {...props}
                        className="w-full h-auto object-cover max-h-[280px] sm:max-h-[360px] block"
                        alt={props.alt || "Generated Image"}
                      />
                      <a
                        href={props.src}
                        download
                        target="_blank"
                        rel="noopener noreferrer"
                        className="absolute bottom-2 right-2 p-1.5 bg-black/60 hover:bg-black/80 text-white rounded-lg backdrop-blur-sm transition-all shadow hover:scale-105 flex items-center justify-center gap-1.5"
                        title="Download Image"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span className="text-[10px] font-semibold pr-0.5 hidden sm:inline">Download</span>
                      </a>
                    </div>
                  )
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* AI actions row */}
        {!isUser && (
          <div className="flex items-center gap-2 px-1 flex-wrap">
            <button
              onClick={() => onCopy(msg.content, msg.id)}
              className="flex items-center gap-1 text-xs text-text-muted hover:text-text-primary transition-colors"
            >
              {copiedId === msg.id
                ? <><Check className="w-3.5 h-3.5 text-emerald-500" /><span className="text-emerald-500">Copied</span></>
                : <><Copy className="w-3.5 h-3.5" /><span>Copy</span></>
              }
            </button>
            {msg.provider && (
              <span className={`text-[11px] px-2 py-0.5 border rounded-full font-medium ${badgeClass}`}>
                {providerLabels[msg.provider] || msg.provider}
              </span>
            )}
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0 mb-1 shadow-saas-sm">
          {initials}
        </div>
      )}
    </div>
  );
}

/* ─────────────── SUGGESTIONS POOL ─────────────── */
const suggestionsPool = [
  'Help me pack for my trip to Jaipur next week',
  'Compare leather sofas vs fabric sofas',
  'How to identify if the pashmina shawl I am buying is genuine?',
  'Explain quantum computing in simple terms for a ten-year-old',
  'Write a Python function to check if a word is a palindrome',
  'Suggest 5 healthy breakfast ideas that take less than 10 minutes',
  'What are some good team-building exercises for a remote engineering team?',
  'Explain the difference between SQL and NoSQL databases with examples',
  'Help me draft a professional email requesting a project deadline extension',
  'Suggest a week-long travel itinerary for exploring Kyoto, Japan',
  'How do I implement user authentication securely in a Node.js API?',
  'What are the main features of ES6 Javascript and why do we use them?',
  'Give me some tips for improving my public speaking skills',
  'Help me brainstorm names for a mobile app focused on mental health',
  'What is the difference between machine learning and deep learning?',
  'Write a short sci-fi story opening about a robot discovering feelings',
  'How does a browser render a webpage under the hood?',
  'Suggest some beginner-friendly projects for learning React',
];

/* ─────────────── MAIN CHATBOT ─────────────── */
export default function Chatbot({ user }) {
  const token = localStorage.getItem('token');

  const [sessions, setSessions]               = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages]               = useState([]);
  const [inputText, setInputText]             = useState('');
  const [lastMessages, setLastMessages]       = useState({});
  const [provider, setProvider]               = useState('mistral');
  const [model, setModel]                     = useState('open-mixtral-8x7b');
  const [modelsData, setModelsData]           = useState({ providers: [] });
  const [loading, setLoading]                 = useState(true);
  const [sending, setSending]                 = useState(false);
  const [copiedId, setCopiedId]               = useState(null);
  const [error, setError]                     = useState('');
  const [sidebarOpen, setSidebarOpen]         = useState(false);
  const [isImageMode, setIsImageMode]         = useState(false);

  // Filter enabled providers and active models for the current mode
  const availableProviders = (modelsData.providers || []).filter(p => 
    p.enabled && p.models.some(m => m.active && (isImageMode ? m.supports_image : m.supports_chat))
  );

  const currentProviderObj = availableProviders.find(p => p.name === provider);
  const availableModels = currentProviderObj 
    ? currentProviderObj.models.filter(m => m.active && (isImageMode ? m.supports_image : m.supports_chat))
    : [];

  // Selected provider/model correction effect
  useEffect(() => {
    if (availableProviders.length > 0) {
      const isCurrentProviderValid = availableProviders.some(p => p.name === provider);
      if (!isCurrentProviderValid) {
        const nextProvider = availableProviders[0].name;
        setProvider(nextProvider);
        const nextProviderObj = availableProviders[0];
        const nextModels = nextProviderObj.models.filter(m => m.active && (isImageMode ? m.supports_image : m.supports_chat));
        if (nextModels.length > 0) {
          setModel(nextModels[0].id);
        }
      } else {
        const models = currentProviderObj ? currentProviderObj.models.filter(m => m.active && (isImageMode ? m.supports_image : m.supports_chat)) : [];
        if (models.length > 0 && !models.some(m => m.id === model)) {
          setModel(models[0].id);
        }
      }
    }
  }, [isImageMode, modelsData, provider, model]);
  const [currentSuggestions, setCurrentSuggestions] = useState([]);

  const messagesEndRef = useRef(null);
  const inputRef       = useRef(null);
  const textareaRef    = useRef(null);
  const fileInputRef   = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      showToast(`Attached file: ${file.name}`, 'success');
    }
  };

  useEffect(() => {
    const shuffled = [...suggestionsPool].sort(() => 0.5 - Math.random());
    setCurrentSuggestions(shuffled.slice(0, 3));
  }, [activeSessionId]);

  /* ─── RENDER HELPER: INPUT FORM ─── */
  const renderInputForm = (isCentered) => {
    return (
      <form onSubmit={handleSend} className={isCentered ? "w-full max-w-lg px-4 mt-6" : "max-w-xl mx-auto w-full"}>
        <div className={`relative flex flex-col bg-white border border-slate-200 rounded-2xl p-2 px-3 focus-within:ring-4 transition-all
          ${isImageMode 
            ? 'focus-within:border-purple-400 focus-within:ring-purple-100/50' 
            : 'focus-within:border-blue-400 focus-within:ring-blue-100/50'
          }
          ${isCentered ? 'shadow-lg shadow-blue-500/5' : 'shadow-sm'}`}>
          
          {/* Subtle colorful glow line at the bottom of the container */}
          <div className={`absolute left-6 right-6 bottom-0 h-[2px] blur-[1px] rounded-full opacity-60 bg-gradient-to-r 
            ${isImageMode 
              ? 'from-purple-500 via-fuchsia-400 via-pink-400 to-rose-400' 
              : 'from-blue-400 via-emerald-400 via-purple-400 to-pink-500'
            }`} 
          />
          
          <textarea
            ref={(el) => { inputRef.current = el; textareaRef.current = el; }}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={sending}
            placeholder={isImageMode ? "Describe the image you want to generate..." : "Ask anything"}
            rows={1}
            className="w-full bg-transparent px-1.5 pt-1 pb-1 text-sm text-slate-800 placeholder:text-slate-400 outline-none disabled:opacity-50 min-h-[28px] max-h-36 resize-none leading-relaxed chatbot-textarea"
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 144) + 'px';
            }}
          />
          <div className="flex items-center justify-between border-t border-slate-100 pt-1.5 px-0.5 mt-1">
            {/* Left Actions: Gallery + Attachment */}
            <div className="flex items-center gap-1.5 text-slate-400">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-1.5 rounded-lg hover:bg-slate-100 hover:text-slate-600 transition-colors shrink-0"
                title="Add image"
              >
                <Image className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-1.5 rounded-lg hover:bg-slate-100 hover:text-slate-600 transition-colors shrink-0"
                title="Attach file"
              >
                <Paperclip className="w-4 h-4" />
              </button>
            </div>

            {/* Right Actions: Mic + Send Button */}
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => showToast('Voice typing is coming soon!', 'success')}
                className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                title="Use voice"
              >
                <Mic className="w-4 h-4" />
              </button>
              <button
                type="submit"
                disabled={!inputText.trim() || sending}
                className="w-7 h-7 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all shadow-sm shrink-0"
                title="Send message"
              >
                {sending ? (
                  <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <ArrowUp className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
          />
        </div>
      </form>
    );
  };

  /* ─── RENDER HELPER: EMPTY STATE ─── */
  const renderEmptyState = () => {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center px-4 py-16 page-fade max-w-3xl mx-auto w-full">
        <h3 className="text-4xl font-bold text-slate-800 tracking-tight mb-2">Meet AI Mode</h3>
        <p className="text-base text-slate-500 mb-4">
          Ask detailed questions for better responses
        </p>
        
        {/* Render input area inside empty state */}
        {renderInputForm(true)}

        {/* Suggestions list underneath */}
        <div className="flex flex-col items-start gap-3 mt-6 w-full max-w-lg px-6 text-left">
          {currentSuggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => { setInputText(s); setTimeout(() => inputRef.current?.focus(), 50); }}
              className="flex items-center gap-3 text-sm text-slate-500 hover:text-blue-600 transition-colors group text-left"
            >
              <div className="w-5 h-5 rounded-full bg-slate-100 group-hover:bg-blue-50 flex items-center justify-center transition-colors shrink-0">
                <Compass className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 transition-colors" />
              </div>
              <span className="font-light">{s}</span>
            </button>
          ))}
        </div>
      </div>
    );
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  /* ── INIT ── */
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const modelsRes = await fetch('/api/models', { headers: { Authorization: `Bearer ${token}` } });
        if (modelsRes.ok) {
          const fetchedData = await modelsRes.json();
          setModelsData(fetchedData);
        }
        const settingsRes = await fetch('/api/settings', { headers: { Authorization: `Bearer ${token}` } });
        if (settingsRes.ok) {
          const s = await settingsRes.json();
          if (s.default_provider) setProvider(s.default_provider);
          if (s.default_model)    setModel(s.default_model);
        }
        const sessRes = await fetch('/api/chat/sessions', { headers: { Authorization: `Bearer ${token}` } });
        if (sessRes.ok) {
          const data = await sessRes.json();
          setSessions(data);
          if (data.length > 0) {
            setActiveSessionId(data[0].id);
          } else {
            const created = await createSession();
            if (created) { setSessions([created]); setActiveSessionId(created.id); }
          }
        }
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    init();
  }, [token]);

  /* ── FETCH MESSAGES ── */
  useEffect(() => {
    if (!activeSessionId) { setMessages([]); return; }
    const fetchMsgs = async () => {
      setError('');
      try {
        const res = await fetch(`/api/chat/sessions/${activeSessionId}/messages`, { headers: { Authorization: `Bearer ${token}` } });
        if (res.ok) {
          const data = await res.json();
          setMessages(data);
          if (data.length > 0) setLastMessages(prev => ({ ...prev, [activeSessionId]: data[data.length - 1].content }));
        } else setError('Failed to load chat history.');
      } catch { setError('Connection error.'); }
    };
    fetchMsgs();
  }, [activeSessionId, token]);

  /* ── SESSION HELPERS ── */
  const createSession = async () => {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New Chat' }),
    });
    return res.ok ? await res.json() : null;
  };

  const handleNewChat = async () => {
    try {
      const ns = await createSession();
      if (ns) { setSessions(prev => [ns, ...prev]); setActiveSessionId(ns.id); setMessages([]); setSidebarOpen(false); showToast('New chat started', 'success'); }
    } catch { showToast('Failed to create session', 'error'); }
  };

  const handleDeleteSession = async (e, id) => {
    e.stopPropagation();
    try {
      const res = await fetch(`/api/chat/sessions/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const remaining = sessions.filter(s => s.id !== id);
        setSessions(remaining);
        if (activeSessionId === id) {
          if (remaining.length > 0) setActiveSessionId(remaining[0].id);
          else { const ns = await createSession(); if (ns) { setSessions([ns]); setActiveSessionId(ns.id); } }
        }
        showToast('Chat deleted', 'success');
      }
    } catch { showToast('Failed to delete', 'error'); }
  };

  /* ── SEND ── */
  const handleSend = async (e) => {
    e?.preventDefault();
    const text = inputText.trim();
    if (!text || !activeSessionId || sending) return;
    setInputText(''); setSending(true); setError('');

    // Reset textarea height
    if (textareaRef.current) { textareaRef.current.style.height = 'auto'; }

    if (isImageMode) {
      // Image Generation Mode
      const tempMsg = { 
        id: Date.now(), 
        session_id: activeSessionId, 
        role: 'user', 
        content: `Generate image: ${text}`, 
        provider, 
        model, 
        created_at: new Date().toISOString() 
      };
      setMessages(prev => [...prev, tempMsg]);

      try {
        // 1. Save user prompt message to database
        const userMsgRes = await fetch(`/api/chat/sessions/${activeSessionId}/messages`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: 'user', content: `Generate image: ${text}`, provider, model }),
        });
        const savedUserMsg = userMsgRes.ok ? await userMsgRes.json() : tempMsg;

        // 2. Call backend image generation API
        const genRes = await fetch('/api/image/generate', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: text, provider, model }),
        });
        const genData = await genRes.json();
        if (!genRes.ok) throw new Error(genData.detail || 'Failed to generate image.');

        // 3. Construct assistant markdown message containing the image URL
        const imgMarkdown = `Here is the generated image for **"${text}"**:\n\n![Generated Image](${genData.image_url_or_path})`;

        // 4. Save assistant image message to database
        const aiMsgRes = await fetch(`/api/chat/sessions/${activeSessionId}/messages`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: 'assistant', content: imgMarkdown, provider, model }),
        });
        
        let savedAiMsg;
        if (aiMsgRes.ok) {
          savedAiMsg = await aiMsgRes.json();
        } else {
          savedAiMsg = {
            id: Date.now() + 1,
            session_id: activeSessionId,
            role: 'assistant',
            content: imgMarkdown,
            provider,
            model,
            created_at: new Date().toISOString()
          };
        }

        // 5. Update local message history and sidebar title
        setMessages(prev => [...prev.filter(m => m.id !== tempMsg.id), savedUserMsg, savedAiMsg]);
        setLastMessages(prev => ({ ...prev, [activeSessionId]: `[Image] ${text}` }));

        setSessions(prev => prev.map(s => {
          if (s.id === activeSessionId && (s.title === 'New Chat' || s.title === 'Sandbox Session')) {
            return { ...s, title: `Image: ${text.split(/\s+/).slice(0, 4).join(' ')}`, updated_at: new Date().toISOString() };
          }
          return s;
        }));
      } catch (err) {
        setError(err.message);
        showToast(err.message || 'Error generating image', 'error');
        setMessages(prev => prev.filter(m => m.id !== tempMsg.id));
      } finally {
        setSending(false);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
    } else {
      // Text Chat Mode
      const tempMsg = { id: Date.now(), session_id: activeSessionId, role: 'user', content: text, provider, model, created_at: new Date().toISOString() };
      setMessages(prev => [...prev, tempMsg]);

      try {
        const res  = await fetch('/api/chat/message', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: activeSessionId, content: text, provider, model }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to get response.');

        const aiMsg = { id: data.chat_message_id, session_id: activeSessionId, role: 'assistant', content: data.answer, provider: data.provider_used, model: data.model_used, created_at: new Date().toISOString() };
        setMessages(prev => [...prev.filter(m => m.id !== tempMsg.id), tempMsg, aiMsg]);
        setLastMessages(prev => ({ ...prev, [activeSessionId]: data.answer }));

        setSessions(prev => prev.map(s => {
          if (s.id === activeSessionId && (s.title === 'New Chat' || s.title === 'Sandbox Session')) {
            const words = text.split(/\s+/);
            return { ...s, title: words.slice(0, 6).join(' ') + (words.length > 6 ? '…' : ''), updated_at: new Date().toISOString() };
          }
          return s;
        }));
      } catch (err) {
        setError(err.message);
        showToast(err.message || 'Error fetching response', 'error');
        setMessages(prev => prev.filter(m => m.id !== tempMsg.id));
      } finally {
        setSending(false);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
    }
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    showToast('Copied to clipboard', 'success');
    setTimeout(() => setCopiedId(null), 2000);
  };


  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  /* ── LOADING ── */
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-page-bg">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-white border border-border-light flex items-center justify-center shadow-saas-md animate-pulse">
            <img src="/logo.png" className="w-8 h-8 rounded-lg object-cover" alt="Loading" />
          </div>
          <p className="text-sm text-text-muted font-medium">Loading your chats...</p>
        </div>
      </div>
    );
  }

  const activeSession = sessions.find(s => s.id === activeSessionId);

  return (
    <div className="flex-1 flex h-full overflow-hidden" style={{ background: '#F8FAFC' }}>

      {/* ═══════ SIDEBAR ═══════ */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/20 z-20 sm:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`
        absolute sm:relative z-30 sm:z-auto w-60 h-full flex flex-col
        transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full sm:translate-x-0'}
        sm:shrink-0
      `}
        style={{ background: 'linear-gradient(180deg, #1e3a5f 0%, #1e3050 100%)' }}
      >
        {/* Sidebar header */}
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <img src="/logo.png" className="w-8 h-8 rounded-lg object-cover bg-white" alt="Logo" />
            <span className="font-bold text-sm text-white">Indya AI</span>
          </div>
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-3 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-lg transition-colors btn-hover-scale shadow-saas-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            New Chat
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-2">
          {sessions.length === 0 ? (
            <p className="text-xs text-white/40 text-center py-8">No chats yet</p>
          ) : (
            sessions.map(s => {
              const isActive = s.id === activeSessionId;
              return (
                <div
                  key={s.id}
                  onClick={() => { setActiveSessionId(s.id); setSidebarOpen(false); }}
                  className={`group flex items-center gap-2.5 px-3 py-2.5 mx-2 mb-0.5 rounded-lg cursor-pointer transition-all text-sm
                    ${isActive
                      ? 'bg-white/15 text-white'
                      : 'text-white/60 hover:bg-white/10 hover:text-white/90'}
                  `}
                >
                  <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
                  <span className="flex-1 truncate text-xs">{s.title}</span>
                  <button
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-red-400 transition-all shrink-0"
                    title="Delete"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* User info + logout */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center text-white text-xs font-bold shadow-saas-sm">
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.name || 'User'}</p>
              <p className="text-[10px] text-white/50 truncate">{user?.email || ''}</p>
            </div>
          </div>
          <button
            onClick={() => { localStorage.removeItem('token'); window.location.href = '/'; }}
            className="w-full flex items-center gap-2 px-3 py-2 text-xs text-white/60 hover:text-red-400 hover:bg-white/10 rounded-lg transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
        </div>
      </aside>

      {/* ═══════ MAIN CHAT ═══════ */}
      <div className="flex-1 flex flex-col h-full min-w-0">

        {/* ─── Header ─── */}
        <header className="bg-white border-b border-border-light px-4 py-3 flex items-center justify-between shrink-0 shadow-saas-sm">
          <div className="flex items-center gap-3">
            {/* Hamburger */}
            <button
              onClick={() => setSidebarOpen(v => !v)}
              className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-page-bg transition-colors sm:hidden"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16"/>
              </svg>
            </button>
            <div className="hidden sm:flex items-center gap-2">
              <img src="/logo.png" className="w-7 h-7 rounded-lg object-cover bg-white shadow-sm" alt="Logo" />
              <span className="font-semibold text-sm text-text-primary">Indya AI</span>
            </div>
            <span className="text-text-muted text-sm hidden sm:block">/</span>
            <h1 className="text-sm font-semibold text-text-primary truncate max-w-[80px] sm:max-w-[150px] lg:max-w-xs">
              {activeSession?.title || 'New Chat'}
            </h1>
          </div>

          {/* Model and Mode Selectors on the right side of Top Bar */}
          <div className="flex items-center gap-2">
            {/* Mode Toggle Button */}
            <button
              type="button"
              onClick={() => {
                setIsImageMode(!isImageMode);
              }}
              className={`flex items-center gap-1.5 px-2.5 py-1 border rounded-full text-[10px] font-semibold transition-all shrink-0 cursor-pointer
                ${isImageMode 
                  ? 'bg-purple-50 text-purple-600 border-purple-200 hover:bg-purple-100 shadow-sm' 
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                }`}
            >
              {isImageMode ? (
                <>
                  <Sparkles className="w-3 h-3 text-purple-500 animate-pulse" />
                  <span>Image Gen</span>
                </>
              ) : (
                <>
                  <MessageSquare className="w-3 h-3 text-slate-500" />
                  <span>Text Chat</span>
                </>
              )}
            </button>

            <div className="h-4 w-[1px] bg-slate-200 mx-0.5 shrink-0" />

            <PillSelect
              value={provider}
              options={availableProviders.map(p => p.name)}
              onChange={(p) => {
                setProvider(p);
                const pObj = availableProviders.find(x => x.name === p);
                const models = pObj ? pObj.models.filter(m => m.active && (isImageMode ? m.supports_image : m.supports_chat)) : [];
                if (models.length > 0) {
                  setModel(models[0].id);
                }
              }}
              optionLabel={(o) => providerLabels[o] || o}
            />
            <PillSelect
              value={model}
              options={availableModels.map(m => m.id)}
              onChange={setModel}
              optionLabel={(o) => o.split('/').pop()}
            />
          </div>
        </header>

        {/* ─── Messages ─── */}
        <div className="flex-1 overflow-y-auto bg-[#F8FAFC]">
          <div className="max-w-chat mx-auto w-full h-full flex flex-col px-4 sm:px-6">

            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600 mt-4 animate-fade-in">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {messages.length === 0 && !sending ? (
              renderEmptyState()
            ) : (
              <div className="flex-1 py-6 space-y-5">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} msg={msg} user={user} onCopy={handleCopy} copiedId={copiedId} />
                ))}
                {sending && <TypingIndicator isImage={isImageMode} />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* ─── Input (Only show when active) ─── */}
        {(messages.length > 0 || sending) && (
          <div className="bg-white border-t border-border-light px-4 py-4 shrink-0">
            {renderInputForm(false)}
          </div>
        )}
      </div>
    </div>
  );
}
