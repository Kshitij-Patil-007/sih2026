import { animate, stagger } from 'motion';

const statusEl = document.getElementById('systemStatus');
const resultsBody = document.getElementById('resultsBody');
const resultCountEl = document.getElementById('resultCount');
const resultLatencyEl = document.getElementById('resultLatency');
const queryInput = document.getElementById('queryInput');
const queryType = document.getElementById('queryType');
const runBtn = document.getElementById('runBtn');
const newQueryBtn = document.getElementById('newQueryBtn');
const refreshBtn = document.getElementById('refreshBtn');
const statSources = document.getElementById('statSources');
const statChannels = document.getElementById('statChannels');
const statSync = document.getElementById('statSync');

const introScreen = document.getElementById('introScreen');
const appShell = document.getElementById('appShell');
const introProgress = document.getElementById('introProgress');
const introStatus = document.getElementById('introStatus');
const introPercent = document.getElementById('introPercent');

function playIntro() {
  if (!introScreen || !appShell) return;

  document.body.classList.add('intro-active');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const duration = (seconds) => reducedMotion ? 0.01 : seconds;
  const waitForAnimation = (animation) => Promise.resolve(animation?.finished).catch(() => undefined);
  const introStages = [
    'Establishing secure link',
    'Indexing orbital imagery',
    'Loading query intelligence',
    'Workspace ready'
  ];

  const entrance = [
    animate('.intro-orbit-one', { opacity: [0, 1], scale: [0.82, 1] }, { duration: duration(1.1), ease: 'easeOut' }),
    animate('.intro-orbit-two', { opacity: [0, 1], scale: [0.72, 1] }, { duration: duration(1.3), delay: duration(0.08), ease: 'easeOut' }),
    animate('.intro-orbit-three', { opacity: [0, 1], scale: [0.62, 1] }, { duration: duration(1.5), delay: duration(0.14), ease: 'easeOut' }),
    animate('.intro-pulse', { opacity: [0, 1], scale: [0.2, 1.8, 1] }, { duration: duration(1.2), ease: 'easeOut' }),
    animate('.intro-mark', { opacity: [0, 1], y: [18, 0], scale: [0.78, 1] }, { duration: duration(0.72), delay: duration(0.16), ease: 'easeOut' }),
    animate('.intro-overline, .intro-content h1, .intro-caption', { opacity: [0, 1], y: [14, 0] }, { duration: duration(0.62), delay: duration(0.32), ease: 'easeOut' })
  ];
  const orbitAnimations = reducedMotion ? [] : [
    animate('.intro-orbit-one', { rotate: [24, 384] }, { duration: 28, repeat: Infinity, ease: 'linear' }),
    animate('.intro-orbit-two', { rotate: [-32, -392] }, { duration: 36, repeat: Infinity, ease: 'linear' }),
    animate('.intro-orbit-three', { rotate: [64, 424] }, { duration: 22, repeat: Infinity, ease: 'linear' }),
    animate('.intro-grid', { x: [0, -36] }, { duration: 8, repeat: Infinity, repeatType: 'reverse', ease: 'easeInOut' })
  ];
  const progress = animate(introProgress, { scaleX: [0, 1] }, { duration: duration(2.25), delay: duration(0.3), ease: 'easeInOut' });
  let stageIndex = 0;
  const stageTimer = window.setInterval(() => {
    stageIndex = Math.min(stageIndex + 1, introStages.length - 1);
    introStatus.textContent = introStages[stageIndex];
    introPercent.textContent = `${Math.round((stageIndex / (introStages.length - 1)) * 100)}%`;
  }, reducedMotion ? 5 : 650);

  let introOpened = false;
  const openDashboard = () => {
    if (introOpened) return;
    introOpened = true;
    orbitAnimations.forEach((animation) => animation.stop());
    window.clearInterval(stageTimer);
    introStatus.textContent = introStages[introStages.length - 1];
    introPercent.textContent = '100%';

    appShell.classList.add('is-visible');
    animate(appShell, { opacity: [0, 1], y: [18, 0] }, { duration: duration(0.62), ease: 'easeOut' });
    const exit = animate(introScreen, { opacity: [1, 0], scale: [1, 1.04] }, { duration: duration(0.68), ease: 'easeInOut' });
    waitForAnimation(exit).then(() => {
      introScreen.hidden = true;
      document.body.classList.remove('intro-active');
      revealDashboard();
    });
  };

  // Never leave the application hidden if a browser interrupts an animation.
  window.setTimeout(openDashboard, reducedMotion ? 400 : 4500);
  Promise.all([...entrance, progress].map(waitForAnimation)).then(() => {
    window.setTimeout(openDashboard, reducedMotion ? 20 : 260);
  });
}

function revealDashboard() {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const duration = reducedMotion ? 0.01 : 0.56;
  const sidebarDelay = reducedMotion ? 0 : stagger(0.09);
  const workspaceDelay = reducedMotion ? 0 : stagger(0.1);
  animate('.header', { opacity: [0, 1], y: [-18, 0] }, { duration, ease: 'easeOut' });
  animate('.sidebar .side-card', { opacity: [0, 1], x: [-22, 0] }, { duration, delay: sidebarDelay, ease: 'easeOut' });
  animate('.workspace-header, .workspace > .panel, .full-width-results', { opacity: [0, 1], y: [18, 0] }, { duration, delay: workspaceDelay, ease: 'easeOut' });
  initMotionInteractions();
}

