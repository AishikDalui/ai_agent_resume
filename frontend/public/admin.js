const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
let BACKEND_BASE_URL = DEFAULT_BACKEND_URL;
const BUTTON_LOADER_MIN_MS = 500;
const ADMIN_TOKEN_KEY = "admin_access_token";
const ADMIN_LOGIN_AT_KEY = "admin_login_at";
const ADMIN_SESSION_MAX_AGE_MS = 60 * 60 * 1000;

const adminAuthTitle = document.getElementById("admin-auth-title");
const adminLoginForm = document.getElementById("admin-login-form");
const adminEmailInput = document.getElementById("admin-email");
const adminPasswordInput = document.getElementById("admin-password");
const adminEmailField = document.getElementById("admin-email-field");
const adminPasswordField = document.getElementById("admin-password-field");
const adminShowPasswordBtn = document.getElementById("admin-show-password-btn");
const adminLoginBtn = document.getElementById("admin-login-btn");
const adminLoginError = document.getElementById("admin-login-error");
const adminLoginSuccess = document.getElementById("admin-login-success");

const resumeUploadSection = document.getElementById("resume-upload-section");
const resumeUploadForm = document.getElementById("resume-upload-form");
const resumeFileInput = document.getElementById("resume-file");
const resumeFilePickBtn = document.getElementById("resume-file-pick-btn");
const resumeFileNameLabel = document.getElementById("resume-file-name");
const resumeFileClearBtn = document.getElementById("resume-file-clear-btn");
const resumeUploadBtn = document.getElementById("resume-upload-btn");
const resumeUploadError = document.getElementById("resume-upload-error");
const resumeUploadSuccess = document.getElementById("resume-upload-success");
const contentEditorSection = document.getElementById("content-editor-section");
const aboutForm = document.getElementById("about-form");
const aboutInput = document.getElementById("about-input");
const aboutSaveBtn = document.getElementById("about-save-btn");
const contactForm = document.getElementById("contact-form");
const contactHeadingInput = document.getElementById("contact-heading-input");
const contactMessageInput = document.getElementById("contact-message-input");
const contactSaveBtn = document.getElementById("contact-save-btn");
const demoVideoForm = document.getElementById("demo-video-form");
const demoVideoInput = document.getElementById("demo-video-input");
const demoVideoSaveBtn = document.getElementById("demo-video-save-btn");
const voiceCallForm = document.getElementById("voice-call-form");
const voiceCallEnabledInput = document.getElementById("voice-call-enabled-input");
const voiceCallFromNumberInput = document.getElementById("voice-call-from-number-input");
const voiceCallSaveBtn = document.getElementById("voice-call-save-btn");
const skillsForm = document.getElementById("skills-form");
const skillsInput = document.getElementById("skills-input");
const skillsSaveBtn = document.getElementById("skills-save-btn");
const projectsEditorWrap = document.getElementById("projects-editor-wrap");
const addProjectBtn = document.getElementById("add-project-btn");
const contentEditorError = document.getElementById("content-editor-error");
const contentEditorSuccess = document.getElementById("content-editor-success");
let hasActiveUploadedResume = false;
let autoLogoutTimer = null;
let adminContentState = null;
const BACKEND_BLOCK_HINT =
  " If you are using Brave, disable Shields for this page and open frontend on http://localhost (not https/file://).";

function getBackendCandidates() {
  const fromStorage = (localStorage.getItem("backend_base_url") || "").trim();
  const sameOriginApi = `${window.location.origin}/api`;
  const browserHost = (window.location.hostname || "").trim();
  const browserProtocol = window.location.protocol === "https:" ? "https:" : "http:";
  const candidates = [
    sameOriginApi,
    fromStorage,
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    browserHost ? `${browserProtocol}//${browserHost}:8000` : "",
    browserHost ? `http://${browserHost}:8000` : "",
  ];
  return [...new Set(candidates.filter(Boolean))];
}

async function resolveBackendBaseUrl() {
  const candidates = getBackendCandidates();
  for (const candidate of candidates) {
    try {
      const res = await fetch(`${candidate}/health`);
      if (res.ok) {
        BACKEND_BASE_URL = candidate;
        localStorage.setItem("backend_base_url", candidate);
        return candidate;
      }
    } catch (err) {
      // Keep trying fallback candidates.
    }
  }

  BACKEND_BASE_URL = candidates[0] || DEFAULT_BACKEND_URL;
  return null;
}

function setButtonLoading(button, loadingText) {
  if (!button.dataset.originalText) {
    button.dataset.originalText = button.textContent;
  }
  button.disabled = true;
  button.classList.add("loading");
  button.textContent = loadingText;
}

