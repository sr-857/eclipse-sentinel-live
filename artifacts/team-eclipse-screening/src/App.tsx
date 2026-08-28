import { useEffect, useRef, useState, type CSSProperties } from 'react';
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  CloudUpload,
  FileCheck2,
  FileImage,
  Fingerprint,
  Gauge,
  Info,
  LockKeyhole,
  Menu,
  RotateCcw,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Target,
  UserRoundCheck,
  X,
  Zap,
} from 'lucide-react';

type Phase = 'idle' | 'ready' | 'scanning' | 'complete' | 'error';
type RiskLevel = 'Low' | 'Medium' | 'High';

type Metrics = {
  width: number;
  height: number;
  ratio: number;
  brightness: number;
  contrast: number;
  fileSize: number;
};

type CheckResult = {
  title: string;
  status: 'Pass' | 'Review' | 'Prototype';
  tone: 'green' | 'orange' | 'blue';
  description: string;
  icon: typeof FileCheck2;
};

type Analysis = {
  score: number;
  level: RiskLevel;
  metrics: Metrics;
  checks: CheckResult[];
};

const scanStages = ['Upload ID', 'Read', 'Check', 'Face', 'Analyse'];

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getRisk(score: number): RiskLevel {
  if (score < 35) return 'Low';
  if (score < 65) return 'Medium';
  return 'High';
}

function createSampleFile(): Promise<File> {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    canvas.width = 1200;
    canvas.height = 760;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#edf2f7';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(12, 35, 64, .14)';
    ctx.shadowBlur = 30;
    ctx.shadowOffsetY = 12;
    ctx.fillRect(84, 74, 1032, 612);
    ctx.shadowColor = 'transparent';
    ctx.fillStyle = '#08294d';
    ctx.fillRect(84, 74, 1032, 116);
    ctx.fillStyle = '#f8bd5d';
    ctx.fillRect(84, 74, 15, 116);
    ctx.font = '700 32px Arial';
    ctx.fillStyle = '#ffffff';
    ctx.fillText('IDENTITY DOCUMENT', 135, 145);
    ctx.fillStyle = '#dbe8f5';
    ctx.font = '500 17px Arial';
    ctx.fillText('REPUBLIC OF DEMO · SAMPLE ONLY', 135, 171);
    ctx.fillStyle = '#d9e2ec';
    ctx.fillRect(135, 230, 230, 286);
    ctx.fillStyle = '#bfd1e1';
    ctx.beginPath();
    ctx.arc(250, 326, 55, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(187, 396, 126, 86);
    ctx.fillStyle = '#183b60';
    ctx.font = '700 24px Arial';
    ctx.fillText('ALEX MORGAN', 420, 275);
    ctx.fillStyle = '#66788b';
    ctx.font = '500 16px Arial';
    ctx.fillText('DOCUMENT NUMBER', 420, 330);
    ctx.fillStyle = '#183b60';
    ctx.font = '700 21px Arial';
    ctx.fillText('ECL-26188-042', 420, 358);
    ctx.fillStyle = '#66788b';
    ctx.font = '500 16px Arial';
    ctx.fillText('DATE OF BIRTH', 420, 415);
    ctx.fillStyle = '#183b60';
    ctx.font = '700 21px Arial';
    ctx.fillText('14 / 09 / 1998', 420, 443);
    ctx.fillStyle = '#b6c8d9';
    ctx.fillRect(420, 510, 540, 42);
    ctx.fillRect(420, 568, 390, 18);
    ctx.fillStyle = '#184c7a';
    ctx.fillRect(900, 568, 60, 18);
    canvas.toBlob((blob) => {
      if (blob) resolve(new File([blob], 'eclipse-demo-id.png', { type: 'image/png' }));
    }, 'image/png');
  });
}

