const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
let BACKEND_BASE_URL = DEFAULT_BACKEND_URL;

const chatCta = document.getElementById("chat-cta");
const modalBackdrop = document.getElementById("chat-modal-backdrop");
const modalClose = document.getElementById("chat-modal-close");

const stepCollectInfo = document.getElementById("step-collect-info");
const stepVerifyOtp = document.getElementById("step-verify-otp");
const stepChat = document.getElementById("step-chat");

const userInfoForm = document.getElementById("user-info-form");
const infoError = document.getElementById("info-error");
const otpDemo = document.getElementById("otp-demo");
const requestOtpBtn = document.getElementById("request-otp-btn");

const otpForm = document.getElementById("otp-form");
const otpError = document.getElementById("otp-error");
const verifyOtpBtn = document.getElementById("verify-otp-btn");
const BUTTON_LOADER_MIN_MS = 500;

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const emailInput = document.getElementById("email");
const phoneInput = document.getElementById("phone");
const bookSessionCta = document.getElementById("book-session-cta");
const bookingModalBackdrop = document.getElementById("booking-modal-backdrop");
const bookingModalClose = document.getElementById("booking-modal-close");
const bookingStepCollectInfo = document.getElementById("booking-step-collect-info");
const bookingStepVerifyOtp = document.getElementById("booking-step-verify-otp");
const bookingStepCalendar = document.getElementById("booking-step-calendar");
const bookingInfoForm = document.getElementById("booking-info-form");
const bookingOtpForm = document.getElementById("booking-otp-form");
const bookingInfoError = document.getElementById("booking-info-error");
const bookingOtpError = document.getElementById("booking-otp-error");
const bookingOtpDemo = document.getElementById("booking-otp-demo");
const bookingRequestOtpBtn = document.getElementById("booking-request-otp-btn");
const bookingVerifyOtpBtn = document.getElementById("booking-verify-otp-btn");
const bookingNameInput = document.getElementById("booking-name");
const bookingEmailInput = document.getElementById("booking-email");
const bookingOtpInput = document.getElementById("booking-otp");
const bookingCalendarFrame = document.getElementById("booking-calendar-frame");
const bookingCalendarLink = document.getElementById("booking-calendar-link");
const bookingEventForm = document.getElementById("booking-event-form");
const bookingStartAtInput = document.getElementById("booking-start-at");
const bookingDurationInput = document.getElementById("booking-duration");
const bookingNotesInput = document.getElementById("booking-notes");
const bookingCreateEventBtn = document.getElementById("booking-create-event-btn");
const bookingEventError = document.getElementById("booking-event-error");
const bookingEventSuccess = document.getElementById("booking-event-success");
const aboutTextEl = document.getElementById("about-text");
const demoVideoFrameEl = document.getElementById("demo-video-frame");
const contactHeadingEl = document.getElementById("contact-heading");
const contactTextEl = document.getElementById("contact-text");
const contactEmailLink = document.getElementById("contact-email");
const contactWhatsappLink = document.getElementById("contact-whatsapp");
const skillsListEl = document.getElementById("skills-list");
const projectsGridEl = document.getElementById("projects-grid");
const TOUR_COMPLETED_KEY = "site_feature_tour_completed_v1";

let accessToken = null;
let userEmail = "";
let userPhone = "";
let userName = "";
let bookingName = "";
let bookingEmail = "";
const BOOKING_INLINE_ACTIVE = typeof window !== "undefined" && !!window.__openBookingModalFallback;
const BACKEND_BLOCK_HINT =
  "Cannot connect to backend. If you are using Brave, disable Shields for this page and use http://localhost (not https/file://).";
const CONTACT_EMAIL = "aishikdalui@gmail.com";
const CONTACT_PHONE = "+918167278091";
const CONTACT_EMAIL_SUBJECT = "Regarding role opportunity";
const CONTACT_MESSAGE_TEMPLATE =
  "Hi Aishik I am [Your Name] I ping you regarding role: xyz and for [xyz] company.";

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

resolveBackendBaseUrl().then(() => {
  loadPublicContent();
});

setupContactActions();

console.log("[booking-debug] app.js loaded");
console.log("[booking-debug] bookSessionCta exists:", !!bookSessionCta);
console.log("[booking-debug] bookingModalBackdrop exists:", !!bookingModalBackdrop);

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