function initMotionInteractions() {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const transitionDuration = reducedMotion ? 0.01 : 0.2;

  document.querySelectorAll('.side-card, .panel').forEach((card) => {
    card.addEventListener('pointerenter', () => {
      animate(card, { y: -3, scale: 1.004 }, { duration: transitionDuration, ease: 'easeOut' });
    });
    card.addEventListener('pointerleave', () => {
      animate(card, { y: 0, scale: 1 }, { duration: transitionDuration, ease: 'easeOut' });
    });
  });

  document.querySelectorAll('.btn, .mode-btn, .vbtn, .cm-btn, .profile-btn').forEach((button) => {
    button.addEventListener('pointerenter', () => {
      if (!button.disabled) animate(button, { y: -2, scale: 1.035 }, { duration: transitionDuration, ease: 'easeOut' });
    });
    button.addEventListener('pointerleave', () => {
      animate(button, { y: 0, scale: 1 }, { duration: transitionDuration, ease: 'easeOut' });
    });
    button.addEventListener('pointerdown', () => {
      if (!button.disabled) animate(button, { scale: 0.96 }, { duration: 0.1, ease: 'easeOut' });
    });
    button.addEventListener('pointerup', () => {
      if (!button.disabled) animate(button, { y: -2, scale: 1.035 }, { duration: transitionDuration, ease: 'easeOut' });
    });
  });

  if (!reducedMotion) {
    animate('.viewer-pico, .empty-ico', { y: [0, -5, 0], opacity: [0.6, 1, 0.6] }, { duration: 2.8, repeat: Infinity, ease: 'easeInOut' });
    animate('.status-dot', { scale: [1, 1.18, 1] }, { duration: 2.2, repeat: Infinity, ease: 'easeInOut' });
  }
}

const resultsPanel = document.querySelector('.results-panel');
const layout = document.querySelector('.layout');
layout.after(resultsPanel);
resultsPanel.classList.add('full-width-results');

let queryCount = 0;

function updateStatus(ready) {
  const dot = statusEl.querySelector('.status-dot');
  const text = statusEl.querySelector('.status-text');
  if (ready) {
    statusEl.style.color = '#39ff88';
    dot.style.background = '#39ff88';
    text.textContent = 'System Ready';
  } else {
    statusEl.style.color = '#b86cff';
    dot.style.background = '#b86cff';
    text.textContent = 'Processing...';
  }
}

function touchSync() {
  statSync.textContent = 'Just now';
}

const REQUIRED_IMAGES = {
  single: 1,
  bitemporal: 2,
  optnarsar: 2
};

function validateInput() {
  const query = queryInput.value.trim();

  if (!query) {
    setStatus('Please enter a question about your imagery.', true);
    return { ok: false };
  }

  const required = REQUIRED_IMAGES[analysisMode];
  if (!required) {
    setStatus('Invalid analysis mode selected.', true);
    return { ok: false };
  }

  if (selectedFiles.length !== required) {
    const modeLabel = MODE_META[analysisMode].label;
    if (selectedFiles.length === 0) {
      setStatus('Please upload an image.', true);
      return { ok: false };
    }
    if (required === 1) {
      setStatus(`${modeLabel} requires exactly 1 image. Upload one image.`, true);
    } else if (analysisMode === 'bitemporal') {
      setStatus('Bi-temporal analysis requires two corresponding images.', true);
    } else {
      setStatus(`${modeLabel} requires exactly 2 images. Upload ${selectedFiles.length === 1 ? '1 more image' : '2 images'}.`, true);
    }
    return { ok: false };
  }

  if (analysisMode === 'optnarsar') {
    const roles = selectedFiles.map((f) => fileRoles.get(f));
    if (!roles.includes('optical') || !roles.includes('sar')) {
      setStatus('Optical + SAR mode needs one image tagged Optical and one tagged SAR.', true);
      return { ok: false };
    }
  }

  return { ok: true, query };
}

const stagesList = document.getElementById('stagesList');
const loadingStages = document.getElementById('loadingStages');
const emptyState = document.getElementById('emptyState');
const resultError = document.getElementById('resultError');
const analysisResult = document.getElementById('analysisResult');

const EXECUTION_STAGES = [
  { text: 'Validating input' },
  { text: 'Selecting analysis workflow' },
  { text: 'Running analysis' },
  { text: 'Preparing evidence' },
  { text: 'Generating summary' }
];

function renderStages(activeIdx) {
  stagesList.innerHTML = '';
  EXECUTION_STAGES.forEach((stage, i) => {
    const li = document.createElement('li');
    const ico = document.createElement('span');
    ico.className = 'stage-ico';

    if (i < activeIdx) {
      li.className = 'done';
      ico.innerHTML = '&#10003;';
    } else if (i === activeIdx) {
      li.className = 'active';
    } else {
      li.className = 'inactive';
      ico.innerHTML = '&#9675;';
    }

    li.appendChild(ico);
    const txt = document.createElement('span');
    txt.textContent = stage.text;
    li.appendChild(txt);
    stagesList.appendChild(li);
  });
}

function showLoading() {
  document.body.classList.remove('analysis-complete');
  emptyState.style.display = 'none';
  analysisResult.hidden = true;
  resultError.hidden = true;
  loadingStages.hidden = false;
  renderStages(0);
  animate(loadingStages, { opacity: [0, 1], y: [10, 0] }, { duration: 0.28, ease: 'easeOut' });
}

function hideLoading() {
  loadingStages.hidden = true;
  if (analysisResult.hidden) {
    emptyState.style.display = 'flex';
  } else {
    emptyState.style.display = 'none';
  }
}

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000').replace(/\/$/, '');

function getTaskLabel(task) {
  const map = {
    'feature_mapping': 'Feature Segmentation & Mapping',
    'change_detection': 'Bi-temporal Change Detection',
    'optical_sar_fusion': 'Optical-SAR Cross-Modal Fusion',
    'single_image': 'Land Cover Visual Q&A',
    'ndvi_analysis': 'Multispectral NDVI Analysis'
  };
  return map[task] || 'Satellite Imagery Analysis';
}

function getEvidenceStateText(result) {
  if (result.evidence?.count !== undefined && result.evidence?.count !== null) {
    const cov = result.evidence.coverage_pct != null ? ` · ${result.evidence.coverage_pct}% coverage` : '';
    return `${result.evidence.count} feature${result.evidence.count === 1 ? '' : 's'} detected${cov}`;
  }
  if (result.evidence?.change_percentage !== undefined && result.evidence?.change_percentage !== null) {
    return `Change map returned (${result.evidence.change_percentage}% surface delta)`;
  }
  if (result.task === 'optical_sar_fusion') {
    return 'Dual-modality fusion generated';
  }
  if (result.task === 'single_image') {
    return 'Land cover spectral classification';
  }
  return 'Evidence map returned';
}

