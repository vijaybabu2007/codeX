// API Client for LessonFoundry
import { authService } from './services/authService';

const API_BASE = '/api/v1';

function authHeaders(extra = {}) {
  const token = authService.getToken();
  const headers = { ...extra };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function fetchPresets() {
  const res = await fetch(`${API_BASE}/presets`, {
    headers: authHeaders()
  });
  if (!res.ok) throw new Error('Failed to load presets');
  return res.json();
}

export async function uploadSourceText(name, text, documentId = null) {
  const res = await fetch(`${API_BASE}/sources/text${documentId ? `?document_id=${documentId}` : ''}`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ name, text })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to upload source text' }));
    throw new Error(err.detail || 'Source upload failed');
  }
  return res.json();
}

export async function uploadSourceFile(file, name, documentId = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);
  if (documentId) formData.append('document_id', documentId);

  const res = await fetch(`${API_BASE}/sources/file`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to upload file' }));
    throw new Error(err.detail || 'File upload failed');
  }
  return res.json();
}

export async function createContract(contractData) {
  const res = await fetch(`${API_BASE}/contracts`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(contractData)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create contract' }));
    throw new Error(err.detail || 'Contract creation failed');
  }
  return res.json();
}

export async function generateLearningPack(contractId) {
  const res = await fetch(`${API_BASE}/packs/generate`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ contract_id: contractId })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
    throw new Error(err.detail || 'Generation failed');
  }
  return res.json();
}

export async function fetchPackDetails(packId) {
  const res = await fetch(`${API_BASE}/packs/${packId}`, {
    headers: authHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch pack details');
  return res.json();
}

export async function submitAssetDecision(versionId, decisionPayload) {
  const res = await fetch(`${API_BASE}/decisions/asset-versions/${versionId}`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(decisionPayload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Decision submission failed' }));
    throw new Error(err.detail || 'Decision submission failed');
  }
  return res.json();
}

export async function submitQuestionDecision(versionId, decisionPayload) {
  const res = await fetch(`${API_BASE}/decisions/question-versions/${versionId}`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(decisionPayload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Decision submission failed' }));
    throw new Error(err.detail || 'Decision submission failed');
  }
  return res.json();
}

export async function regenerateQuizQuestion(questionId, payload = {}) {
  const res = await fetch(`${API_BASE}/questions/${questionId}/regenerate`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Regeneration failed' }));
    throw new Error(err.detail || 'Question regeneration failed');
  }
  return res.json();
}

export async function editQuizQuestion(questionId, payload) {
  const res = await fetch(`${API_BASE}/questions/${questionId}/edit`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Edit failed' }));
    throw new Error(err.detail || 'Question edit failed');
  }
  return res.json();
}

export async function fetchQuestionDiff(questionId, v1 = null, v2 = null) {
  let url = `${API_BASE}/questions/${questionId}/diff`;
  const params = [];
  if (v1 !== null) params.push(`v1=${v1}`);
  if (v2 !== null) params.push(`v2=${v2}`);
  if (params.length > 0) url += `?${params.join('&')}`;

  const res = await fetch(url, {
    headers: authHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch diff' }));
    throw new Error(err.detail || 'Failed to fetch diff');
  }
  return res.json();
}

export async function fetchStudentPack(packId) {
  const res = await fetch(`${API_BASE}/student/packs/${packId}`, {
    headers: authHeaders()
  });
  if (!res.ok) throw new Error('Failed to load student projection');
  return res.json();
}

export async function submitStudentQuiz(packId, answers) {
  const res = await fetch(`${API_BASE}/student/packs/${packId}/submit-quiz`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ answers })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Quiz submission failed' }));
    throw new Error(err.detail || 'Quiz submission failed');
  }
  return res.json();
}

export async function queryVoiceTutor(payload) {
  const res = await fetch(`${API_BASE}/student/voice/query`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Voice Tutor query failed' }));
    throw new Error(err.detail || 'Voice Tutor query failed');
  }
  return res.json();
}

export async function fetchStudentDashboard() {
  const res = await fetch(`${API_BASE}/student/dashboard`, {
    headers: authHeaders()
  });
  if (!res.ok) throw new Error('Failed to load student dashboard');
  return res.json();
}

export async function fetchStudentMastery(packId) {
  const res = await fetch(`${API_BASE}/student/packs/${packId}/mastery`, {
    headers: authHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load mastery data' }));
    throw new Error(err.detail || 'Failed to load mastery data');
  }
  return res.json();
}

export async function fetchTeacherAnalytics(packId = null) {
  const url = packId && packId !== 'all'
    ? `${API_BASE}/teacher/analytics/overview?pack_id=${encodeURIComponent(packId)}`
    : `${API_BASE}/teacher/analytics/overview`;
  const res = await fetch(url, {
    headers: authHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load teacher analytics' }));
    throw new Error(err.detail || 'Failed to load teacher analytics');
  }
  return res.json();
}

export async function fetchTeacherStudentDetail(studentId, packId = null) {
  const url = packId && packId !== 'all'
    ? `${API_BASE}/teacher/analytics/student/${encodeURIComponent(studentId)}?pack_id=${encodeURIComponent(packId)}`
    : `${API_BASE}/teacher/analytics/student/${encodeURIComponent(studentId)}`;
  const res = await fetch(url, {
    headers: authHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load student diagnostic detail' }));
    throw new Error(err.detail || 'Failed to load student diagnostic detail');
  }
  return res.json();
}