function clearButtonLoading(button) {
  button.disabled = false;
  button.classList.remove("loading");
  button.textContent = button.dataset.originalText || button.textContent;
}

function getAdminToken() {
  return sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
}

function setAdminToken(token) {
  sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
  sessionStorage.setItem(ADMIN_LOGIN_AT_KEY, String(Date.now()));
}

function clearAdminSession() {
  sessionStorage.removeItem(ADMIN_TOKEN_KEY);
  sessionStorage.removeItem(ADMIN_LOGIN_AT_KEY);
}

function showUploadPanel() {
  resumeUploadSection.hidden = false;
}

function hideUploadPanel() {
  resumeUploadSection.hidden = true;
}

function showContentEditor() {
  if (contentEditorSection) {
    contentEditorSection.hidden = false;
  }
}

function hideContentEditor() {
  if (contentEditorSection) {
    contentEditorSection.hidden = true;
  }
}

function setAuthUi(loggedIn) {
  adminLoginBtn.textContent = loggedIn ? "Logout" : "Login";
  adminLoginBtn.dataset.mode = loggedIn ? "logout" : "login";
  adminLoginBtn.dataset.originalText = adminLoginBtn.textContent;
  if (adminAuthTitle) {
    adminAuthTitle.textContent = loggedIn ? "Admin Dashboard" : "Admin Login";
  }
  if (adminEmailField) adminEmailField.hidden = loggedIn;
  if (adminPasswordField) adminPasswordField.hidden = loggedIn;
  adminEmailInput.disabled = loggedIn;
  adminPasswordInput.disabled = loggedIn;
  adminShowPasswordBtn.disabled = loggedIn;
  adminEmailInput.required = !loggedIn;
  adminPasswordInput.required = !loggedIn;
  if (loggedIn) {
    showUploadPanel();
    showContentEditor();
  } else {
    hideUploadPanel();
    hideContentEditor();
  }
}

function scheduleAutoLogout() {
  if (autoLogoutTimer) {
    clearTimeout(autoLogoutTimer);
  }
  const loginAtRaw = sessionStorage.getItem(ADMIN_LOGIN_AT_KEY);
  const loginAt = loginAtRaw ? Number(loginAtRaw) : 0;
  if (!loginAt) return;
  const remaining = ADMIN_SESSION_MAX_AGE_MS - (Date.now() - loginAt);
  if (remaining <= 0) {
    performLogout("Session expired. Logged out automatically after 1 hour.");
    return;
  }
  autoLogoutTimer = setTimeout(() => {
    performLogout("Session expired. Logged out automatically after 1 hour.");
  }, remaining);
}

function performLogout(message = "Logged out successfully.") {
  clearAdminSession();
  hasActiveUploadedResume = false;
  clearSelectedFileUi();
  setAuthUi(false);
  adminLoginSuccess.textContent = message;
  adminLoginError.textContent = "";
  adminPasswordInput.type = "password";
  adminShowPasswordBtn.textContent = "Show";
  adminPasswordInput.value = "";
  adminEmailInput.value = "";
}

const existingToken = getAdminToken();
if (existingToken) {
  const loginAtRaw = sessionStorage.getItem(ADMIN_LOGIN_AT_KEY);
  const loginAt = loginAtRaw ? Number(loginAtRaw) : 0;
  if (!loginAt || Date.now() - loginAt > ADMIN_SESSION_MAX_AGE_MS) {
    performLogout("Session expired. Please login again.");
  } else {
    setAuthUi(true);
    adminLoginSuccess.textContent = "Already logged in.";
    scheduleAutoLogout();
    fetchAdminContent();
  }
} else {
  setAuthUi(false);
}

async function checkBackendHealth() {
  const healthyUrl = await resolveBackendBaseUrl();
  if (healthyUrl) {
    adminLoginError.textContent = "";
    return;
  }

  adminLoginError.textContent = `Cannot reach backend at ${BACKEND_BASE_URL}. Start backend server first.${BACKEND_BLOCK_HINT}`;
}

checkBackendHealth();

if (adminShowPasswordBtn && adminPasswordInput) {
  adminShowPasswordBtn.addEventListener("click", () => {
    const showing = adminPasswordInput.type === "text";
    adminPasswordInput.type = showing ? "password" : "text";
    adminShowPasswordBtn.textContent = showing ? "Show" : "Hide";
  });
}

function clearSelectedFileUi() {
  resumeFileInput.value = "";
  resumeFileNameLabel.textContent = "No file selected";
}