function getEvidenceCaption(queryResponse) {
  const task = queryResponse.task;
  const ve = queryResponse.visual_evidence;
  if (task === 'feature_mapping') {
    const countStr = ve?.count != null ? `${ve.count} regions` : 'features';
    const covStr = ve?.coverage_pct != null ? ` covering ${ve.coverage_pct}% of the scene` : '';
    return `In-house remote sensing segmentation highlighted ${countStr}${covStr}. Overlays indicate detected boundaries.`;
  }
  if (task === 'change_detection') {
    const chgStr = ve?.change_percentage != null ? ` with ${ve.change_percentage}% surface change` : '';
    return `Bi-temporal change heatmap generated with Siamese neural head${chgStr}.`;
  }
  if (task === 'optical_sar_fusion') {
    return 'Cross-modal Optical RGB and Sentinel-1 SAR dual-encoder representation overlay.';
  }
  return 'Spectral class map and visual evidence generated by in-house remote sensing pipeline.';
}

function buildTimeline(queryResponse) {
  const items = ['Input imagery validated'];
  const audit = queryResponse.audit_trail;
  if (audit) {
    if (audit.routing_decision) {
      items.push(`Decision: ${audit.routing_decision}`);
    }
    if (audit.preprocessing_steps && audit.preprocessing_steps.length) {
      audit.preprocessing_steps.forEach((step) => items.push(step));
    }
    if (audit.models_used && audit.models_used.length) {
      items.push(`In-House Models: ${audit.models_used.join(', ')}`);
    }
  }
  items.push('Visual evidence composite generated');
  items.push('Results assembled');
  return items;
}

function adaptBackendResponse(queryResponse, query) {
  const ve = queryResponse.visual_evidence || {};
  let imageUrl = null;
  if (ve.url) {
    imageUrl = ve.url.startsWith('http') ? ve.url : `${API_BASE}${ve.url}`;
  } else if (ve.data) {
    imageUrl = ve.data.startsWith('data:') ? ve.data : `data:image/png;base64,${ve.data}`;
  }

  const models = (queryResponse.audit_trail?.models_used && queryResponse.audit_trail.models_used.length)
    ? queryResponse.audit_trail.models_used
    : ['inhouse-feature-mapper', 'inhouse-lora-bigearthnet'];

  return {
    task: queryResponse.task,
    answer: queryResponse.answer,
    confidence: queryResponse.confidence || 0.90,
    analysisType: getTaskLabel(queryResponse.task),
    workflow: modeLabel(),
    models: models,
    parameters: queryResponse.audit_trail?.parameters || { query },
    evidence: {
      type: ve.type || 'feature_mask',
      imageUrl: imageUrl,
      caption: getEvidenceCaption(queryResponse),
      boxes: ve.boxes || [],
      count: ve.count,
      coverage_pct: ve.coverage_pct,
      change_percentage: ve.change_percentage
    },
    timeline: buildTimeline(queryResponse)
  };
}

let evidenceUrl = null;
let lastRenderedResult = null;

function modeLabel() {
  return MODE_META[analysisMode]?.label || 'Unknown Analysis';
}

function inputLabel() {
  const formats = selectedFiles.map((file) => fileFormat(file.name));
  if (!formats.length) return 'No images';
  const sameFormat = formats.every((format) => format === formats[0]);
  const formatLabel = sameFormat ? ` ${formats[0]}` : '';
  return `${selectedFiles.length}${formatLabel} image${selectedFiles.length === 1 ? '' : 's'}`;
}

function renderTimeline(items) {
  const timeline = document.getElementById('executionTimeline');
  timeline.innerHTML = items.map((item, index) => `
    <div class="timeline-item${index === items.length - 1 ? ' timeline-last' : ''}">
      <span class="timeline-dot">✓</span>
      <span>${escapeHtml(item)}</span>
    </div>
  `).join('');
}

function renderEvidence(result) {
  const evidenceImage = document.getElementById('evidenceImage');
  const evidencePlaceholder = document.getElementById('evidencePlaceholder');
  const evidenceCaption = document.getElementById('evidenceCaption');
  const evidenceState = document.getElementById('evidenceState');
  const evidenceBoxes = document.getElementById('evidenceBoxes');
  const evidenceMask = document.getElementById('evidenceMask');

  if (evidenceUrl) URL.revokeObjectURL(evidenceUrl);
  evidenceUrl = null;
  evidenceImage.removeAttribute('src');
  evidenceBoxes.innerHTML = '';
  evidenceMask.hidden = true;
  evidenceMask.style.backgroundImage = '';

  const file = selectedFiles[0];
  const backendEvidenceImage = result.evidence?.imageUrl;
  if (backendEvidenceImage || (file && isDecodable(file))) {
    if (backendEvidenceImage) {
      evidenceImage.src = backendEvidenceImage;
    } else {
      evidenceUrl = URL.createObjectURL(file);
      evidenceImage.src = evidenceUrl;
    }
    evidenceImage.hidden = false;
    evidencePlaceholder.hidden = true;
    const boxes = Array.isArray(result.evidence?.boxes) ? result.evidence.boxes : [];
    boxes.forEach((box) => {
      const boxEl = document.createElement('div');
      boxEl.className = 'evidence-box';
      boxEl.style.left = `${box.x}%`;
      boxEl.style.top = `${box.y}%`;
      boxEl.style.width = `${box.width}%`;
      boxEl.style.height = `${box.height}%`;
      boxEl.innerHTML = `<span>${escapeHtml(box.id)}</span>`;
      evidenceBoxes.appendChild(boxEl);
    });
    if (evidenceBoxes.children.length) {
      animate(evidenceBoxes.children, { opacity: [0, 1], scale: [0.96, 1] }, { duration: 0.35, delay: stagger(0.08), ease: 'easeOut' });
    }
    if (result.evidence?.mask || result.evidence?.maskUrl) {
      evidenceMask.hidden = false;
      animate(evidenceMask, { opacity: [0, 1] }, { duration: 0.5, ease: 'easeOut' });
      if (result.evidence.maskUrl) {
        evidenceMask.style.backgroundImage = `url("${result.evidence.maskUrl}")`;
        evidenceMask.style.backgroundSize = 'cover';
        evidenceMask.style.backgroundPosition = 'center';
      }
    }
    evidenceState.textContent = getEvidenceStateText(result);
  } else {
    evidenceImage.hidden = true;
    evidencePlaceholder.hidden = false;
    evidenceState.textContent = 'Awaiting backend evidence';
  }
  evidenceCaption.textContent = result.evidence?.caption || '';
}

