import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Image as ImageIcon, X, Loader2, Brain, Wifi, WifiOff } from "lucide-react";
import { toast } from "sonner";
import { checkApiHealth, predictMri } from "@/lib/api";
import GradCAMVisualization from "./GradCAMVisualization";

type Prediction = {
  /** Short code from API: CN | VMCI | MCI | AD */
  prediction: string;
  confidence: number;
  details: { stage: string; probability: number }[];
  explanation: string;
  prediction_full?: string;
  gradcam_base64?: string | null;
};

const SHORT_TO_UI: Record<string, string> = {
  CN: "Normal",
  VMCI: "Very Mild Impairment",
  MCI: "Mild Cognitive Impairment",
  AD: "Alzheimer's Disease",
};

function uiLabel(r: Prediction): string {
  return r.prediction_full ?? SHORT_TO_UI[r.prediction] ?? r.prediction;
}

async function fetchPrediction(file: File): Promise<Prediction | null> {
  const res = await predictMri(file, true);
  if (!res.ok) {
    let msg = `API error (${res.status})`;
    try {
      const err = (await res.json()) as { detail?: string | unknown };
      if (err.detail !== undefined) {
        msg = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
      }
    } catch {
      /* ignore */
    }
    toast.error(msg);
    return null;
  }
  const data = (await res.json()) as Prediction & { details?: Prediction["details"] };
  if (data.prediction === undefined || data.confidence === undefined) return null;
  if (!data.details?.length) return null;
  return data as Prediction;
}

const STAGE_TO_SHORT: Record<string, string> = {
  Normal: "CN",
  "Very Mild Impairment": "VMCI",
  "Mild Cognitive Impairment": "MCI",
  "Alzheimer's Disease": "AD",
};

/* Fallback demo when the API is unreachable or no model is trained */
const simulatePrediction = (): Promise<Prediction> =>
  new Promise((resolve) => {
    const stages = [
      { stage: "Normal", probability: 4.2 },
      { stage: "Very Mild Impairment", probability: 12.8 },
      { stage: "Mild Cognitive Impairment", probability: 72.5 },
      { stage: "Alzheimer's Disease", probability: 10.5 },
    ];
    const top = stages.reduce((a, b) => (a.probability > b.probability ? a : b));
    setTimeout(
      () =>
        resolve({
          prediction: STAGE_TO_SHORT[top.stage] ?? "MCI",
          prediction_full: top.stage,
          confidence: top.probability,
          details: stages,
          explanation:
            top.stage === "Normal"
              ? "No significant markers of cognitive decline were detected in this scan."
              : top.stage === "Alzheimer's Disease"
              ? "The scan shows significant hippocampal atrophy and cortical thinning consistent with Alzheimer's Disease."
              : "The scan shows early signs of neurodegeneration. Follow-up clinical evaluation is recommended.",
        }),
      2500
    );
  });

const stageColors: Record<string, string> = {
  Normal: "stage-normal",
  "Very Mild Impairment": "stage-mild",
  "Mild Cognitive Impairment": "stage-mci",
  "Alzheimer's Disease": "stage-alzheimer",
};

