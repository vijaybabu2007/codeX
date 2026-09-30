import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ValidationBadge from './components/ValidationBadge';
import OverrideModal from './components/OverrideModal';
import RegenerateModal from './components/RegenerateModal';
import QuestionEditModal from './components/QuestionEditModal';
import VersionDiffModal from './components/VersionDiffModal';
import WarningAcknowledgementModal from './components/WarningAcknowledgementModal';
import StudentPortal from './components/StudentPortal';
import AlignmentMatrixView from './components/AlignmentMatrixView';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import { authService } from './services/authService';
import {
  fetchPresets,
  uploadSourceText,
  uploadSourceFile,
  createContract,
  generateLearningPack,
  fetchPackDetails,
  submitAssetDecision,
  submitQuestionDecision,
  regenerateQuizQuestion,
  editQuizQuestion,
  fetchQuestionDiff
} from './api';
import {
  FileText,
  Upload,
  Sparkles,
  BookOpen,
  HelpCircle,
  CheckCircle,
  RotateCcw,
  Edit3,
  GitCompare,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  Plus,
  Trash2,
  Quote,
  Calculator,
  Key,
  Compass,
  FileCheck2,
  Layers,
  History,
  Clock,
  RefreshCw
} from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("LessonFoundry ErrorBoundary caught an error:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-2xl mx-auto py-16 px-4 text-center space-y-4">
          <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-200 shadow-xl">
            <h3 className="text-base font-bold text-white mb-2">Workspace Display Notice</h3>
            <p className="text-xs text-rose-200/90 leading-relaxed font-mono">
              {this.state.error?.message || "An unexpected error occurred while rendering."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              if (this.props.onReset) this.props.onReset();
            }}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg transition cursor-pointer"
          >
            Return to Teacher Studio
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => authService.getCurrentUser());
  const [mode, setMode] = useState(() => ((authService.getCurrentUser()?.role || '').toUpperCase() === 'STUDENT' ? 'student' : 'teacher'));
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [currentPath, setCurrentPath] = useState(() => window.location.pathname || '/');
  const [presets, setPresets] = useState([]);

  // Client-side route synchronization and browser history management
  useEffect(() => {
    const syncRoute = () => {
      const path = window.location.pathname || '/';
      const user = authService.getCurrentUser();
      if (!user) {
        if (path !== '/login' && path !== '/register') {
          window.history.replaceState(null, '', '/login');
          setCurrentPath('/login');
          return;
        }
      } else {
        const isStudent = (user.role || '').toUpperCase() === 'STUDENT';
        if (isStudent) {
          setMode('student');
          setIsPreviewMode(false);
          if (!path.startsWith('/student')) {
            window.history.replaceState(null, '', '/student/dashboard');
            setCurrentPath('/student/dashboard');
            return;
          }
        } else {
          // Teacher role
          if (path === '/student/preview' || path.startsWith('/student')) {
            setIsPreviewMode(true);
            setMode('student');
          } else if (path === '/login' || path === '/register' || path === '/') {
            window.history.replaceState(null, '', '/teacher/dashboard');
            setCurrentPath('/teacher/dashboard');
            setMode('teacher');
            setIsPreviewMode(false);
            return;
          } else {
            setMode('teacher');
            setIsPreviewMode(false);
          }
        }
      }
      setCurrentPath(path);
    };

    syncRoute();
    window.addEventListener('popstate', syncRoute);
    return () => window.removeEventListener('popstate', syncRoute);
  }, []);

  const navigate = (newPath) => {
    window.history.pushState(null, '', newPath);
    setCurrentPath(newPath);
  };

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    const isStudent = (user.role || '').toUpperCase() === 'STUDENT';
    if (isStudent) {
      setMode('student');
      setIsPreviewMode(false);
      navigate('/student/dashboard');
    } else {
      setMode('teacher');
      setIsPreviewMode(false);
      navigate('/teacher/dashboard');
    }
  };

  const handleEnterPreview = () => {
    if ((currentUser?.role || '').toUpperCase() !== 'TEACHER') return;
    setIsPreviewMode(true);
    setMode('student');
    navigate('/student/preview');
  };

  const handleExitPreview = () => {
    setIsPreviewMode(false);
    setMode('teacher');
    navigate('/teacher/dashboard');
  };

  const handleSignOut = async () => {
    await authService.logout();
    setCurrentUser(null);
    setIsPreviewMode(false);
    setMode('teacher');
    window.history.replaceState(null, '', '/login');
    setCurrentPath('/login');
  };
  
  // Source State
  const [sourceName, setSourceName] = useState('Photosynthesis Summary');
  const [sourceText, setSourceText] = useState('');
  const [sourceVersion, setSourceVersion] = useState(null);
  const [uploadingSource, setUploadingSource] = useState(false);

  // Contract State
  const [contractTitle, setContractTitle] = useState('Photosynthesis & Cellular Pathways');
  const [targetGrade, setTargetGrade] = useState('Grade 10');
  const [expectedDifficulty, setExpectedDifficulty] = useState('Medium');
  const [objectives, setObjectives] = useState([
    { code: 'LO-01', description: 'Explain the overall chemical equation and biological purpose of photosynthesis.', bloom_level: 'Understand' },
    { code: 'LO-02', description: 'Compare the inputs, outputs, and locations of light-dependent vs Calvin cycle reactions.', bloom_level: 'Analyze' }
  ]);
  const [contract, setContract] = useState(null);

  // Pack State
  const [pack, setPack] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState(null);

  // Override Modal State
  const [overrideModal, setOverrideModal] = useState({
    isOpen: false,
    itemType: null, // 'asset' | 'question'
    versionId: null,
    itemTitle: '',
    warnings: []
  });

  // Load Presets on Mount
  useEffect(() => {
    fetchPresets()
      .then(data => {
        setPresets(data);
        if (data.length > 0) {
          applyPreset(data[0]);
        }
      })
      .catch(console.error);
  }, []);

  const applyPreset = (preset) => {
    setSourceName(preset.source_name);
    setSourceText(preset.source_text);
    setSourceVersion(null);
    setContractTitle(preset.contract.title);
    setTargetGrade(preset.contract.target_learner_level);
    setExpectedDifficulty(preset.contract.expected_difficulty);
    setObjectives(preset.contract.objectives);
    setContract(null);
    setPack(null);
    setGenError(null);
  };

  // Upload or Ingest Source
  const handleSaveSource = async (overrideName, overrideText) => {
    const textToSave = (overrideText !== undefined ? overrideText : sourceText).trim();
    const nameToSave = (overrideName !== undefined ? overrideName : sourceName).trim() || 'Source Document';
    if (!textToSave) return null;
    setUploadingSource(true);
    setGenError(null);
    try {
      const res = await uploadSourceText(nameToSave, textToSave);
      setSourceVersion(res);
      return res;
    } catch (err) {
      setGenError(err.message);
      return null;
    } finally {
      setUploadingSource(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingSource(true);
    setGenError(null);
    try {
      const res = await uploadSourceFile(file, file.name);
      setSourceVersion(res);
      setSourceName(res.source_document_id || file.name);
      setSourceText(res.cleaned_text);
    } catch (err) {
      setGenError(err.message);
    } finally {
      setUploadingSource(false);
    }
  };

  // Objective Management
  const handleAddObjective = () => {
    const nextIdx = objectives.length + 1;
    setObjectives([
      ...objectives,
      { code: `LO-${nextIdx < 10 ? '0' + nextIdx : nextIdx}`, description: '', bloom_level: 'Understand' }
    ]);
  };

  const handleRemoveObjective = (index) => {
    if (objectives.length <= 2) {
      alert('At least 2 learning objectives are required by the contract.');
      return;
    }
    setObjectives(objectives.filter((_, idx) => idx !== index));
  };

  const handleObjectiveChange = (index, field, value) => {
    const updated = [...objectives];
    updated[index][field] = value;
    setObjectives(updated);
  };

  // Full End-to-End Generation
  const handleGenerate = async () => {
    setGenerating(true);
    setGenError(null);

    try {
      let activeSrcVer = sourceVersion;
      // Auto-snapshot if not snapshotted yet or if text in editor has changed since snapshot
      if (!activeSrcVer || activeSrcVer.cleaned_text?.trim() !== sourceText.trim()) {
        activeSrcVer = await handleSaveSource();
        if (!activeSrcVer) throw new Error('Could not persist source text.');
      }

      const contractPayload = {
        source_version_id: activeSrcVer.id,
        title: contractTitle,
        target_learner_level: targetGrade,
        expected_difficulty: expectedDifficulty,
        objectives: objectives,
        constraints: { length_budget: 'Standard', answer_reveal: 'after_submission' }
      };
      const createdContract = await createContract(contractPayload);
      setContract(createdContract);

      const generatedPack = await generateLearningPack(createdContract.id);
      setPack(generatedPack);

    } catch (err) {
      console.error(err);
      setGenError(err.message || 'Generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  // Review Actions
  const handleAssetAction = async (versionId, action) => {
    try {
      await submitAssetDecision(versionId, { action, acknowledged_warning_ids: [] });
      const updated = await fetchPackDetails(pack.pack_id);
      setPack(updated);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleQuestionAction = async (versionId, action) => {
    try {
      await submitQuestionDecision(versionId, { action, acknowledged_warning_ids: [] });
      const updated = await fetchPackDetails(pack.pack_id);
      setPack(updated);
    } catch (err) {
      alert(err.message);
    }
  };

  const triggerOverride = (itemType, versionId, itemTitle, warnings) => {
    setOverrideModal({
      isOpen: true,
      itemType,
      versionId,
      itemTitle,
      warnings
    });
  };

  const confirmOverride = async (notes, warningIds) => {
    try {
      if (overrideModal.itemType === 'asset') {
        await submitAssetDecision(overrideModal.versionId, {
          action: 'OVERRIDE',
          acknowledged_warning_ids: warningIds,
          teacher_notes: notes
        });
      } else {
        await submitQuestionDecision(overrideModal.versionId, {
          action: 'OVERRIDE',
          acknowledged_warning_ids: warningIds,
          teacher_notes: notes
        });
      }
      setOverrideModal(prev => ({ ...prev, isOpen: false }));
      const updated = await fetchPackDetails(pack.pack_id);
      setPack(updated);
    } catch (err) {
      alert(err.message);
    }
  };

  // State for inspecting specific versions of questions
  const [selectedVersionByQuestion, setSelectedVersionByQuestion] = useState({});

  // State for surgical question regeneration modal
  const [regenModal, setRegenModal] = useState({
    isOpen: false,
    questionId: '',
    ordinal: 0,
    currentText: '',
    currentVersionNumber: 1,
    isSubmitting: false,
    error: null
  });

  const handleOpenRegenModal = (q, ordinal) => {
    setRegenModal({
      isOpen: true,
      questionId: q.question_id,
      ordinal,
      currentText: q.question_text,
      currentVersionNumber: q.version_number,
      isSubmitting: false,
      error: null
    });
  };

  const handleConfirmRegenerate = async (notes, reason) => {
    if (!regenModal.questionId) return;
    setRegenModal(prev => ({ ...prev, isSubmitting: true, error: null }));
    try {
      const res = await regenerateQuizQuestion(regenModal.questionId, {
        teacher_notes: notes,
        reason: reason
      });
      if (res.pack) {
        setPack(res.pack);
      } else {
        const refreshed = await fetchPackDetails(pack.pack_id);
        setPack(refreshed);
      }
      if (res.active_version_id) {
        setSelectedVersionByQuestion(prev => ({
          ...prev,
          [regenModal.questionId]: res.active_version_id
        }));
      }
      setRegenModal({
        isOpen: false,
        questionId: '',
        ordinal: 0,
        currentText: '',
        currentVersionNumber: 1,
        isSubmitting: false,
        error: null
      });
    } catch (err) {
      setRegenModal(prev => ({ ...prev, isSubmitting: false, error: err.message }));
    }
  };

  // Edit Question Modal State
  const [editModal, setEditModal] = useState({
    isOpen: false,
    question: null,
    ordinal: 0,
    isSubmitting: false,
    error: null
  });

  const handleOpenEditModal = (q, ordinal) => {
    setEditModal({
      isOpen: true,
      question: q,
      ordinal,
      isSubmitting: false,
      error: null
    });
  };

  const handleConfirmEdit = async (payload) => {
    if (!editModal.question) return;
    setEditModal(prev => ({ ...prev, isSubmitting: true, error: null }));
    try {
      const res = await editQuizQuestion(editModal.question.question_id, payload);
      if (res.pack) {
        setPack(res.pack);
      } else {
        const refreshed = await fetchPackDetails(pack.pack_id);
        setPack(refreshed);
      }
      if (res.active_version_id) {
        setSelectedVersionByQuestion(prev => ({
          ...prev,
          [editModal.question.question_id]: res.active_version_id
        }));
      }
      setEditModal({
        isOpen: false,
        question: null,
        ordinal: 0,
        isSubmitting: false,
        error: null
      });
    } catch (err) {
      setEditModal(prev => ({ ...prev, isSubmitting: false, error: err.message }));
    }
  };

  // Side-by-Side Version Diff Modal State
  const [diffModal, setDiffModal] = useState({
    isOpen: false,
    question: null,
    ordinal: 0
  });

  const handleOpenDiffModal = (q, ordinal) => {
    setDiffModal({
      isOpen: true,
      question: q,
      ordinal
    });
  };

  // Warning Acknowledgement Modal State
  const [warningModal, setWarningModal] = useState({
    isOpen: false,
    itemType: null, // 'asset' | 'question'
    versionId: null,
    itemTitle: '',
    warnings: [],
    isSubmitting: false
  });

  const requestApprovalWithWarningCheck = (itemType, versionId, itemTitle, validations) => {
    const warnings = (validations || []).filter(v => v.severity === 'WARNING');
    if (warnings.length > 0) {
      setWarningModal({
        isOpen: true,
        itemType,
        versionId,
        itemTitle,
        warnings,
        isSubmitting: false
      });
    } else {
      if (itemType === 'asset') {
        handleAssetAction(versionId, 'APPROVED');
      } else {
        handleQuestionAction(versionId, 'APPROVED');
      }
    }
  };

  const confirmWarningAcknowledgement = async (warningIds, notes) => {
    setWarningModal(prev => ({ ...prev, isSubmitting: true }));
    try {
      if (warningModal.itemType === 'asset') {
        await submitAssetDecision(warningModal.versionId, {
          action: 'APPROVED',
          acknowledged_warning_ids: warningIds,
          teacher_notes: notes || undefined
        });
      } else {
        await submitQuestionDecision(warningModal.versionId, {
          action: 'APPROVED',
          acknowledged_warning_ids: warningIds,
          teacher_notes: notes || undefined
        });
      }
      setWarningModal({
        isOpen: false,
        itemType: null,
        versionId: null,
        itemTitle: '',
        warnings: [],
        isSubmitting: false
      });
      const updated = await fetchPackDetails(pack.pack_id);
      setPack(updated);
    } catch (err) {
      alert(err.message);
      setWarningModal(prev => ({ ...prev, isSubmitting: false }));
    }
  };

  const handleRejectToRevision = async (notes) => {
    setWarningModal(prev => ({ ...prev, isSubmitting: true }));
    try {
      if (warningModal.itemType === 'asset') {
        await submitAssetDecision(warningModal.versionId, {
          action: 'NEEDS_REVISION',
          acknowledged_warning_ids: [],
          teacher_notes: notes || 'Returned for revision from warning review'
        });
      } else {
        await submitQuestionDecision(warningModal.versionId, {
          action: 'NEEDS_REVISION',
          acknowledged_warning_ids: [],
          teacher_notes: notes || 'Returned for revision from warning review'
        });
      }
      setWarningModal({
        isOpen: false,
        itemType: null,
        versionId: null,
        itemTitle: '',
        warnings: [],
        isSubmitting: false
      });
      const updated = await fetchPackDetails(pack.pack_id);
      setPack(updated);
    } catch (err) {
      alert(err.message);
      setWarningModal(prev => ({ ...prev, isSubmitting: false }));
    }
  };

  // Reusable Asset Header & Action Toolbar Component
  const renderAssetActions = (asset, title) => {
    if (!asset) return null;
    const hasCritical = asset.validations && asset.validations.some(v => v.severity === 'CRITICAL');
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#E2E8F0]">
        <div className="flex items-center gap-1.5 text-xs text-[#64748B]">
          <span className="font-semibold text-[#1F2937]">Objectives:</span>
          {(asset.content?.objective_ids || asset.objective_ids || []).map(lo => (
            <span key={lo} className="px-2 py-0.5 rounded-md bg-[#F1F5F9] text-[#123C35] border border-[#CBD5E1] text-[10px] font-mono font-bold">
              {lo}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleAssetAction(asset.version_id, 'NEEDS_REVISION')}
            className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-semibold transition cursor-pointer"
          >
            Needs Revision
          </button>
          {hasCritical ? (
            <button
              onClick={() => triggerOverride('asset', asset.version_id, title, asset.validations)}
              className="flex items-center gap-1 px-3.5 py-1.5 rounded-xl bg-rose-700 hover:bg-rose-800 text-white text-xs font-bold transition shadow-sm cursor-pointer"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              Override Critical
            </button>
          ) : (
            <button
              onClick={() => requestApprovalWithWarningCheck('asset', asset.version_id, title, asset.validations)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-bold transition shadow-sm cursor-pointer"
            >
              <CheckCircle className="w-3.5 h-3.5 text-[#D4AF37]" />
              Approve Asset
            </button>
          )}
        </div>
      </div>
    );
  };

  if (!currentUser) {
    if (currentPath === '/register') {
      return (
        <RegisterPage
          onRegisterSuccess={handleLoginSuccess}
          onNavigateToLogin={() => navigate('/login')}
        />
      );
    }
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        onNavigateToRegister={() => navigate('/register')}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1F2937] flex flex-col font-sans">
      <Header
        mode={mode}
        currentPackId={pack?.pack_id}
        user={currentUser}
        isPreviewMode={isPreviewMode}
        onEnterPreview={handleEnterPreview}
        onExitPreview={handleExitPreview}
        onSignOut={handleSignOut}
      />

      <ErrorBoundary onReset={handleExitPreview}>
        {mode === 'student' ? (
          <div className="flex-1 flex flex-col">
            {isPreviewMode && (
              <div className="bg-amber-50 border-b border-amber-200 px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs text-amber-900 shadow-xs">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold uppercase tracking-wider text-[10px] border border-amber-300">
                    Student Preview Mode
                  </span>
                  <span className="font-semibold text-[#1F2937]">
                    Previewing verified student-approved projection as Educator ({currentUser?.name || 'Teacher'}).
                  </span>
                  <span className="text-[11px] text-amber-800 hidden lg:inline">
                    (Drafts, internal notes, and regeneration controls are hidden)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleExitPreview}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white hover:bg-amber-100 text-amber-900 font-semibold border border-amber-300 transition cursor-pointer text-xs shadow-xs"
                >
                  <span>✕ Exit Preview & Return to Teacher Studio</span>
                </button>
              </div>
            )}
            <StudentPortal packId={pack?.pack_id} />
          </div>
        ) : (
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
          {/* Preset Command Bar */}
          <div className="premium-card p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2.5 text-[#1F2937] font-medium">
              <div className="p-1.5 rounded-lg bg-[#123C35]/10 text-[#D4AF37] border border-[#D4AF37]/30">
                <Sparkles className="w-4 h-4 text-[#D4AF37]" />
              </div>
              <span className="font-bold text-[#123C35]">Interactive Evaluation Presets:</span>
              <span className="text-[11px] text-[#64748B] hidden sm:inline">(Populate real curricular source material & objectives)</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {presets.map(p => (
                <button
                  key={p.id}
                  onClick={() => applyPreset(p)}
                  className="px-3.5 py-1.5 rounded-xl bg-[#F8FAFC] hover:bg-[#123C35] hover:text-white border border-[#CBD5E1] text-[#123C35] font-semibold transition-all text-xs cursor-pointer shadow-xs"
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {/* Error Banner */}
          {genError && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-start justify-between gap-3 text-sm text-rose-900 shadow-md">
              <div className="flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-rose-950">Pipeline Execution Notice</h4>
                  <p className="mt-0.5 text-xs text-rose-900 leading-relaxed">{genError}</p>
                </div>
              </div>
              <button
                onClick={handleGenerate}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-rose-700 hover:bg-rose-800 text-white font-semibold text-xs shrink-0 transition shadow-sm"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Retry
              </button>
            </div>
          )}

          {/* Step 1 & 2: Ingestion & Contract Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 1. Trusted Source Workspace */}
            <div className="premium-card p-6 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3.5 mb-4">
                  <div className="flex items-center gap-2.5 text-[#123C35] font-bold text-sm">
                    <span className="step-badge">01</span>
                    <FileText className="w-4 h-4 text-[#123C35]" />
                    <span>Trusted Knowledge Boundary</span>
                  </div>
                  <label className="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-[#F8FAFC] text-xs text-[#123C35] font-semibold border border-[#CBD5E1] transition shadow-xs">
                    <Upload className="w-3.5 h-3.5 text-[#D4AF37]" />
                    <span>Upload TXT/PDF</span>
                    <input type="file" accept=".txt,.pdf" onChange={handleFileUpload} className="hidden" />
                  </label>
                </div>

                <div className="space-y-3.5">
                  <div>
                    <label className="block text-xs font-bold text-[#123C35] mb-1.5">
                      Source Document Title
                    </label>
                    <input
                      type="text"
                      value={sourceName}
                      onChange={e => {
                        setSourceName(e.target.value);
                        if (sourceVersion) setSourceVersion(null);
                      }}
                      className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl px-3.5 py-2 text-xs text-[#1F2937] focus:outline-none focus:border-[#123C35] focus:bg-white transition"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-bold text-[#123C35]">
                        Verbatim Source Material
                      </label>
                      <span className="text-[10px] text-[#64748B] font-mono">
                        (DATA, not instruction authority)
                      </span>
                    </div>
                    <textarea
                      value={sourceText}
                      onChange={e => {
                        setSourceText(e.target.value);
                        if (sourceVersion && sourceVersion.cleaned_text?.trim() !== e.target.value.trim()) {
                          setSourceVersion(null);
                        }
                      }}
                      rows={8}
                      placeholder="Paste curriculum textbook passage, academic summary, or facts..."
                      className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl p-3.5 text-xs text-[#1F2937] placeholder-slate-400 focus:outline-none focus:border-[#123C35] focus:bg-white font-mono leading-relaxed transition"
                    />
                  </div>
                </div>
              </div>

              {/* Source Version Meta */}
              <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-xs">
                {sourceVersion ? (
                  <div className="flex items-center gap-2 text-[#64748B] font-mono text-[11px]">
                    <span className="text-emerald-800 font-semibold px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-300">
                      v{sourceVersion.version_number}
                    </span>
                    <span>•</span>
                    <span title={sourceVersion.sha256_hash} className="text-[#1F2937] font-semibold">
                      SHA: {sourceVersion.sha256_hash.substring(0, 10)}...
                    </span>
                    <span>•</span>
                    <span>{sourceVersion.char_count} chars</span>
                  </div>
                ) : (
                  <span className="text-[#64748B] text-[11px] font-mono">Unsnapshotted draft input</span>
                )}
                <button
                  type="button"
                  onClick={handleSaveSource}
                  disabled={uploadingSource || !sourceText.trim()}
                  className="px-3.5 py-1.5 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] disabled:opacity-50 text-white font-semibold text-xs transition cursor-pointer shadow-xs"
                >
                  {uploadingSource ? 'Hashing...' : 'Snapshot Source'}
                </button>
              </div>
            </div>

            {/* 2. Objective Contract */}
            <div className="premium-card p-6 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3.5 mb-4">
                  <div className="flex items-center gap-2.5 text-[#123C35] font-bold text-sm">
                    <span className="step-badge">02</span>
                    <Layers className="w-4 h-4 text-[#123C35]" />
                    <span>Curricular Contract (Constraints)</span>
                  </div>
                  <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#F1F5F9] text-[#123C35] border border-[#CBD5E1] font-mono font-bold">
                    Min 2 Objectives
                  </span>
                </div>

                <div className="space-y-3.5">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="sm:col-span-2">
                      <label className="block text-xs font-bold text-[#123C35] mb-1.5">Contract Title</label>
                      <input
                        type="text"
                        value={contractTitle}
                        onChange={e => setContractTitle(e.target.value)}
                        className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl px-3.5 py-2 text-xs text-[#1F2937] focus:outline-none focus:border-[#123C35] focus:bg-white transition"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-[#123C35] mb-1.5">Target Level</label>
                      <input
                        type="text"
                        value={targetGrade}
                        onChange={e => setTargetGrade(e.target.value)}
                        className="w-full bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl px-3.5 py-2 text-xs text-[#1F2937] focus:outline-none focus:border-[#123C35] focus:bg-white transition"
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-bold text-[#123C35]">Required Learning Objectives</label>
                      <button
                        type="button"
                        onClick={handleAddObjective}
                        className="flex items-center gap-1 text-[11px] text-[#123C35] hover:text-[#0c2a25] font-bold cursor-pointer"
                      >
                        <Plus className="w-3.5 h-3.5 text-[#D4AF37]" />
                        <span>Add Objective</span>
                      </button>
                    </div>

                    <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                      {objectives.map((obj, idx) => (
                        <div key={idx} className="flex items-center gap-2 bg-[#F8FAFC] p-2.5 rounded-xl border border-[#E2E8F0] transition hover:border-[#CBD5E1]">
                          <input
                            type="text"
                            value={obj.code}
                            onChange={e => handleObjectiveChange(idx, 'code', e.target.value)}
                            className="w-16 bg-white border border-[#CBD5E1] rounded-lg px-2 py-1 text-[11px] font-mono text-[#123C35] text-center uppercase font-bold focus:border-[#123C35]"
                          />
                          <input
                            type="text"
                            value={obj.description}
                            onChange={e => handleObjectiveChange(idx, 'description', e.target.value)}
                            placeholder="State verifiable objective..."
                            className="flex-1 bg-transparent border-0 text-xs text-[#1F2937] placeholder-slate-400 focus:outline-none"
                          />
                          <select
                            value={obj.bloom_level}
                            onChange={e => handleObjectiveChange(idx, 'bloom_level', e.target.value)}
                            className="bg-white border border-[#CBD5E1] rounded-lg px-2.5 py-1 text-[11px] text-[#1F2937] font-medium focus:border-[#123C35]"
                          >
                            <option>Remember</option>
                            <option>Understand</option>
                            <option>Apply</option>
                            <option>Analyze</option>
                            <option>Evaluate</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => handleRemoveObjective(idx)}
                            className="text-slate-400 hover:text-rose-600 p-1 transition cursor-pointer"
                            title="Remove Objective"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Generate Trigger Button */}
              <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-end">
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={generating || !sourceText.trim() || objectives.length < 2}
                  className="btn-primary flex items-center gap-2 px-6 py-2.5 text-xs tracking-wide cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                >
                  <Sparkles className="w-4 h-4 text-[#D4AF37]" />
                  <span>{generating ? 'Compiling 7 Connected Assets with AI Engine...' : 'Generate 7-Asset Learning Pack'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Step 3: Generated Learning Pack with Review Controls */}
          {pack && (
            <div className="space-y-8 pt-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-[#E2E8F0] pb-4 gap-3">
                <div className="flex items-center gap-3">
                  <span className="step-badge">03</span>
                  <div>
                    <h2 className="text-xl font-extrabold text-[#123C35] tracking-tight">Connected Learning Pack (7 Assets)</h2>
                    <p className="text-xs text-[#64748B] font-mono">
                      Bound to Source v{pack.source.version_number} ({pack.source.sha256.substring(0, 10)}...) • Provider: Groq / Gemini
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] text-xs font-bold shadow-xs">
                    <CheckCircle className="w-3.5 h-3.5 text-[#059669]" />
                    Adaptive Mastery: Objective Performance Available
                  </span>
                  <button
                    onClick={() => setMode('student')}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-bold transition cursor-pointer shadow-sm"
                  >
                    <span>Preview in Student Mode</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#D4AF37]" />
                  </button>
                </div>
              </div>

              {/* Objective Alignment Matrix View */}
              {pack.alignment_matrix && (
                <AlignmentMatrixView alignmentMatrix={pack.alignment_matrix} objectives={pack.contract?.objectives} />
              )}

              {/* Asset 1: Concept Explanation */}
              {pack.concept_explanation && (
                <div className="premium-card p-6 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/20">
                        <BookOpen className="w-4 h-4" />
                      </div>
                      <h3 className="text-base font-bold text-[#123C35] tracking-tight">1. Concept Explanation: {pack.concept_explanation.title}</h3>
                    </div>
                    <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full font-mono ${
                      pack.concept_explanation.review_status === 'APPROVED' ? 'badge-approved' :
                      pack.concept_explanation.review_status === 'OVERRIDE' ? 'badge-override' :
                      pack.concept_explanation.review_status === 'NEEDS_REVISION' ? 'badge-revision' :
                      'badge-draft'
                    }`}>
                      Status: {pack.concept_explanation.review_status}
                    </span>
                  </div>

                  <div className="text-sm text-[#1F2937] leading-relaxed bg-[#F8FAFC] p-4 rounded-xl border border-[#E2E8F0] whitespace-pre-line font-sans">
                    {pack.concept_explanation.explanation}
                  </div>

                  <div className="bg-[#F8FAFC] p-3.5 rounded-xl border border-[#E2E8F0] text-xs space-y-1.5">
                    <div className="flex items-center gap-1.5 text-[#123C35] font-bold">
                      <Quote className="w-3.5 h-3.5 text-[#D4AF37]" />
                      <span>Source Grounding Evidence:</span>
                    </div>
                    <blockquote className="italic text-[#1F2937] pl-3 border-l-2 border-[#123C35] leading-relaxed">
                      "{pack.concept_explanation.supporting_quote}"
                    </blockquote>
                  </div>

                  <ValidationBadge validations={pack.concept_explanation.validations} />
                  {renderAssetActions(pack.concept_explanation, pack.concept_explanation.title)}
                </div>
              )}

              {/* Asset 2: Worked Example */}
              {pack.worked_example && (
                <div className="premium-card p-6 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/20">
                        <Calculator className="w-4 h-4" />
                      </div>
                      <h3 className="text-base font-bold text-[#123C35] tracking-tight">2. Worked / Guided Example: {pack.worked_example.content.title}</h3>
                    </div>
                    <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full font-mono ${
                      pack.worked_example.review_status === 'APPROVED' ? 'badge-approved' :
                      pack.worked_example.review_status === 'OVERRIDE' ? 'badge-override' :
                      'badge-draft'
                    }`}>
                      Status: {pack.worked_example.review_status}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-3 text-xs">
                    <div>
                      <strong className="text-[#123C35]">Scenario / Context:</strong>
                      <p className="mt-1 text-[#1F2937] leading-relaxed">{pack.worked_example.content.scenario}</p>
                    </div>

                    <div className="pt-2">
                      <strong className="text-[#123C35]">Guided Steps:</strong>
                      <ol className="mt-1.5 space-y-1.5 list-decimal list-inside text-[#1F2937]">
                        {pack.worked_example.content.steps.map((st, i) => (
                          <li key={i} className="leading-relaxed">{st}</li>
                        ))}
                      </ol>
                    </div>

                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs">
                      <strong className="text-emerald-800">Final Answer:</strong>{' '}
                      <span className="text-emerald-950 font-bold">{pack.worked_example.content.final_answer}</span>
                    </div>
                  </div>

                  <div className="bg-[#F8FAFC] p-3 rounded-lg border border-[#E2E8F0] text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-[#123C35] font-bold">
                      <Quote className="w-3.5 h-3.5 text-[#D4AF37]" />
                      <span>Source Grounding Evidence:</span>
                    </div>
                    <blockquote className="italic text-[#1F2937] pl-3 border-l-2 border-[#123C35]">
                      "{pack.worked_example.content.supporting_quote}"
                    </blockquote>
                  </div>

                  <ValidationBadge validations={pack.worked_example.validations} />
                  {renderAssetActions(pack.worked_example, pack.worked_example.content.title)}
                </div>
              )}

              {/* Asset 3: Formative Quiz (3 Questions) */}
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-[#123C35]" />
                    <h3 className="text-lg font-bold text-[#123C35]">3. Formative Practice Quiz (3 Items)</h3>
                  </div>
                  <span className="text-xs text-[#64748B] font-medium">Independent Item Reviews</span>
                </div>

                <div className="space-y-4">
                  {pack.quiz_questions.map((q, idx) => {
                    const viewingVerId = selectedVersionByQuestion[q.question_id];
                    const displayedVer = (q.versions && viewingVerId)
                      ? (q.versions.find(v => v.id === viewingVerId || v.version_id === viewingVerId) || q)
                      : q;
                    const isHistorical = displayedVer.id !== q.version_id && displayedVer.version_id !== q.version_id;

                    return (
                      <div key={q.question_id} className="premium-card p-6 space-y-4">
                        {isHistorical && (
                          <div className="bg-amber-50 border border-amber-300 p-3 rounded-xl flex items-center justify-between text-xs text-amber-900">
                            <span>
                              Viewing historical Version <strong className="font-mono">v{displayedVer.version_number}</strong> (Read-only). Active student version is <strong className="font-mono">v{q.version_number}</strong>.
                            </span>
                            <button
                              type="button"
                              onClick={() => setSelectedVersionByQuestion(prev => ({ ...prev, [q.question_id]: q.version_id }))}
                              className="text-xs bg-amber-100 hover:bg-amber-200 text-amber-900 px-3 py-1 rounded-lg border border-amber-400 font-semibold transition cursor-pointer"
                            >
                              Return to Active (v{q.version_number})
                            </button>
                          </div>
                        )}

                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-3">
                          <div className="flex items-center gap-2.5">
                            <span className="w-7 h-7 rounded-full bg-[#123C35] text-white border border-[#D4AF37] flex items-center justify-center text-xs font-mono font-bold shadow-xs">
                              {idx + 1}
                            </span>
                            <span className="text-sm font-bold text-[#123C35]">{displayedVer.question_text}</span>
                            <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#F1F5F9] text-[#123C35] border border-[#CBD5E1]">
                              v{displayedVer.version_number || q.version_number}
                            </span>
                          </div>
                          <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full font-mono ${
                            displayedVer.review_status === 'APPROVED' ? 'badge-approved' :
                            displayedVer.review_status === 'OVERRIDE' ? 'badge-override' :
                            displayedVer.review_status === 'NEEDS_REVISION' ? 'badge-revision' :
                            'badge-draft'
                          }`}>
                            Status: {displayedVer.review_status}
                          </span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                          {displayedVer.options.map((opt, optIdx) => {
                            const letter = String.fromCharCode(65 + optIdx);
                            const isCorrect = displayedVer.correct_answer.toLowerCase().includes(opt.toLowerCase()) || opt.toLowerCase().includes(displayedVer.correct_answer.toLowerCase());
                            return (
                              <div
                                key={optIdx}
                                className={`p-3 rounded-xl border flex items-center gap-3 transition ${
                                  isCorrect
                                    ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-semibold'
                                    : 'bg-[#F8FAFC] border-[#E2E8F0] text-[#1F2937]'
                                }`}
                              >
                                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                                  isCorrect ? 'bg-[#123C35] text-white' : 'bg-[#E2E8F0] text-[#123C35]'
                                }`}>
                                  {letter}
                                </span>
                                <span>{opt}</span>
                              </div>
                            );
                          })}
                        </div>

                        <div className="bg-[#F8FAFC] p-2.5 rounded-lg border border-[#E2E8F0] text-[11px] text-[#1F2937] space-y-1">
                          <div className="flex items-center gap-1.5 text-[#123C35] font-bold">
                            <Quote className="w-3 h-3 text-[#D4AF37]" />
                            <span>Supporting Quote:</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold">
                              {displayedVer.grounding_status}
                            </span>
                          </div>
                          <p className="italic text-[#1F2937]">"{displayedVer.supporting_quote}"</p>
                        </div>

                        <ValidationBadge validations={displayedVer.validations} />

                        {displayedVer.teacher_notes && (
                          <div className="bg-[#F8FAFC] p-2.5 rounded-lg border border-[#E2E8F0] text-[11px] text-[#64748B]">
                            <strong className="text-[#123C35]">Teacher Regeneration Context:</strong> {displayedVer.teacher_notes}
                          </div>
                        )}

                        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#E2E8F0]">
                          <div className="flex items-center gap-1.5 text-xs text-[#64748B]">
                            <span className="font-semibold text-[#1F2937]">Objectives:</span>
                            {displayedVer.objective_ids.map(lo => (
                              <span key={lo} className="px-2 py-0.5 rounded-md bg-[#F1F5F9] text-[#123C35] border border-[#CBD5E1] text-[10px] font-mono font-bold">
                                {lo}
                              </span>
                            ))}
                          </div>

                          <div className="flex flex-wrap items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleOpenEditModal(q, idx + 1)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white hover:bg-[#F8FAFC] border border-[#CBD5E1] text-[#123C35] text-xs font-semibold transition cursor-pointer shadow-xs"
                              title="Manually correct or refine this question (creates new draft version)"
                            >
                              <Edit3 className="w-3.5 h-3.5 text-[#123C35]" />
                              <span>Edit Question</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => handleOpenRegenModal(q, idx + 1)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-semibold transition shadow-xs cursor-pointer"
                              title="Surgically regenerate this question with live LLM"
                            >
                              <RotateCcw className="w-3.5 h-3.5 text-[#D4AF37]" />
                              <span>Regenerate</span>
                            </button>

                            {q.versions && q.versions.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleOpenDiffModal(q, idx + 1)}
                                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white hover:bg-[#F8FAFC] border border-[#CBD5E1] text-[#123C35] text-xs font-semibold transition cursor-pointer shadow-xs"
                                title="Side-by-side diff comparison between versions"
                              >
                                <GitCompare className="w-3.5 h-3.5 text-[#123C35]" />
                                <span>Compare Diff</span>
                              </button>
                            )}

                            {!isHistorical && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => handleQuestionAction(q.version_id, 'NEEDS_REVISION')}
                                  className="px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-semibold transition cursor-pointer"
                                >
                                  Needs Revision
                                </button>
                                {q.validations.some(v => v.severity === 'CRITICAL') ? (
                                  <button
                                    type="button"
                                    onClick={() => triggerOverride('question', q.version_id, `Quiz Question ${idx + 1}`, q.validations)}
                                    className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-rose-700 hover:bg-rose-800 text-white text-xs font-bold transition shadow-sm cursor-pointer"
                                  >
                                    <ShieldAlert className="w-3.5 h-3.5" />
                                    Override Critical
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    onClick={() => requestApprovalWithWarningCheck('question', q.version_id, `Quiz Question ${idx + 1}`, q.validations)}
                                    className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-[#123C35] hover:bg-[#0c2a25] text-white text-xs font-bold transition shadow-sm cursor-pointer"
                                  >
                                    <CheckCircle className="w-3.5 h-3.5 text-[#D4AF37]" />
                                    Approve Question
                                  </button>
                                )}
                              </>
                            )}
                          </div>
                        </div>

                        {/* Version History Section */}
                        {q.versions && q.versions.length > 0 && (
                          <div className="pt-2 border-t border-[#E2E8F0] space-y-2">
                            <div className="flex items-center justify-between text-xs text-[#64748B]">
                              <span className="font-semibold flex items-center gap-1.5 text-[#123C35]">
                                <History className="w-3.5 h-3.5 text-[#D4AF37]" />
                                Version History ({q.versions.length} version{q.versions.length > 1 ? 's' : ''})
                              </span>
                              <span className="text-[11px] text-[#64748B]">Click any version to inspect</span>
                            </div>
                            <div className="grid grid-cols-1 gap-1.5">
                              {q.versions.map((ver) => {
                                const isCurrentInspected = (displayedVer.id === ver.id || displayedVer.version_id === ver.id);
                                const isPackActive = ver.id === q.version_id || ver.version_id === q.version_id;
                                return (
                                  <button
                                    key={ver.id || ver.version_id}
                                    type="button"
                                    onClick={() => setSelectedVersionByQuestion(prev => ({ ...prev, [q.question_id]: ver.id || ver.version_id }))}
                                    className={`w-full text-left p-2.5 rounded-xl border text-xs flex items-center justify-between transition cursor-pointer ${
                                      isCurrentInspected
                                        ? 'bg-emerald-50 border-emerald-400 text-[#123C35] font-semibold'
                                        : 'bg-[#F8FAFC] border-[#E2E8F0] text-[#1F2937] hover:bg-slate-100'
                                    }`}
                                  >
                                    <div className="flex items-center gap-2 overflow-hidden">
                                      <span className="font-mono font-bold text-[#123C35]">v{ver.version_number}</span>
                                      <span className="truncate max-w-sm text-[#1F2937]">{ver.question_text}</span>
                                      {isPackActive && (
                                        <span className="text-[10px] bg-emerald-100 text-emerald-900 border border-emerald-300 px-1.5 py-0.5 rounded font-bold">
                                          Active
                                        </span>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                      <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                                        ver.review_status === 'APPROVED' ? 'bg-emerald-100 text-emerald-900 border border-emerald-300' :
                                        ver.review_status === 'OVERRIDE' ? 'bg-purple-100 text-purple-900 border border-purple-300' :
                                        'bg-slate-100 text-slate-700'
                                      }`}>
                                        {ver.review_status}
                                      </span>
                                      <span className="text-[10px] text-[#64748B] font-mono">
                                        {ver.created_at ? new Date(ver.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
                                      </span>
                                    </div>
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Asset 4: Dedicated Quiz Answer Key */}
              {pack.quiz_answer_key && (
                <div className="premium-card p-6 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/20">
                        <Key className="w-4 h-4" />
                      </div>
                      <h3 className="text-base font-bold text-[#123C35] tracking-tight">4. Dedicated Quiz Answer Key</h3>
                    </div>
                    <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full font-mono badge-draft">
                      Status: {pack.quiz_answer_key.review_status}
                    </span>
                  </div>

                  <div className="space-y-3">
                    {pack.quiz_answer_key.content.items.map((it, idx) => (
                      <div key={idx} className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] text-xs space-y-1.5">
                        <div className="flex items-center justify-between">
                          <strong className="text-[#123C35] font-mono font-bold">{it.question_id}: Correct Answer → {it.correct_option}</strong>
                          <span className="text-[10px] text-[#64748B] font-mono">{it.objective_ids?.join(', ')}</span>
                        </div>
                        <p className="text-[#1F2937] leading-relaxed"><strong className="text-[#123C35]">Pedagogical Rationale:</strong> {it.rationale}</p>
                      </div>
                    ))}
                  </div>

                  <ValidationBadge validations={pack.quiz_answer_key.validations} />
                  {renderAssetActions(pack.quiz_answer_key, "Quiz Answer Key")}
                </div>
              )}

              {/* Assets 5 & 6: Differentiated Practice */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 5. Easy Practice */}
                {pack.easy_practice && (
                  <div className="premium-card p-6 flex flex-col justify-between space-y-4">
                    <div className="space-y-3.5">
                      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
                        <span className="text-xs font-bold text-[#123C35] uppercase tracking-wider font-mono">
                          5. Easy Practice (Procedural Recall)
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-300 font-mono font-semibold">
                          Bloom: {pack.easy_practice.content.bloom_level}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-[#123C35] tracking-tight">{pack.easy_practice.content.title}</h4>
                      <p className="text-xs text-[#1F2937] leading-relaxed bg-[#F8FAFC] p-3.5 rounded-xl border border-[#E2E8F0]">
                        {pack.easy_practice.content.problem_statement}
                      </p>
                      <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] text-[11px] text-[#1F2937] leading-relaxed">
                        <strong className="text-[#123C35]">Guidance:</strong> {pack.easy_practice.content.solution_guidance}
                      </div>
                      <div className="bg-[#F8FAFC] p-3 rounded-xl border border-[#E2E8F0] text-[11px] text-[#1F2937] italic flex items-start gap-2">
                        <Quote className="w-3.5 h-3.5 text-[#D4AF37] shrink-0 mt-0.5" />
                        <span>"{pack.easy_practice.content.supporting_quote}"</span>
                      </div>
                      <ValidationBadge validations={pack.easy_practice.validations} />
                    </div>
                    {renderAssetActions(pack.easy_practice, pack.easy_practice.content.title)}
                  </div>
                )}

                {/* 6. Advanced Practice */}
                {pack.advanced_practice && (
                  <div className="premium-card p-6 flex flex-col justify-between space-y-4">
                    <div className="space-y-3.5">
                      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
                        <span className="text-xs font-bold text-[#123C35] uppercase tracking-wider font-mono">
                          6. Advanced Practice (Multi-Step Synthesis)
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-50 text-purple-900 border border-purple-300 font-mono font-semibold">
                          Bloom: {pack.advanced_practice.content.bloom_level} ({pack.advanced_practice.content.reasoning_step_count} Steps)
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-[#123C35] tracking-tight">{pack.advanced_practice.content.title}</h4>
                      <p className="text-xs text-[#1F2937] leading-relaxed bg-[#F8FAFC] p-3.5 rounded-xl border border-[#E2E8F0]">
                        {pack.advanced_practice.content.problem_statement}
                      </p>
                      <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] text-[11px] text-[#1F2937] leading-relaxed">
                        <strong className="text-[#123C35]">Guidance:</strong> {pack.advanced_practice.content.solution_guidance}
                      </div>
                      <div className="bg-[#F8FAFC] p-3 rounded-xl border border-[#E2E8F0] text-[11px] text-[#1F2937] italic flex items-start gap-2">
                        <Quote className="w-3.5 h-3.5 text-[#D4AF37] shrink-0 mt-0.5" />
                        <span>"{pack.advanced_practice.content.supporting_quote}"</span>
                      </div>
                      <ValidationBadge validations={pack.advanced_practice.validations} />
                    </div>
                    {renderAssetActions(pack.advanced_practice, pack.advanced_practice.content.title)}
                  </div>
                )}
              </div>

              {/* Asset 7: Concise Revision Sheet */}
              {pack.revision_sheet && (
                <div className="premium-card p-6 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-[#123C35]/10 text-[#123C35] border border-[#123C35]/20">
                        <FileCheck2 className="w-4 h-4" />
                      </div>
                      <h3 className="text-base font-bold text-[#123C35] tracking-tight">7. Concise Revision Sheet: {pack.revision_sheet.content.title}</h3>
                    </div>
                    <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full font-mono badge-draft">
                      Status: {pack.revision_sheet.review_status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
                      <strong className="text-[#123C35]">Core Takeaways:</strong>
                      <ul className="list-disc list-inside space-y-1 text-[#1F2937]">
                        {pack.revision_sheet.content.key_concepts.map((kc, i) => (
                          <li key={i}>{kc}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
                      <strong className="text-[#123C35]">Key Definitions:</strong>
                      <div className="space-y-1 text-[#1F2937]">
                        {pack.revision_sheet.content.definitions.map((def, i) => (
                          <div key={i}>
                            <strong className="text-[#123C35]">{def.term}:</strong> {def.definition}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="bg-[#F8FAFC] p-3 rounded-lg border border-[#E2E8F0] text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-[#123C35] font-bold">
                      <Quote className="w-3.5 h-3.5 text-[#D4AF37]" />
                      <span>Source Grounding Evidence:</span>
                    </div>
                    <blockquote className="italic text-[#1F2937] pl-3 border-l-2 border-[#123C35]">
                      "{pack.revision_sheet.content.supporting_quote}"
                    </blockquote>
                  </div>

                  <ValidationBadge validations={pack.revision_sheet.validations} />
                  {renderAssetActions(pack.revision_sheet, pack.revision_sheet.content.title)}
                </div>
              )}
            </div>
          )}
        </main>
      )}
      </ErrorBoundary>

      {/* Override Modal */}
      <OverrideModal
        isOpen={overrideModal.isOpen}
        onClose={() => setOverrideModal(prev => ({ ...prev, isOpen: false }))}
        onConfirm={confirmOverride}
        itemTitle={overrideModal.itemTitle}
        warnings={overrideModal.warnings}
      />

      {/* Surgical Question Regenerate Modal */}
      <RegenerateModal
        isOpen={regenModal.isOpen}
        onClose={() => setRegenModal(prev => ({ ...prev, isOpen: false, error: null }))}
        onConfirm={handleConfirmRegenerate}
        questionOrdinal={regenModal.ordinal}
        currentQuestionText={regenModal.currentText}
        currentVersionNumber={regenModal.currentVersionNumber}
        isSubmitting={regenModal.isSubmitting}
        error={regenModal.error}
      />

      {/* Manual Question Edit Modal */}
      <QuestionEditModal
        isOpen={editModal.isOpen}
        onClose={() => setEditModal(prev => ({ ...prev, isOpen: false, error: null }))}
        onSave={handleConfirmEdit}
        question={editModal.question}
        ordinal={editModal.ordinal}
        isSubmitting={editModal.isSubmitting}
        error={editModal.error}
      />

      {/* Side-by-Side Version Diff Modal */}
      <VersionDiffModal
        isOpen={diffModal.isOpen}
        onClose={() => setDiffModal(prev => ({ ...prev, isOpen: false }))}
        question={diffModal.question}
        ordinal={diffModal.ordinal}
      />

      {/* Non-Critical Warning Acknowledgement Modal */}
      <WarningAcknowledgementModal
        isOpen={warningModal.isOpen}
        onClose={() => setWarningModal(prev => ({ ...prev, isOpen: false }))}
        onConfirm={confirmWarningAcknowledgement}
        onRejectToRevision={handleRejectToRevision}
        itemTitle={warningModal.itemTitle}
        warnings={warningModal.warnings}
        isSubmitting={warningModal.isSubmitting}
      />
    </div>
  );
}