function clearContentNotices() {
  contentEditorError.textContent = "";
  contentEditorSuccess.textContent = "";
}

function getAuthHeaders() {
  const token = getAdminToken();
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

function renderProjectsEditor() {
  if (!projectsEditorWrap) return;
  projectsEditorWrap.innerHTML = "";
  const projects = Array.isArray(adminContentState?.projects) ? adminContentState.projects : [];

  projects.forEach((project) => {
    const card = document.createElement("div");
    card.className = "project-editor";
    card.dataset.projectId = String(project.id || "");
    card.dataset.imageFileId = project.image_file_id || "";
    card.dataset.imageUrl = project.image_url || "";

    card.innerHTML = `
      <h3>Project</h3>
      <label>Title<input type="text" class="proj-title" value="${(project.title || "").replace(/"/g, "&quot;")}" /></label>
      <label>Description<textarea class="proj-description" rows="4">${project.description || ""}</textarea></label>
      <label>Project Link<input type="text" class="proj-link" placeholder="https://github.com/..." value="${(project.project_link || "").replace(/"/g, "&quot;")}" /></label>
      <label>Sort Order<input type="number" class="proj-order" min="0" max="100" value="${Number(project.sort_order || 0)}" /></label>
      <img class="project-image-preview" ${project.image_url ? `src="${project.image_url}"` : ""} ${project.image_url ? "" : "hidden"} />
      <div class="project-editor-actions">
        <input type="file" class="proj-image-file" accept="image/*" hidden />
        <button type="button" class="btn-primary proj-upload-btn">Upload Image</button>
        <button type="button" class="btn-primary proj-save-btn">Save Project</button>
        <button type="button" class="btn-primary proj-delete-btn">Delete Project</button>
      </div>
    `;
    projectsEditorWrap.appendChild(card);
  });
}

function fillContentInputs(content) {
  adminContentState = content;
  aboutInput.value = content.about_me || "";
  contactHeadingInput.value = content.contact_heading || "Contact";
  contactMessageInput.value = content.contact_message || "";
  if (demoVideoInput) {
    demoVideoInput.value = content.demo_video_url || "";
  }
  skillsInput.value = Array.isArray(content.skills) ? content.skills.join("\n") : "";
  renderProjectsEditor();
}

async function fetchAdminContent() {
  try {
    clearContentNotices();
    const res = await fetch(`${BACKEND_BASE_URL}/content/public`, {
      headers: {
        Authorization: `Bearer ${getAdminToken()}`,
      },
    });
    if (!res.ok) {
      contentEditorError.textContent = "Failed to load content from backend.";
      return;
    }
    const data = await res.json();
    fillContentInputs(data);
    await fetchVoiceCallSettings();
  } catch (err) {
    contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
  }
}

async function fetchVoiceCallSettings() {
  if (!voiceCallEnabledInput || !voiceCallFromNumberInput) return;
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/admin/settings/voice-call`, {
      headers: {
        Authorization: `Bearer ${getAdminToken()}`,
      },
    });
    const data = await res.json();
    if (!res.ok) {
      contentEditorError.textContent = data.detail || "Failed to load voice call settings.";
      return;
    }
    voiceCallEnabledInput.checked = !!data.auto_call_enabled;
    voiceCallFromNumberInput.value = data.auto_call_from_number || "";
  } catch (err) {
    contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
  }
}

if (resumeFilePickBtn && resumeFileInput) {
  resumeFilePickBtn.addEventListener("click", () => {
    resumeFileInput.click();
  });
}

if (resumeFileInput) {
  resumeFileInput.addEventListener("change", () => {
    const selected = resumeFileInput.files && resumeFileInput.files[0];
    resumeFileNameLabel.textContent = selected ? selected.name : "No file selected";
  });
}

if (resumeFileClearBtn) {
  resumeFileClearBtn.addEventListener("click", async () => {
    resumeUploadError.textContent = "";
    resumeUploadSuccess.textContent = "";

    const selected = resumeFileInput.files && resumeFileInput.files[0];
    if (selected) {
      clearSelectedFileUi();
      return;
    }

    if (!hasActiveUploadedResume) {
      return;
    }

    const token = getAdminToken();
    if (!token) {
      resumeUploadError.textContent = "Session expired. Please login again.";
      return;
    }

    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/remove-local-resume`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      if (!res.ok) {
        resumeUploadError.textContent = data.detail || "Failed to remove local resume.";
        return;
      }
      hasActiveUploadedResume = false;
      clearSelectedFileUi();
      resumeUploadSuccess.textContent = "Active local uploaded resume removed.";
    } catch (err) {
      resumeUploadError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    }
  });
}