function setupContactActions() {
  if (contactEmailLink) {
    const emailHref =
      `mailto:${CONTACT_EMAIL}` +
      `?subject=${encodeURIComponent(CONTACT_EMAIL_SUBJECT)}` +
      `&body=${encodeURIComponent(CONTACT_MESSAGE_TEMPLATE)}`;
    contactEmailLink.href = emailHref;
  }

  if (contactWhatsappLink) {
    const phoneDigits = CONTACT_PHONE.replace(/\D/g, "");
    const whatsappHref =
      `https://wa.me/${phoneDigits}?text=${encodeURIComponent(CONTACT_MESSAGE_TEMPLATE)}`;
    contactWhatsappLink.href = whatsappHref;
  }
}

function normalizeYoutubeEmbedUrl(url) {
  const raw = String(url || "").trim();
  if (!raw) return "";

  try {
    const parsed = new URL(raw);
    const host = parsed.hostname.replace(/^www\./, "");

    if (host === "youtu.be") {
      const videoId = parsed.pathname.replace(/\//g, "");
      return videoId ? `https://www.youtube.com/embed/${videoId}` : "";
    }

    if (host === "youtube.com" || host === "m.youtube.com") {
      if (parsed.pathname.startsWith("/embed/")) {
        return raw;
      }

      const videoId = parsed.searchParams.get("v");
      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
      }
    }
  } catch (err) {
    return "";
  }

  return "";
}