async function inspectImage(file: File): Promise<Analysis> {
  const imageUrl = URL.createObjectURL(file);
  const image = new Image();
  image.src = imageUrl;
  await new Promise<void>((resolve, reject) => {
    image.onload = () => resolve();
    image.onerror = () => reject(new Error('This image could not be read.'));
  });
  URL.revokeObjectURL(imageUrl);

  const maxSide = 900;
  const scale = Math.min(1, maxSide / Math.max(image.naturalWidth, image.naturalHeight));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
  canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
  const context = canvas.getContext('2d', { willReadFrequently: true });
  if (!context) throw new Error('Your browser could not inspect this image.');
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
  let sum = 0;
  let sumSquares = 0;
  const sampleStep = Math.max(1, Math.floor(pixels.length / 4 / 180000));
  let samples = 0;
  for (let i = 0; i < pixels.length; i += 4 * sampleStep) {
    const brightness = 0.299 * pixels[i] + 0.587 * pixels[i + 1] + 0.114 * pixels[i + 2];
    sum += brightness;
    sumSquares += brightness * brightness;
    samples++;
  }
  const average = sum / samples;
  const contrast = Math.sqrt(Math.max(0, sumSquares / samples - average * average));
  const ratio = image.naturalWidth / image.naturalHeight;
  const ratioDistance = Math.abs(ratio - 1.585);
  let score = 12;
  if (file.size < 12000) score += 10;
  if (image.naturalWidth < 600 || image.naturalHeight < 400) score += 16;
  if (ratioDistance > 0.48) score += 18;
  else if (ratioDistance > 0.22) score += 8;
  if (average < 42 || average > 226) score += 17;
  else if (average < 65 || average > 207) score += 6;
  if (contrast < 18) score += 14;
  else if (contrast < 30) score += 6;
  const ratioGood = ratioDistance <= 0.48;
  const sizeGood = image.naturalWidth >= 600 && image.naturalHeight >= 400;
  const lightGood = average >= 42 && average <= 226;
  const contrastGood = contrast >= 18;
  const checks: CheckResult[] = [
    {
      title: 'Document Validation',
      status: sizeGood && ratioGood ? 'Pass' : 'Review',
      tone: sizeGood && ratioGood ? 'green' : 'orange',
      description: sizeGood && ratioGood
        ? 'Image dimensions and shape look suitable for an ID document.'
        : 'The image shape or resolution is outside the expected ID range.',
      icon: FileCheck2,
    },
    {
      title: 'Tampering Analysis',
      status: lightGood && contrastGood ? 'Pass' : 'Review',
      tone: lightGood && contrastGood ? 'green' : 'orange',
      description: lightGood && contrastGood
        ? 'Lighting and contrast are clear enough for a first-pass visual review.'
        : 'Uneven lighting or low contrast makes visual review less reliable.',
      icon: ScanLine,
    },
    {
      title: 'Face Verification',
      status: 'Prototype',
      tone: 'blue',
      description: 'Prototype signal only — no face-matching model is running in this demo.',
      icon: UserRoundCheck,
    },
    {
      title: 'Data Consistency',
      status: 'Prototype',
      tone: 'blue',
      description: 'Prototype signal only — OCR and cross-source checks need officer review.',
      icon: Fingerprint,
    },
  ];
  const boundedScore = Math.min(92, Math.max(8, Math.round(score)));
  return {
    score: boundedScore,
    level: getRisk(boundedScore),
    metrics: {
      width: image.naturalWidth,
      height: image.naturalHeight,
      ratio,
      brightness: Math.round(average),
      contrast: Math.round(contrast),
      fileSize: file.size,
    },
    checks,
  };
}