if (adminLoginForm) {
  adminLoginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    adminLoginError.textContent = "";
    adminLoginSuccess.textContent = "";

    if (adminLoginBtn.dataset.mode === "logout") {
      performLogout("Logged out successfully.");
      return;
    }

    const email = adminEmailInput.value.trim();
    const password = adminPasswordInput.value.trim();
    if (!email || !password) {
      adminLoginError.textContent = "Please enter email and password.";
      return;
    }

    const start = Date.now();
    setButtonLoading(adminLoginBtn, "Logging in...");

    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        adminLoginError.textContent = data.detail || "Invalid admin credentials.";
        return;
      }

      const token = data.access_token || "";
      if (!token) {
        adminLoginError.textContent = "No token received from server.";
        return;
      }

      setAdminToken(token);
      setAuthUi(true);
      adminLoginSuccess.textContent = "Login successful. Resume upload is now enabled.";
      adminPasswordInput.value = "";
      scheduleAutoLogout();
      fetchAdminContent();
    } catch (err) {
      adminLoginError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      const elapsed = Date.now() - start;
      if (elapsed < BUTTON_LOADER_MIN_MS) {
        await new Promise((resolve) => setTimeout(resolve, BUTTON_LOADER_MIN_MS - elapsed));
      }
      clearButtonLoading(adminLoginBtn);
    }
  });
}

if (resumeUploadForm) {
  resumeUploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    resumeUploadError.textContent = "";
    resumeUploadSuccess.textContent = "";

    const token = getAdminToken();
    if (!token) {
      resumeUploadError.textContent = "Session expired. Please login again.";
      return;
    }

    const file = resumeFileInput.files && resumeFileInput.files[0];
    if (!file) {
      resumeUploadError.textContent = "Please select a PDF file.";
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      resumeUploadError.textContent = "Only PDF files are allowed.";
      return;
    }

    const start = Date.now();
    setButtonLoading(resumeUploadBtn, "Uploading...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/upload-resume`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        resumeUploadError.textContent = data.detail || "Upload failed.";
        return;
      }

      resumeUploadSuccess.textContent = `Resume uploaded successfully. Extracted ${data.extracted_chars} characters.`;
      hasActiveUploadedResume = true;
      clearSelectedFileUi();
    } catch (err) {
      resumeUploadError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      const elapsed = Date.now() - start;
      if (elapsed < BUTTON_LOADER_MIN_MS) {
        await new Promise((resolve) => setTimeout(resolve, BUTTON_LOADER_MIN_MS - elapsed));
      }
      clearButtonLoading(resumeUploadBtn);
    }
  });
}

if (aboutForm) {
  aboutForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearContentNotices();
    setButtonLoading(aboutSaveBtn, "Saving...");
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/content/about`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify({ about_me: aboutInput.value.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to save About.";
        return;
      }
      fillContentInputs(data);
      contentEditorSuccess.textContent = "About updated.";
    } catch (err) {
      contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      clearButtonLoading(aboutSaveBtn);
    }
  });
}

if (contactForm) {
  contactForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearContentNotices();
    setButtonLoading(contactSaveBtn, "Saving...");
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/content/contact`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          contact_heading: contactHeadingInput.value.trim(),
          contact_message: contactMessageInput.value.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to save Contact.";
        return;
      }
      fillContentInputs(data);
      contentEditorSuccess.textContent = "Contact updated.";
    } catch (err) {
      contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      clearButtonLoading(contactSaveBtn);
    }
  });
}

if (skillsForm) {
  skillsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearContentNotices();
    setButtonLoading(skillsSaveBtn, "Saving...");
    const skills = skillsInput.value
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);
    if (skills.length > 10) {
      contentEditorError.textContent = "Maximum 10 skills are allowed.";
      clearButtonLoading(skillsSaveBtn);
      return;
    }
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/content/skills`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify({ skills }),
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to save Skills.";
        return;
      }
      fillContentInputs(data);
      contentEditorSuccess.textContent = "Skills updated.";
    } catch (err) {
      contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      clearButtonLoading(skillsSaveBtn);
    }
  });
}

if (demoVideoForm) {
  demoVideoForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearContentNotices();
    setButtonLoading(demoVideoSaveBtn, "Saving...");
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/content/demo-video`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          demo_video_url: demoVideoInput.value.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to save demo video.";
        return;
      }
      fillContentInputs(data);
      contentEditorSuccess.textContent = "Demo video updated.";
    } catch (err) {
      contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      clearButtonLoading(demoVideoSaveBtn);
    }
  });
}