async function loadPublicContent() {
  if (!aboutTextEl || !skillsListEl || !projectsGridEl) return;
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/content/public`);
    if (!res.ok) return;
    const data = await res.json();

    if (data.about_me && typeof data.about_me === "string") {
      aboutTextEl.textContent = data.about_me;
    }

    if (contactHeadingEl && data.contact_heading) {
      contactHeadingEl.textContent = data.contact_heading;
    }
    if (demoVideoFrameEl && data.demo_video_url) {
      const embedUrl = normalizeYoutubeEmbedUrl(data.demo_video_url);
      if (embedUrl) {
        demoVideoFrameEl.src = embedUrl;
      }
    }
    if (contactTextEl && data.contact_message) {
      contactTextEl.textContent = data.contact_message;
    }

    if (Array.isArray(data.skills)) {
      skillsListEl.innerHTML = "";
      data.skills.forEach((skillName) => {
        const li = document.createElement("li");
        li.textContent = String(skillName);
        skillsListEl.appendChild(li);
      });
    }

    if (Array.isArray(data.projects)) {
      projectsGridEl.innerHTML = "";
      data.projects.forEach((project) => {
        const hasLink = typeof project.project_link === "string" && project.project_link.trim().length > 0;
        const cardNode = hasLink ? document.createElement("a") : document.createElement("article");
        cardNode.className = hasLink ? "card card-clickable" : "card";
        if (hasLink && cardNode instanceof HTMLAnchorElement) {
          cardNode.href = project.project_link.trim();
          cardNode.target = "_blank";
          cardNode.rel = "noopener noreferrer";
        }

        const title = document.createElement("h3");
        title.textContent = project.title || "Untitled Project";

        const desc = document.createElement("p");
        desc.textContent = project.description || "";

        cardNode.appendChild(title);
        cardNode.appendChild(desc);

        if (project.image_url) {
          const img = document.createElement("img");
          img.src = project.image_url;
          img.alt = project.title || "Project image";
          img.style.marginTop = "0.75rem";
          img.style.width = "100%";
          img.style.borderRadius = "0.65rem";
          img.style.border = "1px solid rgba(148, 163, 184, 0.35)";
          cardNode.appendChild(img);
        }

        projectsGridEl.appendChild(cardNode);
      });
    }
  } catch (err) {
    // Keep default static content if backend content API is unavailable.
  }
}

function createTourUi() {
  const backdrop = document.createElement("div");
  backdrop.className = "tour-backdrop";

  const card = document.createElement("div");
  card.className = "tour-card";
  card.innerHTML = `
    <p class="tour-title" id="tour-title"></p>
    <p class="tour-text" id="tour-text"></p>
    <div class="tour-actions">
      <button type="button" class="tour-btn" id="tour-back-btn">Back</button>
      <button type="button" class="tour-btn" id="tour-next-btn">Next</button>
      <button type="button" class="tour-btn" id="tour-skip-btn">Skip</button>
    </div>
  `;

  document.body.appendChild(backdrop);
  document.body.appendChild(card);

  return {
    backdrop,
    card,
    titleEl: card.querySelector("#tour-title"),
    textEl: card.querySelector("#tour-text"),
    backBtn: card.querySelector("#tour-back-btn"),
    nextBtn: card.querySelector("#tour-next-btn"),
    skipBtn: card.querySelector("#tour-skip-btn"),
  };
}

function startFeatureTour() {
  const steps = [
    {
      selector: "#book-session-spotlight",
      title: "Book Session",
      text: "Use this section to verify email and book a Google Meet session.",
    },
    {
      selector: "#featured-video",
      title: "Website Demo",
      text: "Watch this video for a quick website demo.",
    },
    {
      selector: "#about",
      title: "About Me",
      text: "This section describes background and specialization.",
    },
    {
      selector: "#skills",
      title: "Skills",
      text: "Shows key skills in bubble tags.",
    },
    {
      selector: "#projects",
      title: "Projects",
      text: "Displays project cards with descriptions and links (if available).",
    },
    {
      selector: "#contact",
      title: "Contact",
      text: "Contains contact details/instructions set by admin.",
    },
    {
      selector: "#chat-cta",
      title: "Chat with me",
      text: "Click here to start OTP verification and AI chat.",
    },
  ];

  const ui = createTourUi();
  let index = 0;
  let currentEl = null;

  function clearHighlight() {
    if (currentEl) {
      currentEl.classList.remove("tour-highlight");
      currentEl = null;
    }
  }

  function finishTour() {
    clearHighlight();
    ui.backdrop.remove();
    ui.card.remove();
    localStorage.setItem(TOUR_COMPLETED_KEY, "1");
  }

  function renderStep() {
    clearHighlight();
    const step = steps[index];
    const target = document.querySelector(step.selector);
    ui.titleEl.textContent = `${index + 1}/${steps.length} - ${step.title}`;
    ui.textEl.textContent = step.text;
    ui.backBtn.disabled = index === 0;
    ui.nextBtn.textContent = index === steps.length - 1 ? "Done" : "Next";

    if (target instanceof HTMLElement) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      target.classList.add("tour-highlight");
      currentEl = target;
    }
  }

  ui.backBtn.addEventListener("click", () => {
    if (index > 0) {
      index -= 1;
      renderStep();
    }
  });

  ui.nextBtn.addEventListener("click", () => {
    if (index >= steps.length - 1) {
      finishTour();
      return;
    }
    index += 1;
    renderStep();
  });

  ui.skipBtn.addEventListener("click", finishTour);
  renderStep();
}

function initFirstTimeTour() {
  if (localStorage.getItem(TOUR_COMPLETED_KEY) === "1") {
    return;
  }
  setTimeout(() => {
    startFeatureTour();
  }, 700);
}

if (phoneInput) {
  phoneInput.addEventListener("input", () => {
    const digitsOnly = phoneInput.value.replace(/\D/g, "");
    phoneInput.value = digitsOnly.slice(0, 10);
  });
}

initFirstTimeTour();

function openModal() {
  modalBackdrop.hidden = false;
  modalBackdrop.style.display = "flex";
  stepCollectInfo.hidden = false;
  stepVerifyOtp.hidden = true;
  stepChat.hidden = true;
  infoError.textContent = "";
  otpError.textContent = "";
  otpDemo.textContent = "";
  document.getElementById("otp").value = "";
  userInfoForm.reset();
  clearButtonLoading(requestOtpBtn);
  clearButtonLoading(verifyOtpBtn);
}

function closeModal() {
  modalBackdrop.style.display = "none";
  modalBackdrop.hidden = true;
}

function openBookingModal() {
  console.log("[booking-debug] openBookingModal called");
  if (!bookingModalBackdrop) return;
  bookingModalBackdrop.removeAttribute("hidden");
  bookingModalBackdrop.hidden = false;
  bookingModalBackdrop.style.display = "flex";
  console.log(
    "[booking-debug] modal display state:",
    bookingModalBackdrop.style.display,
    "hidden attr:",
    bookingModalBackdrop.hasAttribute("hidden"),
    "hidden prop:",
    bookingModalBackdrop.hidden
  );
  if (bookingStepCollectInfo) bookingStepCollectInfo.hidden = false;
  if (bookingStepVerifyOtp) bookingStepVerifyOtp.hidden = true;
  if (bookingStepCalendar) bookingStepCalendar.hidden = true;
  if (bookingInfoError) bookingInfoError.textContent = "";
  if (bookingOtpError) bookingOtpError.textContent = "";
  if (bookingEventError) bookingEventError.textContent = "";
  if (bookingEventSuccess) bookingEventSuccess.textContent = "";
  if (bookingOtpDemo) bookingOtpDemo.textContent = "";
  if (bookingOtpInput) bookingOtpInput.value = "";
  if (bookingInfoForm) bookingInfoForm.reset();
  if (bookingRequestOtpBtn) clearButtonLoading(bookingRequestOtpBtn);
  if (bookingVerifyOtpBtn) clearButtonLoading(bookingVerifyOtpBtn);
}

function closeBookingModal() {
  console.log("[booking-debug] closeBookingModal called");
  if (!bookingModalBackdrop) return;
  bookingModalBackdrop.style.display = "none";
  bookingModalBackdrop.setAttribute("hidden", "");
  bookingModalBackdrop.hidden = true;
}

if (chatCta) chatCta.addEventListener("click", openModal);
if (modalClose) modalClose.addEventListener("click", closeModal);
if (!BOOKING_INLINE_ACTIVE && bookSessionCta) {
  bookSessionCta.addEventListener("click", (e) => {
    console.log("[booking-debug] Book Session button clicked", e.target);
    openBookingModal();
  });
}
if (!BOOKING_INLINE_ACTIVE && bookingModalClose) {
  bookingModalClose.addEventListener("click", closeBookingModal);
}

modalBackdrop.addEventListener("click", (e) => {
  if (e.target === modalBackdrop) {
    closeModal();
  }
});

if (!BOOKING_INLINE_ACTIVE && bookingModalBackdrop) {
  bookingModalBackdrop.addEventListener("click", (e) => {
    console.log("[booking-debug] booking backdrop click", e.target);
    if (e.target === bookingModalBackdrop) {
      closeBookingModal();
    }
  });
}

if (!BOOKING_INLINE_ACTIVE) {
  document.addEventListener("click", (e) => {
    const target = e.target;
    if (!(target instanceof Element)) return;
    const trigger = target.closest("#book-session-cta");
    if (trigger) {
      console.log("[booking-debug] delegated click matched #book-session-cta");
      openBookingModal();
    }
  });
}

if (userInfoForm) userInfoForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  infoError.textContent = "";
  const start = Date.now();
  setButtonLoading(requestOtpBtn, "Requesting OTP...");

  const name = document.getElementById("name").value.trim();
  const email = emailInput.value.trim();
  const phone = phoneInput.value.trim();

  if (!name || !email || !phone) {
    infoError.textContent = "Please fill in all fields.";
    clearButtonLoading(requestOtpBtn);
    return;
  }

  if (!email.includes("@")) {
    infoError.textContent = "Please enter a valid email address with @.";
    clearButtonLoading(requestOtpBtn);
    return;
  }

  if (!/^\d{10}$/.test(phone)) {
    infoError.textContent = "Phone number must be exactly 10 digits.";
    clearButtonLoading(requestOtpBtn);
    return;
  }

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/auth/request-otp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email, phone }),
    });

    if (!res.ok) {
      const data = await res.json();
      infoError.textContent = data.detail || "Failed to request OTP.";
      return;
    }

    const data = await res.json();
    userEmail = email;
    userPhone = phone;
    userName = name;

    otpDemo.textContent = data.otp ? `Demo OTP (for local testing): ${data.otp}` : "";
    otpError.textContent = "";
    document.getElementById("otp").value = "";
    stepCollectInfo.hidden = true;
    stepVerifyOtp.hidden = false;
  } catch (err) {
    infoError.textContent = BACKEND_BLOCK_HINT;
  } finally {
    const elapsed = Date.now() - start;
    if (elapsed < BUTTON_LOADER_MIN_MS) {
      await new Promise((resolve) => setTimeout(resolve, BUTTON_LOADER_MIN_MS - elapsed));
    }
    clearButtonLoading(requestOtpBtn);
  }
});

if (otpForm) otpForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  otpError.textContent = "";
  const start = Date.now();
  setButtonLoading(verifyOtpBtn, "Verifying...");

  const otp = document.getElementById("otp").value.trim();
  if (!otp) {
    otpError.textContent = "Please enter the OTP.";
    clearButtonLoading(verifyOtpBtn);
    return;
  }

  try {
    const res = await fetch(
      `${BACKEND_BASE_URL}/auth/verify-otp?name=${encodeURIComponent(userName)}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: userEmail,
          phone: userPhone,
          otp,
        }),
      }
    );

    if (!res.ok) {
      const data = await res.json();
      otpError.textContent = data.detail || "OTP verification failed.";
      return;
    }

    const data = await res.json();
    accessToken = data.access_token;

    stepVerifyOtp.hidden = true;
    stepChat.hidden = false;
    appendMessage("bot", "You're verified! Ask me anything about my experience, skills, or projects.");
  } catch (err) {
    otpError.textContent = BACKEND_BLOCK_HINT;
  } finally {
    const elapsed = Date.now() - start;
    if (elapsed < BUTTON_LOADER_MIN_MS) {
      await new Promise((resolve) => setTimeout(resolve, BUTTON_LOADER_MIN_MS - elapsed));
    }
    clearButtonLoading(verifyOtpBtn);
  }
});