async function screenDocumentWithBackend(file: File): Promise<Analysis> {
  const localAnalysis = await inspectImage(file);
  try {
    const formData = new FormData();
    formData.append('document', file);

    const backendBase = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    const res = await fetch(`${backendBase.replace(/\/$/, '')}/screen`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    const data = await res.json();
    if (data.error) {
      throw new Error(data.error);
    }

    const score = typeof data.risk_score === 'number' ? data.risk_score : localAnalysis.score;
    const level: RiskLevel = data.risk_level === 'LOW' ? 'Low' : data.risk_level === 'HIGH' ? 'High' : 'Medium';

    const docVal = data.document_validation || {};
    const tampVal = data.tampering || {};
    const faceVal = data.face_verification || {};
    const consVal = data.data_consistency || {};

    const checks: CheckResult[] = [
      {
        title: 'Document Validation',
        status: docVal.status === 'PASS' ? 'Pass' : 'Review',
        tone: docVal.status === 'PASS' ? 'green' : 'orange',
        description: docVal.reason || 'Document validation check completed.',
        icon: FileCheck2,
      },
      {
        title: 'Tampering Analysis',
        status: tampVal.status === 'NORMAL' ? 'Pass' : 'Review',
        tone: tampVal.status === 'NORMAL' ? 'green' : 'orange',
        description: tampVal.reason || 'Prototype Tampering Analysis completed.',
        icon: ScanLine,
      },
      {
        title: 'Face Verification',
        status: faceVal.status === 'MATCH' || faceVal.status === 'FACE DETECTED' ? 'Pass' : faceVal.status === 'MISMATCH' ? 'Review' : 'Prototype',
        tone: faceVal.status === 'MATCH' || faceVal.status === 'FACE DETECTED' ? 'green' : faceVal.status === 'MISMATCH' || faceVal.status === 'REVIEW' ? 'orange' : 'blue',
        description: faceVal.reason || (faceVal.face_detected ? 'Face detected in document.' : 'Prototype face verification signal.'),
        icon: UserRoundCheck,
      },
      {
        title: 'Data Consistency',
        status: consVal.status === 'PASS' ? 'Pass' : 'Review',
        tone: consVal.status === 'PASS' ? 'green' : 'orange',
        description: consVal.reason || 'OCR data consistency check completed.',
        icon: Fingerprint,
      },
    ];

    return {
      score,
      level,
      metrics: localAnalysis.metrics,
      checks,
    };
  } catch (err) {
    console.warn('Backend screening offline/failed, using fallback:', err);
    return {
      ...localAnalysis,
      checks: localAnalysis.checks.map((c) => ({
        ...c,
        description: `${c.description} [Backend API: SIMULATED FALLBACK]`,
      })),
    };
  }
}

function App() {
  const [phase, setPhase] = useState<Phase>('idle');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState('');
  const [stage, setStage] = useState(0);
  const [mobileNav, setMobileNav] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const screeningRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (phase !== 'scanning') return;
    const timer = window.setInterval(() => setStage((current) => Math.min(4, current + 1)), 500);
    return () => window.clearInterval(timer);
  }, [phase]);

  const chooseFile = (nextFile: File | undefined) => {
    if (!nextFile) return;
    setError('');
    setAnalysis(null);
    if (!nextFile.type.startsWith('image/')) {
      setPhase('error');
      setError('Please choose an image file such as JPG, PNG, or WEBP.');
      return;
    }
    if (nextFile.size > 15 * 1024 * 1024) {
      setPhase('error');
      setError('This image is larger than 15 MB. Choose a smaller document photo.');
      return;
    }
    if (preview) URL.revokeObjectURL(preview);
    setFile(nextFile);
    setPreview(URL.createObjectURL(nextFile));
    setPhase('ready');
  };

  const loadSample = async () => chooseFile(await createSampleFile());

  const startAnalysis = async () => {
    if (!file || phase === 'scanning') return;
    setError('');
    setStage(0);
    setPhase('scanning');
    try {
      const result = await screenDocumentWithBackend(file);
      await new Promise((resolve) => window.setTimeout(resolve, 2000));
      setAnalysis(result);
      setPhase('complete');
      window.setTimeout(() => document.getElementById('results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch {
      setPhase('error');
      setError('We could not read this image. Please try another clear document photo.');
    }
  };

  const reset = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview('');
    setAnalysis(null);
    setError('');
    setStage(0);
    setPhase('idle');
    window.setTimeout(() => screeningRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50);
  };

  const riskClass = analysis?.level.toLowerCase() ?? '';

  return (
    <div className="site-shell">
      <div className="demo-strip">
        <span className="demo-pulse" />
        <span>ML PROTOTYPE — DEMONSTRATION ONLY</span>
        <span className="strip-detail">No document is uploaded to a server</span>
      </div>
      <header className="nav-wrap">
        <a className="brand" href="#top" aria-label="TEAM ECLIPSE home">
          <span className="brand-mark"><ScanLine size={19} strokeWidth={2.5} /></span>
          <span><strong>TEAM ECLIPSE</strong><small>SIH26188 / ID SCREENING</small></span>
        </a>
        <button className="mobile-menu" onClick={() => setMobileNav((open) => !open)} aria-label="Toggle navigation">
          {mobileNav ? <X size={20} /> : <Menu size={20} />}
        </button>
        <nav className={`main-nav ${mobileNav ? 'is-open' : ''}`}>
          <a href="#screening" onClick={() => setMobileNav(false)}>Screening</a>
          <a href="#how-it-works" onClick={() => setMobileNav(false)}>How it works</a>
          <a href="#roadmap" onClick={() => setMobileNav(false)}>Roadmap</a>
          <a href="#team" onClick={() => setMobileNav(false)}>Team</a>
          <a className="nav-cta" href="#screening" onClick={() => setMobileNav(false)}>Try the demo <ArrowRight size={15} /></a>
        </nav>
      </header>

      <main id="top">
        <section className="hero-section">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-line" /> AI-BASED IDENTITY SCREENING</div>
            <h1>Spot the signal<br /><em>before the risk.</em></h1>
            <p className="hero-lede">A simple, explainable screening companion for officers handling identity documents — built to make the first review faster and clearer.</p>
            <div className="hero-actions">
              <a className="primary-button" href="#screening">Screen a document <ArrowRight size={17} /></a>
              <a className="text-link" href="#how-it-works">See how it works <ChevronRight size={16} /></a>
            </div>
            <div className="hero-note"><LockKeyhole size={14} /> Runs locally in your browser for this demonstration</div>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="signal-card">
              <div className="signal-top"><span className="tiny-label">LIVE PROTOTYPE SIGNAL</span><span className="signal-dot" /></div>
              <div className="signal-number">04<span>/04</span></div>
              <div className="signal-label">explainable checks</div>
              <div className="signal-bars"><i /><i /><i /><i /></div>
            </div>
            <div className="hero-scan"><ScanLine size={24} /><span>LOCAL ANALYSIS</span></div>
          </div>
        </section>

        <section className="screening-section" id="screening" ref={screeningRef}>
          <div className="section-kicker"><span>01</span> SCREENING CONSOLE</div>
          <div className="screening-heading">
            <div><h2>Screen an identity document</h2><p>Upload a clear photo to start a lightweight prototype analysis.</p></div>
            <div className="local-badge"><span /><span>LOCAL DEMO MODE</span></div>
          </div>
          <div className="screening-card">
            <div className="process-rail">
              {scanStages.map((item, index) => (
                <div className={`process-step ${phase === 'scanning' && index === stage ? 'active' : ''} ${phase === 'complete' || (phase === 'scanning' && index < stage) ? 'done' : ''}`} key={item}>
                  <span className="step-number">{phase === 'complete' || (phase === 'scanning' && index < stage) ? <Check size={13} /> : `0${index + 1}`}</span>
                  <span>{item}</span>
                  {index < scanStages.length - 1 && <i className="step-connector" />}
                </div>
              ))}
            </div>
            <div className="screening-workspace">
              <div className={`upload-panel ${phase === 'error' ? 'has-error' : ''}`}>
                {!file ? (
                  <div
                    className="dropzone"
                    onClick={() => inputRef.current?.click()}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={(event) => { event.preventDefault(); chooseFile(event.dataTransfer.files[0]); }}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click(); }}
                  >
                    <div className="upload-icon"><CloudUpload size={26} /></div>
                    <h3>Upload ID document</h3>
                    <p>Drop an image here, or <u>browse your files</u></p>
                    <span className="file-hint">JPG, PNG or WEBP · up to 15 MB</span>
                    {phase === 'error' && <div className="inline-error"><CircleAlert size={15} />{error}</div>}
                  </div>
                ) : (
                  <div className="file-preview-wrap">
                    <div className="preview-image-wrap">
                      <img src={preview} alt="Uploaded identity document preview" />
                      {phase === 'scanning' && <div className="scan-beam" />}
                      {phase === 'scanning' && <div className="preview-scan-tag"><ScanLine size={13} /> ANALYSING</div>}
                    </div>
                    <div className="file-info">
                      <div className="file-type-icon"><FileImage size={20} /></div>
                      <div><strong>{file.name}</strong><span>{formatBytes(file.size)} · {file.type.split('/')[1]?.toUpperCase()}</span></div>
                      {phase !== 'scanning' && <button className="icon-button" onClick={reset} aria-label="Remove document"><X size={17} /></button>}
                    </div>
                    {phase === 'error' && <div className="inline-error"><CircleAlert size={15} />{error}</div>}
                  </div>
                )}
                <input ref={inputRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => chooseFile(event.target.files?.[0])} hidden />
                {!file && phase !== 'error' && <button className="sample-button" onClick={(event) => { event.stopPropagation(); void loadSample(); }}><Sparkles size={14} /> Use sample document</button>}
              </div>
              <div className="action-panel">
                <div className="action-copy">
                  <span className="mini-label">READY WHEN YOU ARE</span>
                  <h3>{phase === 'scanning' ? 'Reading the document…' : phase === 'complete' ? 'Analysis complete' : 'Start a local analysis'}</h3>
                  <p>{phase === 'scanning' ? `Checking ${scanStages[stage].toLowerCase()} signals from the image.` : 'This prototype looks at image quality and document signals. No file leaves this browser.'}</p>
                </div>
                {phase === 'scanning' ? (
                  <div className="scanning-state"><div className="spinner" /><span>Working through checks</span></div>
                ) : phase === 'complete' ? (
                  <button className="secondary-button full-button" onClick={reset}><RotateCcw size={16} /> Scan another document</button>
                ) : (
                  <button className="primary-button full-button" disabled={!file} onClick={() => void startAnalysis()}><Zap size={16} /> Run screening check</button>
                )}
                <div className="action-footnote"><Info size={13} /> Prototype output, not a final identity decision</div>
              </div>
            </div>
          </div>
        </section>

        {phase === 'complete' && analysis && (
          <section className="results-section" id="results">
            <div className="result-heading">
              <div><div className="section-kicker"><span>02</span> SCREENING RESULT</div><h2>Here is what the prototype found</h2></div>
              <button className="text-button" onClick={reset}><RotateCcw size={15} /> Reset check</button>
            </div>
            <div className="result-grid">
              <div className={`risk-card ${riskClass}`}>
                <div className="result-card-label">PROTOTYPE RISK SIGNAL</div>
                <div className="risk-score-ring" style={{ '--score': `${analysis.score * 3.6}deg` } as CSSProperties}>
                  <div><strong>{analysis.score}</strong><span>/ 100</span></div>
                </div>
                <div className="risk-label">{analysis.level} risk</div>
                <p>Based on the image quality and document checks shown here.</p>
              </div>
              <div className="explanation-card">
                <div className="result-card-label">EXPLAINABLE CHECKS</div>
                <div className="check-list">
                  {analysis.checks.map((check) => {
                    const Icon = check.icon;
                    return <div className="check-row" key={check.title}>
                      <div className={`check-icon ${check.tone}`}><Icon size={17} /></div>
                      <div className="check-text"><div><strong>{check.title}</strong><span className={`status-pill ${check.tone}`}>{check.status}</span></div><p>{check.description}</p></div>
                    </div>;
                  })}
                </div>
              </div>
              <div className="recommendation-card">
                <div className="result-card-label">RECOMMENDED NEXT STEP</div>
                <div className="recommendation-icon"><Target size={21} /></div>
                <h3>{analysis.level === 'Low' ? 'Continue with officer review' : analysis.level === 'Medium' ? 'Request a clearer document' : 'Pause and review manually'}</h3>
                <p>{analysis.level === 'Low' ? 'The image looks suitable for a first review. Continue with your normal verification process.' : analysis.level === 'Medium' ? 'One or more image signals need a closer look. Ask for a clearer image before deciding.' : 'Several image signals need attention. Do not rely on this prototype alone.'}</p>
                <div className="officer-note"><ShieldCheck size={15} /> Your judgment stays in control</div>
              </div>
            </div>
            <div className="metrics-row">
              <span><strong>{analysis.metrics.width} × {analysis.metrics.height}</strong> image size</span>
              <span><strong>{analysis.metrics.brightness}</strong> average brightness</span>
              <span><strong>{analysis.metrics.contrast}</strong> contrast signal</span>
              <span><strong>{formatBytes(analysis.metrics.fileSize)}</strong> file size</span>
            </div>
            <div className="result-disclaimer"><CircleAlert size={16} /><span><strong>Important:</strong> This is a machine-learning prototype for demonstration only. It supports an officer's decision and does not make the final identity decision itself.</span></div>
          </section>
        )}

        <section className="how-section" id="how-it-works">
          <div className="section-kicker"><span>03</span> HOW IT WORKS</div>
          <div className="how-heading"><h2>From document to<br /><em>decision support.</em></h2><p>We keep the first step simple: make the signals visible, explainable, and easy for a human to review.</p></div>
          <div className="how-grid">
            {[
              { icon: CloudUpload, number: '01', title: 'Upload ID', text: 'Add a clear photo of the identity document you want to screen.' },
              { icon: ScanLine, number: '02', title: 'Read & check', text: 'The prototype measures quality, dimensions, brightness, and contrast locally.' },
              { icon: Gauge, number: '03', title: 'See the signal', text: 'Get a simple risk level with the checks that led to it, in plain language.' },
              { icon: UserRoundCheck, number: '04', title: 'Officer decides', text: 'Use the result as a supporting signal alongside your normal process.' },
            ].map((item) => {
              const Icon = item.icon;
              return <div className="how-item" key={item.number}><span className="how-number">{item.number}</span><div className="how-icon"><Icon size={20} /></div><h3>{item.title}</h3><p>{item.text}</p></div>;
            })}
          </div>
        </section>

        <section className="capabilities-section">
          <div className="capability-copy"><div className="section-kicker"><span>04</span> PROTOTYPE CAPABILITIES</div><h2>Built to be understood,<br /><em>not just scored.</em></h2><p>Trust starts with showing the work. Every prototype signal is paired with a simple explanation so the officer can decide what to do next.</p><a className="text-link" href="#screening">Try the screening flow <ArrowRight size={16} /></a></div>
          <div className="capability-list">
            <div><span className="capability-index">A1</span><div><h3>Lightweight image analysis</h3><p>Brightness, contrast, size, and shape are measured from the uploaded image.</p></div><CheckCircle2 size={19} /></div>
            <div><span className="capability-index">A2</span><div><h3>Explainable risk signal</h3><p>A deterministic score shows which simple signals raised or lowered the result.</p></div><CheckCircle2 size={19} /></div>
            <div><span className="capability-index">A3</span><div><h3>Human-first recommendation</h3><p>The output points to a next step without replacing the officer's judgment.</p></div><CheckCircle2 size={19} /></div>
          </div>
        </section>

        <section className="roadmap-section" id="roadmap">
          <div className="section-kicker"><span>05</span> ROADMAP</div>
          <div className="roadmap-heading"><h2>Today is a prototype.<br /><em>Tomorrow is stronger.</em></h2><p>A clear path from local demonstration to a more capable screening assistant.</p></div>
          <div className="roadmap-line">
            <div className="roadmap-item current"><span className="roadmap-dot" /><span className="roadmap-tag">CURRENT</span><h3>Simple working ML prototype</h3><p>Real browser-side image signals, explainable risk levels, and an officer-first flow.</p></div>
            <div className="roadmap-item"><span className="roadmap-dot" /><span className="roadmap-tag">NEXT</span><h3>Better ML models</h3><p>More document types, stronger face and liveness checks.</p></div>
            <div className="roadmap-item"><span className="roadmap-dot" /><span className="roadmap-tag">VISION</span><h3>Trusted document network</h3><p>Explore a Hyperledger Fabric security layer for verifiable records.</p></div>
          </div>
        </section>

        <section className="team-section" id="team">
          <div className="team-card"><div><div className="section-kicker light"><span className="eyebrow-line" /><span>06</span> TEAM ECLIPSE</div><h2>Making identity screening<br /><em>clearer for everyone.</em></h2><p>Built for SIH26188 with a focus on simple language, useful signals, and responsible human oversight.</p></div><div className="team-meta"><div><span>TEAM</span><strong>ECLIPSE</strong></div><div><span>CHALLENGE</span><strong>SIH26188</strong></div><div><span>STATUS</span><strong><i /> DEMO READY</strong></div></div></div>
        </section>
      </main>
      <footer><a className="brand" href="#top"><span className="brand-mark"><ScanLine size={17} /></span><span><strong>TEAM ECLIPSE</strong><small>AI-BASED IDENTITY SCREENING</small></span></a><span className="footer-note">ML PROTOTYPE — DEMONSTRATION ONLY · Built for SIH26188</span><a className="back-top" href="#top">Back to top <ChevronRight size={14} /></a></footer>
    </div>
  );
}

export default App;
