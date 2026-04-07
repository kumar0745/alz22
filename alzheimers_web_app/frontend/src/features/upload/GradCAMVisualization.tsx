import { useState } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, Layers } from "lucide-react";

type Props = {
  preview: string;
  /** Base64 PNG from backend Grad-CAM overlay (optional). */
  gradcamBase64?: string | null;
};

/**
 * Grad-CAM: uses server-generated overlay when available; otherwise a subtle demo overlay.
 */
const GradCAMVisualization = ({ preview, gradcamBase64 }: Props) => {
  const [opacity, setOpacity] = useState(0.55);
  const [showOverlay, setShowOverlay] = useState(true);
  const heatmapSrc = gradcamBase64 ? `data:image/png;base64,${gradcamBase64}` : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="glass-card rounded-2xl p-6 space-y-4 border border-cyan-500/10 shadow-[0_0_40px_hsla(185,80%,50%,0.08)]"
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-accent" />
          <p className="text-sm font-medium text-foreground">Grad-CAM saliency</p>
          {heatmapSrc && (
            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-primary/15 text-primary border border-primary/20">
              Model
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setShowOverlay((v) => !v)}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {showOverlay ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          {showOverlay ? "Hide" : "Show"}
        </button>
      </div>

      <div className="relative rounded-xl overflow-hidden aspect-square max-h-64 mx-auto ring-1 ring-cyan-400/20 mri-preview-glow">
        <img src={preview} alt="MRI scan" className="w-full h-full object-contain bg-black/50" />
        {showOverlay && heatmapSrc && (
          <img
            src={heatmapSrc}
            alt="Grad-CAM overlay"
            className="absolute inset-0 w-full h-full object-contain pointer-events-none mix-blend-screen"
            style={{ opacity }}
          />
        )}
        {showOverlay && !heatmapSrc && (
          <div className="absolute inset-0 mix-blend-screen pointer-events-none" style={{ opacity }}>
            <div
              className="w-full h-full"
              style={{
                background: `
                  radial-gradient(ellipse 35% 40% at 55% 45%, hsla(0,90%,50%,0.85) 0%, hsla(30,95%,50%,0.5) 30%, hsla(60,90%,50%,0.28) 55%, transparent 75%),
                  radial-gradient(ellipse 20% 25% at 40% 38%, hsla(0,85%,55%,0.65) 0%, hsla(45,90%,50%,0.25) 50%, transparent 70%),
                  radial-gradient(ellipse 15% 18% at 62% 55%, hsla(15,90%,50%,0.45) 0%, hsla(50,80%,50%,0.18) 50%, transparent 70%)
                `,
              }}
            />
          </div>
        )}
      </div>

      {showOverlay && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Overlay intensity</span>
            <span>{Math.round(opacity * 100)}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-primary bg-muted"
          />
        </div>
      )}

      <div className="flex items-center gap-2 pt-1">
        <div
          className="h-2.5 flex-1 rounded-full"
          style={{
            background:
              "linear-gradient(90deg, hsl(240,60%,50%), hsl(185,80%,50%), hsl(120,70%,50%), hsl(60,90%,55%), hsl(30,95%,50%), hsl(0,90%,50%))",
          }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground -mt-2">
        <span>Low relevance</span>
        <span>High relevance</span>
      </div>

      <p className="text-xs text-muted-foreground leading-relaxed">
        {heatmapSrc
          ? "Regions emphasized in warm colors are most influential for the model’s decision (Grad-CAM on the last convolutional block)."
          : "Demo overlay shown — start the API with a trained ResNet50 model and request explain=true to load real saliency maps."}
      </p>
    </motion.div>
  );
};

export default GradCAMVisualization;