if (!BOOKING_INLINE_ACTIVE && bookingInfoForm) bookingInfoForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  bookingInfoError.textContent = "";
  const start = Date.now();
  setButtonLoading(bookingRequestOtpBtn, "Sending Code...");

  const name = bookingNameInput.value.trim();
  const email = bookingEmailInput.value.trim();

  if (!name || !email) {
    bookingInfoError.textContent = "Please fill in name and email.";
    clearButtonLoading(bookingRequestOtpBtn);
    return;
  }

  if (!email.includes("@")) {
    bookingInfoError.textContent = "Please enter a valid email address with @.";
    clearButtonLoading(bookingRequestOtpBtn);
    return;
  }

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/booking/request-otp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email }),
    });

    if (!res.ok) {
      const data = await res.json();
      bookingInfoError.textContent = data.detail || "Failed to send verification code.";
      return;
    }

    const data = await res.json();
    bookingName = name;
    bookingEmail = email;
    bookingOtpDemo.textContent = data.otp ? `Demo OTP (for local testing): ${data.otp}` : "";
    bookingStepCollectInfo.hidden = true;
    bookingStepVerifyOtp.hidden = false;
    bookingOtpInput.value = "";
  } catch (err) {
    bookingInfoError.textContent = BACKEND_BLOCK_HINT;
  } finally {
    const elapsed = Date.now() - start;
    if (elapsed < BUTTON_LOADER_MIN_MS) {
      await new Promise((resolve) => setTimeout(resolve, BUTTON_LOADER_MIN_MS - elapsed));
    }
    clearButtonLoading(bookingRequestOtpBtn);
  }
});