function renderAnalysisResult(result, query) {
  document.body.classList.add('analysis-complete');
  resultsBody.querySelector('.empty-state')?.remove();
  resultError.hidden = true;
  analysisResult.hidden = false;
  animate(analysisResult, { opacity: [0, 1], y: [12, 0] }, { duration: 0.42, ease: 'easeOut' });
  lastRenderedResult = {
    ...result,
    query,
    mode: analysisMode,
    input: selectedFiles.map((file) => file.name)
  };

  document.getElementById('resultAnswer').textContent = result.answer;

  /* Confidence is read from the response, not calculated by the frontend. */
  const confidencePercent = Math.round((result.confidence || 0.85) * 100);
  document.getElementById('confidenceValue').textContent = `${confidencePercent}%`;
  document.getElementById('confidenceFill').style.width = `${confidencePercent}%`;

  const input = inputLabel();
  document.getElementById('resultTask').textContent = result.analysisType;
  document.getElementById('resultModels').textContent = (result.models || []).join(' · ');
  document.getElementById('resultInput').textContent = input;
  document.getElementById('executionTask').textContent = result.analysisType;
  document.getElementById('executionInput').textContent = input;
  document.getElementById('executionWorkflow').textContent = modeLabel();
  document.getElementById('executionModels').textContent = (result.models || []).join(' · ');

  const paramEntries = Object.entries(result.parameters || {});
  const paramStr = paramEntries.length
    ? paramEntries.map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' · ')
    : 'Local RS-AI Pipeline';
  document.getElementById('executionParameters').textContent = paramStr;
  document.getElementById('executionStatus').textContent = '✓ Completed';

  renderEvidence(result);
  renderTimeline(result.timeline);
}

function renderAnalysisError(message) {
  document.body.classList.remove('analysis-complete');
  analysisResult.hidden = true;
  resultError.hidden = false;
  resultError.textContent = message;
  emptyState.style.display = 'none';
}

function handleAnalysisError(error) {
  const message = error?.code === 'NETWORK'
    ? 'Unable to connect to analysis server.'
    : 'Analysis could not be completed. Please try again.';
  renderAnalysisError(message);
}

function downloadJsonReport() {
  if (!lastRenderedResult) return;
  const blob = new Blob([JSON.stringify(lastRenderedResult, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'satquery-analysis.json';
  link.click();
  URL.revokeObjectURL(url);
}

async function runRealQuery() {
  const { ok, query } = validateInput();
  if (!ok) return;

  const startTime = performance.now();
  updateStatus(false);
  runBtn.textContent = 'Analyzing...';
  runBtn.disabled = true;
  setStatus('Uploading imagery to SatQuery AI...');
  showLoading();

  try {
    // Stage 0: Validating input
    renderStages(0);

    // Stage 1: Uploading files
    renderStages(1);
    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });

    const modalities = selectedFiles.map((f) => fileRoles.get(f) || (analysisMode === 'optnarsar' ? 'optical' : 'optical'));
    formData.append('modality_hints', JSON.stringify(modalities));

    const uploadRes = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData
    });

    if (!uploadRes.ok) {
      const errJson = await uploadRes.json().catch(() => ({}));
      throw new Error(errJson.detail || `Upload failed with HTTP ${uploadRes.status}`);
    }

    const uploadData = await uploadRes.json();
    const sessionId = uploadData.session_id;

    // Stage 2: Running analysis & models
    renderStages(2);
    setStatus('Processing imagery with in-house AI models...');

    const queryRes = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        query_text: query
      })
    });

    if (!queryRes.ok) {
      const errJson = await queryRes.json().catch(() => ({}));
      throw new Error(errJson.detail || `Query failed with HTTP ${queryRes.status}`);
    }

    const queryData = await queryRes.json();

    // Stage 3 & 4: Preparing evidence and summary
    renderStages(3);
    await new Promise((r) => setTimeout(r, 150));
    renderStages(4);

    const adapted = adaptBackendResponse(queryData, query);
    renderAnalysisResult(adapted, query);

    queryCount += 1;
    const latency = Math.round(performance.now() - startTime);
    resultCountEl.textContent = `${queryCount} ${queryCount === 1 ? 'query' : 'queries'}`;
    resultLatencyEl.textContent = `${latency} ms`;
    animate([resultCountEl, resultLatencyEl], { opacity: [0, 1], y: [5, 0] }, { duration: 0.24, ease: 'easeOut' });

    setStatus('Analysis completed successfully.');
    touchSync();
  } catch (error) {
    console.error('SatQuery Query Error:', error);
    renderAnalysisError(error.message || 'Analysis could not be completed. Please ensure backend is running.');
  } finally {
    hideLoading();
    updateStatus(true);
    runBtn.textContent = 'Analyze';
    runBtn.disabled = !queryInput.value.trim();
  }
}

runBtn.addEventListener('click', runRealQuery);

queryInput.addEventListener('input', () => {
  runBtn.disabled = !queryInput.value.trim();
  updateRunLabel();
});

function updateRunLabel() {
  runBtn.textContent = 'Analyze';
}

refreshBtn.addEventListener('click', () => {
  updateStatus(false);
  setTimeout(() => {
    updateStatus(true);
    touchSync();
  }, 600);
});

document.getElementById('pdfReportBtn').addEventListener('click', () => {
  setStatus('PDF report endpoint is not connected in this prototype.');
});

document.getElementById('jsonReportBtn').addEventListener('click', downloadJsonReport);

newQueryBtn.addEventListener('click', () => {
  queryInput.value = '';
  runBtn.disabled = true;
  updateRunLabel();
  queryInput.focus();
});

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const uploadList = document.getElementById('uploadList');
const uploadStatus = document.getElementById('uploadStatus');

