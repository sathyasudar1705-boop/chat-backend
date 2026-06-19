import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

export default function LandingPage() {
  const token = localStorage.getItem('token');
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 md:p-8 font-sans page-fade relative overflow-hidden select-none bg-[#EBF0FF]">
      
      {/* Decorative organic backgrounds, mimicking the inspiration image */}
      <div className="absolute top-[-10%] right-[-10%] w-[40vw] h-[40vw] bg-[#6885FF] rounded-full opacity-80 -z-10 blur-[10px]" />
      <div className="absolute bottom-[-15%] left-[-15%] w-[45vw] h-[45vw] bg-[#0047FF] rounded-full opacity-90 -z-10 blur-[20px]" />
      <div className="absolute bottom-[-10%] right-[30%] w-[35vw] h-[35vw] bg-[#FF4B72] rounded-full opacity-60 -z-10 blur-[30px]" />
      <div className="absolute top-[30%] left-[-10%] w-[25vw] h-[25vw] bg-[#FF4B72] rounded-full opacity-70 -z-10 blur-[15px]" />

      {/* Main card panel container */}
      <div className="w-full max-w-6xl bg-white rounded-[32px] shadow-2xl border border-slate-100 overflow-hidden flex flex-col min-h-[620px] relative z-10">
        
        {/* Navbar */}
        <header className="px-8 py-6 flex items-center justify-between border-b border-slate-50">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <img src="/logo.png" className="w-9 h-9 rounded-xl object-cover" alt="Indya AI Logo" />
            <span className="font-extrabold text-lg text-[#0F34C2] tracking-tight">Indya AI</span>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/login" className="px-5 py-2 border border-slate-200 text-slate-700 hover:bg-slate-50 text-sm font-semibold rounded-full transition-all btn-hover-scale shadow-sm bg-white">
              Login
            </Link>
          </div>
        </header>

        {/* Hero Section */}
        <main className="flex-1 flex flex-col lg:flex-row items-center px-8 sm:px-12 py-10 lg:py-16 gap-10 lg:gap-16">
          
          {/* Left Column (Content) */}
          <div className="flex-1 text-left flex flex-col justify-center max-w-xl lg:max-w-none">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-[#0F34C2] leading-[1.15] tracking-tight mb-6">
              Chat Bot
              <br />
              <span className="text-[#FF4B72]">Messenger</span>
            </h1>
            
            <p className="text-slate-500 text-sm sm:text-base leading-relaxed font-light">
              Connect with multiple AI providers inside a single clean interface.
              Access Gemini, Groq, Mistral, and more securely. Fast responses, smart fallbacks, and zero clutter — experience the next generation of conversational AI.
            </p>
          </div>

          {/* Right Column (Illustration Image) */}
          <div className="flex-1 w-full max-w-lg lg:max-w-none flex items-center justify-center relative">
            <div className="w-full relative group">
              {/* Soft colorful backplate glow */}
              <div className="absolute inset-0 bg-gradient-to-tr from-[#6885FF]/10 to-[#FF4B72]/10 rounded-[32px] blur-xl" />
              <img 
                src="/landing_hero.png" 
                className="w-full h-auto object-contain relative z-10 hover:scale-[1.02] transition-transform duration-300" 
                alt="Chat Bot Illustration" 
              />
            </div>
          </div>
          
        </main>
      </div>
    </div>
  );
}