if (!BOOKING_INLINE_ACTIVE && bookingOtpForm) bookingOtpForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  bookingOtpError.textContent = "";
  const start = Date.now();
  setButtonLoading(bookingVerifyOtpBtn, "Verifying...");

  const otp = bookingOtpInput.value.trim();
  if (!otp) {
    bookingOtpError.textContent = "Please enter the OTP.";
    clearButtonLoading(bookingVerifyOtpBtn);
    return;
  }

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/booking/verify-otp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: bookingName,
        email: bookingEmail,
        otp,
      }),
    });

    if (!res.ok) {
      const data = await res.json();
      bookingOtpError.textContent = data.detail || "OTP verification failed.";
      return;
    }

    const data = await res.json();
    const calendarUrl = (data && data.calendar_url) || "https://calendar.google.com/";
    if (bookingCalendarFrame) {
      bookingCalendarFrame.src = "";
      bookingCalendarFrame.hidden = true;
    }
    bookingCalendarLink.href = calendarUrl;
    bookingCalendarLink.textContent = calendarUrl;

    bookingStepVerifyOtp.hidden = true;
    bookingStepCalendar.hidden = false;
  } catch (err) {
    bookingOtpError.textContent = BACKEND_BLOCK_HINT;
  } finally {
    const elapsed = Date.now() - start;
    if (elapsed < BUTTON_LOADER_MIN_MS) {
      await new Promise((resolve) => setTimeout(resolve, BUTTON_LOADER_MIN_MS - elapsed));
    }
    clearButtonLoading(bookingVerifyOtpBtn);
  }
});