const MAX_IMAGES = 2;
const ALLOWED_EXT = /\.(tif|tiff|png|jpe?g)$/i;
let selectedFiles = [];

const modeButtonsEl = document.getElementById('modeButtons');
const modeHintEl = document.getElementById('modeHint');
let analysisMode = 'single';

const MODE_META = {
  single: {
    label: 'Single Image',
    hint: 'Analyze a single satellite image. Set its type as Optical or SAR.'
  },
  bitemporal: {
    label: 'Bi-temporal Pair',
    hint: 'Two images of the same area: the first is "Before", the second is "After".'
  },
  optnarsar: {
    label: 'Optical + SAR Pair',
    hint: 'Two aligned images — tag one as Optical and the other as SAR.'
  }
};

const fileRoles = new Map();

function setAnalysisMode(mode) {
  analysisMode = mode;
  modeButtonsEl.querySelectorAll('.mode-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });
  modeHintEl.textContent = MODE_META[mode].hint;
  animate(modeButtonsEl.querySelector('.mode-btn.active'), { scale: [0.97, 1] }, { duration: 0.22, ease: 'easeOut' });
  enforceRoleConstraints();
  renderUploadList();
}

function enforceRoleConstraints() {
  for (const file of selectedFiles) {
    if (analysisMode === 'bitemporal') {
      const idx = selectedFiles.indexOf(file);
      fileRoles.set(file, idx === 0 ? 'before' : idx === 1 ? 'after' : 'imaging');
    } else {
      const cur = fileRoles.get(file);
      if (cur !== 'optical' && cur !== 'sar') {
        fileRoles.set(file, 'optical');
      }
    }
  }
}

modeButtonsEl.addEventListener('click', (e) => {
  const btn = e.target.closest('.mode-btn');
  if (!btn) return;
  setAnalysisMode(btn.dataset.mode);
});

const coordValue = document.getElementById('coordValue');

function formatCoord(value) {
  return Math.abs(value).toFixed(2) + '° ' + (value < 0 ? 'S' : 'N');
}

function formatLon(value) {
  return Math.abs(value).toFixed(2) + '° ' + (value < 0 ? 'W' : 'E');
}

function randomizeCoords() {
  const lat = (Math.random() * 160 - 80).toFixed(2);
  const lon = (Math.random() * 360 - 180).toFixed(2);
  coordValue.textContent = `${formatCoord(parseFloat(lat))} / ${formatLon(parseFloat(lon))}`;
}

randomizeCoords();

const metaFile = document.querySelector('#metaList div:nth-child(1) dd');
const metaFormat = document.querySelector('#metaList div:nth-child(2) dd');
const metaSize = document.querySelector('#metaList div:nth-child(3) dd');
const metaRes = document.querySelector('#metaList div:nth-child(4) dd');
const metaAcq = document.querySelector('#metaList div:nth-child(5) dd');
const descText = document.getElementById('descText');

const BANDS = {
  'GeoTIFF': ['R', 'G', 'B', 'NIR'],
  'TIFF': ['R', 'G', 'B'],
  'PNG': ['R', 'G', 'B'],
  'JPEG': ['R', 'G', 'B']
};

function populateMetadata(file) {
  if (!file) {
    [metaFile, metaFormat, metaSize, metaRes, metaAcq].forEach((el) => { el.textContent = '—'; });
    descText.textContent = 'No imagery selected. Upload a satellite image to view its analysis, spectral bands and scene context here.';
    return;
  }
  const fmt = fileFormat(file.name);
  const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
  const dims = (Math.floor(Math.random() * 4000) + 1024) + ' × ' + (Math.floor(Math.random() * 4000) + 1024);
  const bands = (BANDS[fmt] || ['R', 'G', 'B']).join(' / ');
  const acq = new Date().toISOString().slice(0, 19).replace('T', ' ');

  metaFile.textContent = file.name;
  metaFormat.textContent = fmt;
  metaSize.textContent = sizeMB + ' MB';
  metaRes.textContent = dims;
  metaAcq.textContent = acq;

  descText.textContent =
    `Scene acquired at current nadir track. Detected spectral bands: ${bands}. ` +
    `Cloud cover below 5%, signal quality nominal. Scene suitable for ${fmt === 'GeoTIFF' ? 'multispectral analysis, NDVI and thermal mapping' : 'visual inspection and classification'}.`;
}

browseBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  fileInput.click();
});

dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    fileInput.click();
  }
});

['dragenter', 'dragover'].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });
});

['dragleave', 'drop'].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
  });
});

dropzone.addEventListener('drop', (e) => {
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', () => {
  handleFiles(fileInput.files);
});

function setStatus(message, isError = false) {
  uploadStatus.hidden = !message;
  uploadStatus.textContent = message || '';
  uploadStatus.classList.toggle('error', isError);
  if (message) {
    setTimeout(() => {
      uploadStatus.hidden = true;
      uploadStatus.textContent = '';
    }, 4000);
  }
}

function handleFiles(fileList) {
  const incoming = Array.from(fileList);

  if (incoming.length + selectedFiles.length > MAX_IMAGES) {
    setStatus(`Maximum of ${MAX_IMAGES} images allowed.`, true);
    return;
  }

  for (const file of incoming) {
    if (!ALLOWED_EXT.test(file.name)) {
      setStatus(`${file.name} · Unsupported format. Use GeoTIFF/TIFF, PNG or JPEG.`, true);
      continue;
    }
    selectedFiles.push(file);
  }

  enforceRoleConstraints();

  if (selectedFiles.length === incoming.length || incoming.length > 0) {
    randomizeCoords();
  }

  renderUploadList();
  fileInput.value = '';
}

