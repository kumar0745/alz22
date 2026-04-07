import { motion } from "framer-motion";

/**
 * Stylized “3D” brain — pure SVG with cyan/purple/blue depth gradients (no external image asset).
 */
const BrainHero3D = ({ className = "" }: { className?: string }) => (
  <motion.svg
    viewBox="0 0 400 420"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    initial={{ opacity: 0, scale: 0.96 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 1.2, ease: "easeOut" }}
  >
    <defs>
      <linearGradient id="brainShell" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="hsl(217 91% 58%)" stopOpacity="0.95" />
        <stop offset="45%" stopColor="hsl(270 60% 52%)" stopOpacity="0.85" />
        <stop offset="100%" stopColor="hsl(185 80% 48%)" stopOpacity="0.75" />
      </linearGradient>
      <linearGradient id="brainCore" x1="20%" y1="0%" x2="80%" y2="100%">
        <stop offset="0%" stopColor="hsl(222 47% 18%)" />
        <stop offset="100%" stopColor="hsl(270 40% 22%)" />
      </linearGradient>
      <radialGradient id="glowLobe" cx="50%" cy="40%" r="60%">
        <stop offset="0%" stopColor="hsl(185 90% 60%)" stopOpacity="0.55" />
        <stop offset="100%" stopColor="hsl(217 91% 50%)" stopOpacity="0" />
      </radialGradient>
      <filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
        <feGaussianBlur stdDeviation="8" result="b" />
        <feMerge>
          <feMergeNode in="b" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
      <filter id="innerShadow">
        <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="hsl(222 47% 6%)" floodOpacity="0.45" />
      </filter>
    </defs>

    {/* Ambient glow behind */}
    <ellipse cx="200" cy="210" rx="160" ry="175" fill="url(#glowLobe)" opacity="0.9" />

    {/* Main mass — two hemispheres suggestion */}
    <path
      filter="url(#softGlow)"
      d="M200 48c-62 0-112 48-118 110-4 38 8 76 32 104 26 32 62 52 102 56 18 2 36 1 52-4 46-14 82-52 94-98 14-58-10-118-56-152-28-22-62-34-98-36-2 0-4 0-6 0z"
      fill="url(#brainShell)"
      stroke="hsla(210,40%,96%,0.12)"
      strokeWidth="1.5"
    />
    <path
      d="M198 72c-48 6-88 44-96 96-6 36 6 72 30 98 22 24 54 40 88 44 12 1 24 0 36-3 40-10 70-44 80-84 12-52-8-108-52-138-24-18-52-28-82-30l-4-3z"
      fill="url(#brainCore)"
      opacity="0.55"
    />

    {/* Sulci / gyri hints */}
    <path
      d="M128 160c24-18 52-28 82-30M152 200c28-10 58-12 88-6M160 248c32 8 64 6 96-8M175 290c26 14 54 20 84 16"
      stroke="hsla(210,40%,96%,0.14)"
      strokeWidth="2"
      strokeLinecap="round"
    />

    {/* Synaptic nodes */}
    {[
      [120, 140],
      [250, 120],
      [290, 200],
      [100, 230],
      [220, 260],
      [170, 310],
      [260, 300],
    ].map(([x, y], i) => (
      <circle key={i} cx={x} cy={y} r="4" fill="hsl(185 90% 65%)" opacity="0.85" filter="url(#innerShadow)">
        <animate attributeName="opacity" values="0.5;1;0.5" dur={`${2.4 + i * 0.2}s`} repeatCount="indefinite" />
      </circle>
    ))}

    {/* Connection arcs */}
    <path
      d="M120 140 Q200 100 290 200 M100 230 Q200 180 260 300"
      stroke="url(#brainShell)"
      strokeOpacity="0.35"
      strokeWidth="1.2"
      fill="none"
    />
  </motion.svg>
);

export default BrainHero3D;
