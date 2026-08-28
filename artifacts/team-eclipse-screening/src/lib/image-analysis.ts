// Browser-side lightweight image analysis for demo purposes

export type AnalysisResult = {
  score: 'Low' | 'Medium' | 'High';
  checks: {
    documentValidation: { status: 'pass' | 'fail' | 'warn'; message: string };
    tamperingAnalysis: { status: 'pass' | 'fail' | 'warn'; message: string };
    faceVerification: { status: 'pass' | 'fail' | 'warn'; message: string };
    dataConsistency: { status: 'pass' | 'fail' | 'warn'; message: string };
  };
  metrics: {
    resolution: string;
    brightness: number;
    contrast: number;
    sharpness: number;
  };
};

export async function analyzeImage(file: File, imageUrl: string): Promise<AnalysisResult> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Canvas not supported'));
        return;
      }
      
      // We don't need full resolution for basic stats, scale down for speed
      const scale = Math.min(1, 800 / Math.max(img.width, img.height));
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      
      let rSum = 0, gSum = 0, bSum = 0;
      let count = 0;
      
      for (let i = 0; i < data.length; i += 4) {
        rSum += data[i];
        gSum += data[i+1];
        bSum += data[i+2];
        count++;
      }
      
      const rAvg = rSum / count;
      const gAvg = gSum / count;
      const bAvg = bSum / count;
      
      // Calculate perceptive luminance
      const brightness = (0.299 * rAvg + 0.587 * gAvg + 0.114 * bAvg);
      
      // Calculate standard deviation (contrast approximation)
      let varianceSum = 0;
      for (let i = 0; i < data.length; i += 4) {
        const lum = (0.299 * data[i] + 0.587 * data[i+1] + 0.114 * data[i+2]);
        varianceSum += Math.pow(lum - brightness, 2);
      }
      const contrast = Math.sqrt(varianceSum / count);
      
      // Pseudo-sharpness via simple edge detection variance could be done, 
      // but let's use a deterministic mock based on contrast for the demo
      const sharpness = Math.min(100, contrast * 1.5);
      
      // Aspect ratio check (common IDs are roughly 1.58 - CR80 standard)
      const aspectRatio = img.width / img.height;
      const isLandscape = aspectRatio > 1;
      const normalizedRatio = isLandscape ? aspectRatio : 1 / aspectRatio;
      const isIdProportion = normalizedRatio > 1.4 && normalizedRatio < 1.7;
      
      // Generate deterministic results based on file size, brightness, contrast, and aspect ratio
      
      let totalRisk = 0;
      
      // 1. Document Validation
      let docStatus: 'pass' | 'fail' | 'warn' = 'pass';
      let docMessage = 'Format and dimensions verified.';
      
      if (!isIdProportion) {
        docStatus = 'warn';
        docMessage = 'Unusual aspect ratio for standard ID.';
        totalRisk += 1;
      }
      if (img.width < 500 || img.height < 500) {
        docStatus = 'fail';
        docMessage = 'Resolution too low for reliable extraction.';
        totalRisk += 2;
      }
      
      // 2. Tampering Analysis (Prototype signal based on image quality stats)
      let tamperStatus: 'pass' | 'fail' | 'warn' = 'pass';
      let tamperMessage = 'No digital manipulation artifacts detected.';
      
      if (contrast < 20 || brightness < 40 || brightness > 220) {
        tamperStatus = 'warn';
        tamperMessage = 'Sub-optimal lighting conditions; confidence reduced.';
        totalRisk += 1;
      }
      // Deterministic pseudo-randomness based on file size modulo
      if (file.size % 7 === 0) {
        tamperStatus = 'fail';
        tamperMessage = 'Inconsistent compression blocks detected.';
        totalRisk += 2;
      }
      
      // 3. Face Verification (Simulated prototype)
      let faceStatus: 'pass' | 'fail' | 'warn' = 'pass';
      let faceMessage = 'Primary facial geometry matches reference standard.';
      
      if (file.size % 5 === 0) {
        faceStatus = 'warn';
        faceMessage = 'Partial glare over structural features.';
        totalRisk += 1;
      }
      
      // 4. Data Consistency (Simulated prototype)
      let dataStatus: 'pass' | 'fail' | 'warn' = 'pass';
      let dataMessage = 'MRZ and visual zones cross-check successful.';
      
      if (file.size % 13 === 0) {
        dataStatus = 'fail';
        dataMessage = 'Checksum mismatch in simulated MRZ read.';
        totalRisk += 2;
      }
      
      // Overall Score
      let score: 'Low' | 'Medium' | 'High' = 'Low';
      if (totalRisk >= 3) {
        score = 'High';
      } else if (totalRisk > 0) {
        score = 'Medium';
      }
      
      resolve({
        score,
        checks: {
          documentValidation: { status: docStatus, message: docMessage },
          tamperingAnalysis: { status: tamperStatus, message: tamperMessage },
          faceVerification: { status: faceStatus, message: faceMessage },
          dataConsistency: { status: dataStatus, message: dataMessage }
        },
        metrics: {
          resolution: `${img.width} × ${img.height}`,
          brightness: Math.round((brightness / 255) * 100),
          contrast: Math.round(contrast),
          sharpness: Math.round(sharpness)
        }
      });
    };
    
    img.onerror = () => {
      reject(new Error('Failed to load image for analysis'));
    };
    
    img.src = imageUrl;
  });
}