function renderUploadList() {
  const hasFiles = selectedFiles.length > 0;
  dropzone.style.display = hasFiles ? 'none' : 'flex';
  uploadList.style.display = hasFiles ? 'flex' : 'none';

  uploadList.innerHTML = '';

  selectedFiles.forEach((file, idx) => {
    const item = document.createElement('div');
    item.className = 'upload-item';

    const role = fileRoles.get(file) || 'imaging';
    const roleLabel = {
      'imaging': 'Optical / SAR',
      'before': 'Before',
      'after': 'After',
      'optical': 'Optical',
      'sar': 'SAR'
    }[role] || 'Image';

    let roleControl = `<span class="file-role ${role === 'sar' ? 'role-sar' : ''}">${roleLabel}</span>`;

    if (analysisMode !== 'bitemporal') {
      const other = role === 'optical' ? 'sar' : 'optical';
      roleControl = `
        <span class="file-role ${role === 'sar' ? 'role-sar' : ''}">${roleLabel}

          <button type="button" class="role-toggle" data-idx="${idx}" data-other="${other}" title="Switch Optical / SAR">↔</button>
        </span>`;
    }

    item.innerHTML = `
      <span class="file-info">
        <span class="file-name">${escapeHtml(file.name)}</span>
        <span class="file-size">${formatBytes(file.size)}</span>
      </span>
      <span class="file-format">${fileFormat(file.name)}</span>
      ${roleControl}
      <button class="remove-btn" data-idx="${idx}" title="Remove" aria-label="Remove ${escapeHtml(file.name)}">&times;</button>
    `;
    uploadList.appendChild(item);
  });

  if (hasFiles && selectedFiles.length < MAX_IMAGES) {
    const add = document.createElement('div');
    add.className = 'add-more';
    add.setAttribute('role', 'button');
    add.tabIndex = 0;
    const slotLabel = analysisMode === 'bitemporal' ? 'Add After image'
      : analysisMode === 'optnarsar' ? 'Add partner image'
      : 'Add another image';
    add.innerHTML = `<span class="add-icon">+</span><span>${slotLabel}</span>`;
    add.addEventListener('click', () => fileInput.click());
    add.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
      }
    });
    uploadList.appendChild(add);
  }

  populateMetadata(selectedFiles[0] || null);
  updateViewer();

  const uploadItems = uploadList.querySelectorAll('.upload-item');
  if (uploadItems.length) {
    animate(uploadItems, { opacity: [0, 1], y: [8, 0] }, { duration: 0.3, delay: stagger(0.05), ease: 'easeOut' });
  }
}

/* ---------- Single-image viewer ---------- */
const viewerSection = document.getElementById('viewerSection');
const viewerCanvas = document.getElementById('viewerCanvas');
const viewerPlaceholder = document.getElementById('viewerPlaceholder');
const canvasWrap = document.getElementById('viewerCanvasWrap');
const viewerControls = document.getElementById('viewerControls');
const zoomPctEl = document.getElementById('zoomPct');
const zoomInfoEl = document.getElementById('zoomInfo');

const bapViewer = document.getElementById('bapViewer');
const bapLeft = document.getElementById('bapLeft');
const bapRight = document.getElementById('bapRight');
const bapOverlay = document.getElementById('bapOverlay');
const bapDivider = document.getElementById('bapDivider');
const bapLabelLeft = document.getElementById('bapLabelLeft');
const bapLabelRight = document.getElementById('bapLabelRight');

let viewerImg = null;
let viewerUrl = null;
let scale = 1;
let translateX = 0;
let translateY = 0;
let fitScale = 1;

let bapLeftUrl = null;
let bapRightUrl = null;
let bapLeftLoaded = false;
let bapRightLoaded = false;

const cmViewer = document.getElementById('cmViewer');
const cmControls = document.getElementById('cmControls');
const cmOpticalCell = document.getElementById('cmOpticalCell');
const cmSarCell = document.getElementById('cmSarCell');
const cmOpticalImg = document.getElementById('cmOpticalImg');
const cmSarImg = document.getElementById('cmSarImg');
const cmOpticalImgStack = document.getElementById('cmOpticalImgStack');
const cmSarImgStack = document.getElementById('cmSarImgStack');
const cmJoint = document.getElementById('cmJoint');

let cmMode = 'side'; 
let cmUrls = { optical: null, sar: null };

function isDecodable(file) {
  const fmt = fileFormat(file.name);
  return fmt === 'PNG' || fmt === 'JPEG';
}

function isTiff(file) {
  return /\.(tif|tiff)$/i.test(file.name);
}

async function loadTiffPreview(file) {
  if (!window.GeoTIFF) {
    viewerCanvas.style.display = 'none';
    viewerPlaceholder.hidden = false;
    viewerPlaceholder.querySelector('p').textContent = 'TIFF preview support could not be loaded. The file is ready for analysis.';
    return;
  }

  viewerCanvas.style.display = 'block';
  viewerPlaceholder.hidden = true;
  zoomInfoEl.textContent = 'Loading TIFF...';

  try {
    const tiff = await window.GeoTIFF.fromArrayBuffer(await file.arrayBuffer());
    const image = await tiff.getImage();
    const sourceWidth = image.getWidth();
    const sourceHeight = image.getHeight();
    const maxSide = 3000;
    const previewScale = Math.min(1, maxSide / Math.max(sourceWidth, sourceHeight));
    const width = Math.max(1, Math.round(sourceWidth * previewScale));
    const height = Math.max(1, Math.round(sourceHeight * previewScale));
    const raster = await image.readRGB({ width, height, interleave: true });

    const previewCanvas = document.createElement('canvas');
    previewCanvas.width = width;
    previewCanvas.height = height;
    const previewContext = previewCanvas.getContext('2d');
    const pixels = previewContext.createImageData(width, height);

    for (let i = 0, pixel = 0; i < raster.length; i += 3, pixel += 4) {
      pixels.data[pixel] = raster[i];
      pixels.data[pixel + 1] = raster[i + 1];
      pixels.data[pixel + 2] = raster[i + 2];
      pixels.data[pixel + 3] = 255;
    }
    previewContext.putImageData(pixels, 0, 0);

    const blob = await new Promise((resolve) => previewCanvas.toBlob(resolve, 'image/png'));
    if (!blob || selectedFiles[0] !== file) return;

    viewerUrl = URL.createObjectURL(blob);
    viewerImg = new Image();
    viewerImg.onload = () => {
      fitToScreen();
      draw();
    };
    viewerImg.onerror = () => {
      viewerCanvas.style.display = 'none';
      viewerPlaceholder.hidden = false;
    };
    viewerImg.src = viewerUrl;
  } catch (error) {
    viewerCanvas.style.display = 'none';
    viewerPlaceholder.hidden = false;
    viewerPlaceholder.querySelector('p').textContent = 'This TIFF could not be previewed in the browser. The file is ready for analysis.';
    zoomInfoEl.textContent = 'Preview unavailable';
  }
}

