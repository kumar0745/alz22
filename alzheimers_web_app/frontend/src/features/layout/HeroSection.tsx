import { motion } from "framer-motion";
import { ArrowDown, Shield, Zap, Activity, Sparkles } from "lucide-react";
import heroBrain from "@/assets/hero-brain.png";

const stats = [
  { icon: Shield, label: "Validated", value: "ResNet50" },
  { icon: Zap, label: "Inference", value: "< 2s" },
  { icon: Activity, label: "Classes", value: "CN → AD" },
];

const HeroSection = () => (
  <section
    id="hero"
    className="relative min-h-screen flex items-center overflow-hidden pt-20 neural-bg neural-mesh-bg mri-hero-vignette"
  >
    <div className="absolute inset-0 pointer-events-none opacity-40 scanlines" aria-hidden />

    {/* Ambient glow orbs */}
    <div className="absolute top-1/4 left-1/4 w-[28rem] h-[28rem] rounded-full bg-primary/15 blur-[120px] pointer-events-none animate-pulse-slow motion-reduce:animate-none" />
    <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-secondary/15 blur-[100px] pointer-events-none" />
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[36rem] h-[36rem] rounded-full bg-cyan-500/5 blur-[140px] pointer-events-none" />

    <div className="container mx-auto px-6 grid lg:grid-cols-2 gap-12 items-center relative z-10">
      {/* Left */}
      <motion.div initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8 }}>
        <span className="inline-flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-accent mb-4 border border-accent/35 rounded-full px-4 py-1.5 glass-card shadow-[0_0_24px_hsla(185,80%,50%,0.15)]">
          <Sparkles className="w-3.5 h-3.5" />
          Deep Learning · Transfer learning
        </span>
        <h1 className="font-display text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
          <span className="gradient-text">Alzheimer&apos;s</span>{" "}
          <span className="text-foreground drop-shadow-sm">MRI Intelligence</span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-lg mb-8 leading-relaxed">
          Professional-grade glassmorphism UI meets ResNet50 classification: upload a slice, read confidence scores, and
          inspect Grad-CAM saliency — built for distinction-level demos.
        </p>

        <div className="flex flex-wrap gap-4 mb-12">
          <a
            href="#upload"
            className="btn-primary-glow px-8 py-3.5 rounded-xl font-semibold text-primary-foreground text-base transition-transform hover:scale-[1.02] active:scale-[0.98]"
          >
            Upload MRI Scan
          </a>
          <a
            href="#info"
            className="glass-card px-8 py-3.5 rounded-xl font-semibold text-foreground text-base border border-white/10 hover:border-primary/40 hover:shadow-[0_0_32px_hsla(217,91%,60%,0.12)] transition-all"
          >
            Learn more
          </a>
        </div>

        <div className="flex flex-wrap gap-8">
          {stats.map((s) => (
            <div key={s.label} className="flex items-center gap-3 group">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center border border-white/5 shadow-inner transition-transform group-hover:scale-105">
                <s.icon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-display font-bold text-foreground tracking-tight">{s.value}</p>
                <p className="text-xs text-muted-foreground">{s.label}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Right – SVG 3D brain + rings */}
      <motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, delay: 0.2 }}
        className="relative flex justify-center items-center perspective-[1200px]"
      >
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-[min(100%,420px)] aspect-square rounded-full border border-primary/20 animate-orbit" />
          <div className="absolute w-[min(90%,380px)] aspect-square rounded-full border border-cyan-400/15 animate-orbit-rev" />
        </div>
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-primary/20 via-transparent to-secondary/10 blur-[80px] scale-110" />
        <img
          src={heroBrain}
          alt="Stylized brain visualization"
          className="relative w-full max-w-md md:max-w-lg rounded-[2rem] border border-white/10 shadow-[0_0_80px_hsla(217,91%,60%,0.25)] object-contain float-animation"
          loading="eager"
        />

        <motion.div
          animate={{ y: [0, -10, 0] }}
          transition={{ repeat: Infinity, duration: 3.2, ease: "easeInOut" }}
          className="absolute top-8 right-2 md:right-8 glass-card px-4 py-2.5 rounded-2xl flex items-center gap-2 border border-cyan-400/20 shadow-lg"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent" />
          </span>
          <span className="text-xs font-semibold text-foreground">Model ready</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="absolute -bottom-4 left-1/2 -translate-x-1/2 glass-card px-5 py-2 rounded-full text-[11px] text-muted-foreground border border-white/10 whitespace-nowrap"
        >
          Grad-CAM explainability · REST API
        </motion.div>
      </motion.div>
    </div>

    <motion.div
      animate={{ y: [0, 10, 0] }}
      transition={{ repeat: Infinity, duration: 2.2 }}
      className="absolute bottom-8 left-1/2 -translate-x-1/2 text-muted-foreground/80"
    >
      <ArrowDown className="w-5 h-5" />
    </motion.div>
  </section>
);

export default HeroSection;