if (voiceCallForm) {
  voiceCallForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearContentNotices();
    setButtonLoading(voiceCallSaveBtn, "Saving...");
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/settings/voice-call`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          auto_call_enabled: !!voiceCallEnabledInput.checked,
          auto_call_from_number: voiceCallFromNumberInput.value.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to save voice call settings.";
        return;
      }
      voiceCallEnabledInput.checked = !!data.auto_call_enabled;
      voiceCallFromNumberInput.value = data.auto_call_from_number || "";
      contentEditorSuccess.textContent = "Voice call settings updated.";
    } catch (err) {
      contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      clearButtonLoading(voiceCallSaveBtn);
    }
  });
}

if (addProjectBtn) {
  addProjectBtn.addEventListener("click", async () => {
    clearContentNotices();
    const count = Array.isArray(adminContentState?.projects) ? adminContentState.projects.length : 0;
    if (count >= 3) {
      contentEditorError.textContent = "Only up to 3 projects are allowed.";
      return;
    }
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/content/projects`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          title: "New Project",
          description: "Project description",
          image_url: "",
          image_file_id: "",
          project_link: "",
          sort_order: count,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to add project.";
        return;
      }
      fillContentInputs(data);
      contentEditorSuccess.textContent = "Project added.";
    } catch (err) {
      contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    }
  });
}

if (projectsEditorWrap) {
  projectsEditorWrap.addEventListener("click", async (e) => {
    const target = e.target;
    if (!(target instanceof Element)) return;
    const card = target.closest(".project-editor");
    if (!card) return;

    const projectId = Number(card.dataset.projectId || "0");
    const titleInput = card.querySelector(".proj-title");
    const descInput = card.querySelector(".proj-description");
    const orderInput = card.querySelector(".proj-order");
    const linkInput = card.querySelector(".proj-link");
    const fileInput = card.querySelector(".proj-image-file");
    const preview = card.querySelector(".project-image-preview");
    if (
      !(titleInput instanceof HTMLInputElement) ||
      !(descInput instanceof HTMLTextAreaElement) ||
      !(orderInput instanceof HTMLInputElement) ||
      !(linkInput instanceof HTMLInputElement)
    ) {
      return;
    }

    if (target.classList.contains("proj-upload-btn")) {
      if (fileInput instanceof HTMLInputElement) {
        fileInput.click();
      }
      return;
    }

    if (target.classList.contains("proj-delete-btn")) {
      clearContentNotices();
      const res = await fetch(`${BACKEND_BASE_URL}/admin/content/projects/${projectId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${getAdminToken()}`,
        },
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to delete project.";
        return;
      }
      fillContentInputs(data);
      contentEditorSuccess.textContent = "Project deleted.";
      return;
    }

    if (target.classList.contains("proj-save-btn")) {
      clearContentNotices();
      const body = {
        title: titleInput.value.trim(),
        description: descInput.value.trim(),
        image_url: card.dataset.imageUrl || "",
        image_file_id: card.dataset.imageFileId || "",
        project_link: linkInput.value.trim(),
        sort_order: Number(orderInput.value || 0),
      };
      const res = await fetch(`${BACKEND_BASE_URL}/admin/content/projects/${projectId}`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Failed to save project.";
        return;
      }
      fillContentInputs(data);
      contentEditorSuccess.textContent = "Project updated.";
    }
  });

  projectsEditorWrap.addEventListener("change", async (e) => {
    const target = e.target;
    if (!(target instanceof HTMLInputElement) || !target.classList.contains("proj-image-file")) return;
    const card = target.closest(".project-editor");
    if (!card) return;
    const file = target.files && target.files[0];
    if (!file) return;

    clearContentNotices();
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${BACKEND_BASE_URL}/admin/upload-project-image`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${getAdminToken()}`,
        },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        contentEditorError.textContent = data.detail || "Image upload failed.";
        return;
      }
      card.dataset.imageUrl = data.image_url || "";
      card.dataset.imageFileId = data.image_file_id || "";
      const preview = card.querySelector(".project-image-preview");
      if (preview instanceof HTMLImageElement) {
        preview.src = data.image_url || "";
        preview.hidden = !data.image_url;
      }
      contentEditorSuccess.textContent = "Project image uploaded. Click Save Project to apply.";
    } catch (err) {
      contentEditorError.textContent = `Network error. Cannot connect to ${BACKEND_BASE_URL}.${BACKEND_BLOCK_HINT}`;
    } finally {
      target.value = "";
    }
  });
}