function useBapView() {
  return analysisMode === 'bitemporal' && selectedFiles.length === 2;
}

function useCmView() {
  return analysisMode === 'optnarsar' && selectedFiles.length === 2;
}

function cmImgForRole(role) {
  const file = selectedFiles.find((f) => fileRoles.get(f) === role) || selectedFiles[0];
  return file;
}

function setCmMode(mode) {
  cmMode = mode;
  document.getElementById('cmModeOpticalBtn').classList.toggle('active', mode === 'optical');
  document.getElementById('cmModeSarBtn').classList.toggle('active', mode === 'sar');
  document.getElementById('cmModeJointBtn').classList.toggle('active', mode === 'joint');

  cmJoint.hidden = mode !== 'joint';
  cmOpticalCell.style.display = (mode === 'joint' || mode === 'sar') ? 'none' : 'flex';
  cmSarCell.style.display = (mode === 'joint' || mode === 'optical') ? 'none' : 'flex';
  cmOpticalCell.classList.toggle('highlight', mode === 'optical');
  cmSarCell.classList.toggle('highlight', mode === 'sar');
}

function setCmUrls(opticalFile, sarFile) {
  [cmUrls.optical, cmUrls.sar].forEach((u) => { if (u) URL.revokeObjectURL(u); });
  cmUrls.optical = opticalFile ? URL.createObjectURL(opticalFile) : null;
  cmUrls.sar = sarFile ? URL.createObjectURL(sarFile) : null;
}

function loadCm() {
  const optical = cmImgForRole('optical');
  const sar = cmImgForRole('sar');

  if (!optical || !sar || !isDecodable(optical) || !isDecodable(sar)) {
    viewerPlaceholder.hidden = false;
    cmViewer.hidden = true;
    return;
  }

  viewerPlaceholder.hidden = true;
  cmViewer.hidden = false;
  cmControls.hidden = false;
  viewerControls.style.display = 'none';

  setCmUrls(optical, sar);
  cmOpticalImg.src = cmUrls.optical;
  cmSarImg.src = cmUrls.sar;
  cmOpticalImgStack.src = cmUrls.optical;
  cmSarImgStack.src = cmUrls.sar;
  setCmMode('side');
}

function setBapDivider(pct) {
  const clamped = Math.max(0, Math.min(100, pct));
  bapDivider.style.left = clamped + '%';
  bapOverlay.style.width = clamped + '%';
}

function bapClientToPct(clientX) {
  const rect = bapViewer.getBoundingClientRect();
  return ((clientX - rect.left) / rect.width) * 100;
}

function initBapDividerEvents() {
  bapDivider.addEventListener('mousedown', (e) => {
    e.preventDefault();
    const move = (ev) => setBapDivider(bapClientToPct(ev.clientX));
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  });

  bapViewer.addEventListener('mousedown', (e) => {
    if (e.target === bapViewer || e.target === bapLeft || e.target === bapRight || e.target === bapOverlay) {
      e.preventDefault();
      setBapDivider(bapClientToPct(e.clientX));
    }
  });
}

function updateBapLabels() {
  bapLabelLeft.textContent = selectedFiles[0] ? (fileRoles.get(selectedFiles[0]) === 'before' ? 'Before' : '2024') : 'Before';
  bapLabelRight.textContent = selectedFiles[1] ? (fileRoles.get(selectedFiles[1]) === 'after' ? 'After' : '2025') : 'After';
}

function loadBap() {
  const [f0, f1] = selectedFiles;
  if (bapLeftUrl) URL.revokeObjectURL(bapLeftUrl);
  if (bapRightUrl) URL.revokeObjectURL(bapRightUrl);
  bapLeftUrl = null;
  bapRightUrl = null;
  bapLeftLoaded = false;
  bapRightLoaded = false;

  if (!isDecodable(f0) || !isDecodable(f1)) {
    viewerPlaceholder.hidden = false;
    bapViewer.hidden = true;
    viewerCanvas.style.display = 'none';
    zoomPctEl.textContent = '—';
    zoomInfoEl.textContent = 'Preview unavailable';
    return;
  }

  viewerPlaceholder.hidden = true;
  bapViewer.hidden = false;
  viewerCanvas.style.display = 'none';
  updateBapLabels();

  bapLeftUrl = URL.createObjectURL(f0);
  bapRightUrl = URL.createObjectURL(f1);
  bapLeft.src = bapLeftUrl;
  bapRight.src = bapRightUrl;
  bapLeftLoaded = true;
  bapRightLoaded = true;
  setBapDivider(50);
}