const UploadSection = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Prediction | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    checkApiHealth().then((ok) => {
      if (!cancelled) setApiOnline(ok);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const predict = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const fromApi = await fetchPrediction(file);
      setResult(fromApi ?? (await simulatePrediction()));
    } catch {
      toast.error("Network error — showing demo output.");
      setResult(await simulatePrediction());
    }
    setLoading(false);
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  return (
    <section id="upload" className="py-24 neural-bg relative">
      <div className="absolute top-0 right-0 w-72 h-72 rounded-full bg-secondary/5 blur-[100px] pointer-events-none" />
      <div className="container mx-auto px-6 max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-12 space-y-4">
          {apiOnline === false && (
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-200/90 max-w-lg mx-auto">
              <WifiOff className="w-3.5 h-3.5 shrink-0" />
              Backend unreachable — predictions will use local demo mode. Run:{" "}
              <code className="rounded bg-black/30 px-1.5 py-0.5 font-mono text-[10px]">uvicorn main:app --port 8000</code>
            </div>
          )}
          {apiOnline === true && (
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-4 py-1.5 text-xs text-emerald-100/90">
              <Wifi className="w-3.5 h-3.5" /> API connected — live ResNet50 inference
            </div>
          )}
          <h2 className="font-display text-4xl font-bold mb-3 gradient-text">Upload MRI Scan</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Drag & drop a brain MRI slice (JPEG/PNG). The backend returns stage codes (CN, VMCI, MCI, AD) and optional Grad-CAM.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Upload area */}
          <motion.div initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
            {!preview ? (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
                className="glass-card border-dashed border-2 border-primary/30 rounded-2xl h-80 flex flex-col items-center justify-center cursor-pointer hover:border-primary/60 transition-colors group"
              >
                <Upload className="w-12 h-12 text-primary/60 mb-4 group-hover:text-primary transition-colors" />
                <p className="text-foreground font-medium mb-1">Drop MRI image here</p>
                <p className="text-muted-foreground text-sm">or click to browse</p>
                <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
              </div>
            ) : (
              <div className="glass-card rounded-2xl p-4 relative group mri-preview-glow">
                <img src={preview} alt="MRI preview" className="w-full h-72 object-contain rounded-xl ring-1 ring-cyan-400/15" />
                <button onClick={reset} className="absolute top-6 right-6 bg-destructive/80 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <X className="w-4 h-4 text-destructive-foreground" />
                </button>
                <p className="text-xs text-muted-foreground mt-2 truncate">{file?.name}</p>
              </div>
            )}

            {preview && !result && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={predict}
                disabled={loading}
                className="btn-primary-glow w-full mt-4 py-3 rounded-xl font-semibold text-primary-foreground flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" /> Analyzing…
                  </>
                ) : (
                  <>
                    <Brain className="w-5 h-5" /> Predict Disease Stage
                  </>
                )}
              </motion.button>
            )}
          </motion.div>

          {/* Result area */}
          <AnimatePresence mode="wait">
            {loading && (
              <motion.div key="loader" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="glass-card rounded-2xl flex flex-col items-center justify-center h-80">
                <div className="relative w-24 h-24 mb-6">
                  <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
                  <div className="absolute inset-0 rounded-full border-4 border-t-primary animate-spin" />
                  <Brain className="absolute inset-0 m-auto w-10 h-10 text-primary" />
                </div>
                <p className="text-foreground font-semibold">Analyzing MRI Scan…</p>
                <p className="text-muted-foreground text-sm mt-1">Running CNN classification</p>
              </motion.div>
            )}

            {result && !loading && (
              <motion.div key="result" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                {/* Main prediction */}
                <div className={`glass-card rounded-2xl p-6 border ${stageColors[uiLabel(result)] ?? "stage-mci"}`}>
                  <p className="text-sm uppercase tracking-wider mb-1 opacity-80">Predicted stage</p>
                  <h3 className="font-display text-2xl font-bold">{uiLabel(result)}</h3>
                  <p className="text-xs text-muted-foreground mt-2 font-mono tracking-wide">
                    Code: {result.prediction} · {result.confidence.toFixed(1)}% confidence
                  </p>
                </div>

                {/* Confidence bars */}
                <div className="glass-card rounded-2xl p-6 space-y-3">
                  <p className="text-sm text-muted-foreground font-medium mb-2">Confidence Breakdown</p>
                  {result.details.map((d) => (
                    <div key={d.stage}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-foreground">{d.stage}</span>
                        <span className="text-muted-foreground">{d.probability.toFixed(1)}%</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${d.probability}%` }}
                          transition={{ duration: 0.8, delay: 0.2 }}
                          className="h-full rounded-full"
                          style={{ background: "var(--gradient-primary)" }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Explanation */}
                <div className="glass-card rounded-2xl p-6">
                  <p className="text-sm text-muted-foreground font-medium mb-2">Clinical Insight</p>
                  <p className="text-foreground text-sm leading-relaxed">{result.explanation}</p>
                </div>

                {/* Grad-CAM Heatmap */}
                {preview && <GradCAMVisualization preview={preview} gradcamBase64={result.gradcam_base64} />}

                <button onClick={reset} className="w-full py-2 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-primary/40 transition-colors text-sm">
                  Analyze Another Scan
                </button>
              </motion.div>
            )}

            {!loading && !result && (
              <motion.div key="placeholder" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card rounded-2xl flex flex-col items-center justify-center h-80 text-center px-6">
                <ImageIcon className="w-12 h-12 text-muted-foreground/40 mb-4" />
                <p className="text-muted-foreground">Upload an MRI scan to see AI-powered predictions with confidence scores and clinical insights.</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
};

export default UploadSection;