if (!BOOKING_INLINE_ACTIVE && bookingEventForm) bookingEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  bookingEventError.textContent = "";
  bookingEventSuccess.textContent = "";
  const start = Date.now();
  setButtonLoading(bookingCreateEventBtn, "Creating Event...");

  const localDateTime = bookingStartAtInput.value;
  const duration = Number(bookingDurationInput.value);
  const notes = bookingNotesInput.value.trim();

  if (!localDateTime) {
    bookingEventError.textContent = "Please select date and time.";
    clearButtonLoading(bookingCreateEventBtn);
    return;
  }
  if (!duration || duration < 15 || duration > 180) {
    bookingEventError.textContent = "Duration must be between 15 and 180 minutes.";
    clearButtonLoading(bookingCreateEventBtn);
    return;
  }

  try {
    const startAtIso = new Date(localDateTime).toISOString();
    const res = await fetch(`${BACKEND_BASE_URL}/booking/create-meet-event`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: bookingName,
        email: bookingEmail,
        start_at: startAtIso,
        duration_minutes: duration,
        notes,
      }),
    });

    if (!res.ok) {
      const data = await res.json();
      bookingEventError.textContent = data.detail || "Failed to create Google Meet event.";
      return;
    }

    const data = await res.json();
    const meetLink = data.meet_link || "Not available";
    const eventLink = data.event_link || "";
    bookingEventSuccess.textContent = `Meeting created. Meet link: ${meetLink}`;
    if (eventLink) {
      bookingCalendarLink.href = eventLink;
      bookingCalendarLink.textContent = eventLink;
    }
  } catch (err) {
    bookingEventError.textContent = BACKEND_BLOCK_HINT;
  } finally {
    const elapsed = Date.now() - start;
    if (elapsed < BUTTON_LOADER_MIN_MS) {
      await new Promise((resolve) => setTimeout(resolve, BUTTON_LOADER_MIN_MS - elapsed));
    }
    clearButtonLoading(bookingCreateEventBtn);
  }
});

function appendMessage(sender, text) {
  const messageEl = document.createElement("div");
  messageEl.className = `message message-${sender}`;

  const senderEl = document.createElement("div");
  senderEl.className = "sender";
  senderEl.textContent = sender === "user" ? "You" : "Analyst AI";

  const bubbleEl = document.createElement("div");
  bubbleEl.className = "bubble";
  bubbleEl.textContent = text;

  messageEl.appendChild(senderEl);
  messageEl.appendChild(bubbleEl);

  chatWindow.appendChild(messageEl);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

if (chatForm) chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!accessToken) {
    appendMessage("bot", "You need to verify your OTP first.");
    return;
  }

  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage("user", text);
  chatInput.value = "";

  appendMessage("bot", "Thinking...");
  const thinkingBubble = chatWindow.lastChild;

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ message: text }),
    });

    chatWindow.removeChild(thinkingBubble);

    if (res.status === 401) {
      accessToken = null;
      appendMessage("bot", "Session expired or invalid. Please request and verify OTP again.");
      return;
    }

    if (!res.ok) {
      let message = "Sorry, something went wrong while contacting the server.";
      try {
        const data = await res.json();
        message = data.detail || message;
      } catch (err) {
        // Keep fallback message.
      }
      appendMessage("bot", message);
      return;
    }

    const data = await res.json();
    appendMessage("bot", data.reply || "I couldn't generate a response.");
  } catch (err) {
    chatWindow.removeChild(thinkingBubble);
    appendMessage("bot", BACKEND_BLOCK_HINT);
  }
});