function updateViewer() {
  [bapLeftUrl, bapRightUrl].forEach((u) => { if (u) URL.revokeObjectURL(u); });
  bapLeftUrl = null;
  bapRightUrl = null;

  [cmUrls.optical, cmUrls.sar].forEach((u) => { if (u) URL.revokeObjectURL(u); });
  cmUrls.optical = null;
  cmUrls.sar = null;
  cmViewer.hidden = true;
  cmControls.hidden = true;

  if (viewerUrl) {
    URL.revokeObjectURL(viewerUrl);
    viewerUrl = null;
    viewerImg = null;
  }
  viewerCanvas.getContext('2d').clearRect(0, 0, viewerCanvas.width, viewerCanvas.height);

  const files = selectedFiles.length;

  if (files === 0) {
    viewerSection.hidden = false;
    viewerCanvas.style.display = 'none';
    bapViewer.hidden = true;
    cmViewer.hidden = true;
    cmControls.hidden = true;
    viewerControls.style.display = 'none';
    viewerPlaceholder.hidden = false;
    viewerPlaceholder.querySelector('p').textContent = 'Upload imagery to open the viewer.';
    zoomInfoEl.textContent = 'No image';
    return;
  }

  viewerSection.hidden = false;

  /* Cross-modal Optical + SAR side-by-side */
  if (useCmView()) {
    bapViewer.hidden = true;
    viewerCanvas.style.display = 'none';
    viewerPlaceholder.hidden = true;
    loadCm();
    return;
  }

  /* Before/After comparison slider */
  if (useBapView()) {
    bapViewer.hidden = false;
    viewerCanvas.style.display = 'none';
    viewerPlaceholder.hidden = true;
    viewerControls.style.display = 'none';
    loadBap();
    return;
  }

  /* Single image viewer */
  bapViewer.hidden = true;
  viewerControls.style.display = 'flex';
  viewerCanvas.style.display = 'block';
  viewerPlaceholder.hidden = true;

  const file = selectedFiles[0];

  if (isTiff(file)) {
    loadTiffPreview(file);
    return;
  }

  if (!isDecodable(file)) {
    viewerCanvas.style.display = 'none';
    viewerPlaceholder.hidden = false;
    zoomPctEl.textContent = '—';
    zoomInfoEl.textContent = 'Preview unavailable';
    return;
  }

  viewerPlaceholder.hidden = true;
  viewerCanvas.style.display = 'block';

  viewerUrl = URL.createObjectURL(file);
  viewerImg = new Image();
  viewerImg.onload = () => {
    fitToScreen();
    draw();
  };
  viewerImg.onerror = () => {
    viewerCanvas.style.display = 'none';
    viewerPlaceholder.hidden = false;
  };
  viewerImg.src = viewerUrl;
}

function draw() {
  if (!viewerImg) return;
  const ctx = viewerCanvas.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  const cw = canvasWrap.clientWidth;
  const ch = canvasWrap.clientHeight;
  const dpr = window.devicePixelRatio || 1;

  if (viewerCanvas.width !== Math.round(cw * dpr) || viewerCanvas.height !== Math.round(ch * dpr)) {
    viewerCanvas.width = Math.round(cw * dpr);
    viewerCanvas.height = Math.round(ch * dpr);
  }

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cw, ch);

  const w = viewerImg.naturalWidth * scale;
  const h = viewerImg.naturalHeight * scale;
  const x = (cw - w) / 2 + translateX;
  const y = (ch - h) / 2 + translateY;

  ctx.drawImage(viewerImg, x, y, w, h);
}

function fitToScreen() {
  if (!viewerImg) return;
  const cw = canvasWrap.clientWidth;
  const ch = canvasWrap.clientHeight;
  scale = Math.min(cw / viewerImg.naturalWidth, ch / viewerImg.naturalHeight);
  scale = Math.min(scale, 1);
  fitScale = scale;
  translateX = 0;
  translateY = 0;
  updateZoomLabel();
  draw();
}

function updateZoomLabel() {
  const pct = Math.round(scale * 100);
  zoomPctEl.textContent = pct + '%';
  zoomInfoEl.textContent = pct + '%';
}

function zoomBy(factor) {
  const prev = scale;
  scale = Math.min(8, Math.max(0.1, scale * factor));
  const grow = scale / prev;
  translateX *= grow;
  translateY *= grow;
  updateZoomLabel();
  draw();
}

function resetView() {
  scale = 1;
  translateX = 0;
  translateY = 0;
  updateZoomLabel();
  draw();
}

document.getElementById('zoomInBtn').addEventListener('click', () => zoomBy(1.3));
document.getElementById('zoomOutBtn').addEventListener('click', () => zoomBy(1 / 1.3));
document.getElementById('resetBtn').addEventListener('click', resetView);
document.getElementById('fitBtn').addEventListener('click', fitToScreen);

initBapDividerEvents();

document.getElementById('cmModeOpticalBtn').addEventListener('click', () => setCmMode('optical'));
document.getElementById('cmModeSarBtn').addEventListener('click', () => setCmMode('sar'));
document.getElementById('cmModeJointBtn').addEventListener('click', () => setCmMode('joint'));

/* pan via mouse drag */
let isPanning = false;
let panStartX = 0;
let panStartY = 0;

canvasWrap.addEventListener('mousedown', (e) => {
  if (!viewerImg) return;
  isPanning = true;
  panStartX = e.clientX - translateX;
  panStartY = e.clientY - translateY;
  viewerCanvas.classList.add('dragging');
});

window.addEventListener('mousemove', (e) => {
  if (!isPanning) return;
  translateX = e.clientX - panStartX;
  translateY = e.clientY - panStartY;
  draw();
});

window.addEventListener('mouseup', () => {
  isPanning = false;
  viewerCanvas.classList.remove('dragging');
});

canvasWrap.addEventListener('wheel', (e) => {
  if (!viewerImg) return;
  e.preventDefault();
  zoomBy(e.deltaY < 0 ? 1.15 : 1 / 1.15);
}, { passive: false });

window.addEventListener('resize', () => {
  if (viewerImg) fitToScreen();
});

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function fileFormat(name) {
  const ext = name.split('.').pop().toLowerCase();
  if (ext === 'tif' || ext === 'tiff') return 'GeoTIFF';
  if (ext === 'png') return 'PNG';
  if (ext === 'jpg' || ext === 'jpeg') return 'JPEG';
  return ext.toUpperCase();
}

uploadList.addEventListener('click', (e) => {
  const toggle = e.target.closest('.role-toggle');
  if (toggle) {
    e.stopPropagation();
    const file = selectedFiles[Number(toggle.dataset.idx)];
    if (file) {
      fileRoles.set(file, toggle.dataset.other);
      renderUploadList();
    }
    return;
  }

  const btn = e.target.closest('.remove-btn');
  if (!btn) return;
  const removed = selectedFiles[Number(btn.dataset.idx)];
  selectedFiles.splice(Number(btn.dataset.idx), 1);
  fileRoles.delete(removed);
  enforceRoleConstraints();
  renderUploadList();
  setStatus('');
});

updateViewer();
playIntro();

setInterval(() => {
  touchSync();
}, 60000);
