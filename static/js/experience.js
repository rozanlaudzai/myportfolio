(() => {
  const page = document.getElementById("experience-page");
  const config = page.dataset;
  const searchForm = document.getElementById("experience-search-form");
  const searchInput = document.getElementById("experience-search-input");
  const list = document.getElementById("experience-list");
  const states = {
    loading: document.getElementById("experience-loading"),
    error: document.getElementById("experience-error"),
    empty: document.getElementById("experience-empty"),
    list,
  };
  const SEARCH_DEBOUNCE_DELAY = 300;
  const UUID_PLACEHOLDER = "00000000-0000-0000-0000-000000000000";
  let abortController;
  let searchTimer;
  let editingId = null;
  const records = new Map();

  function displayPageSection(activeState) {
    for (const [name, element] of Object.entries(states)) {
      element.classList.toggle("hide", name !== activeState);
    }
    list.setAttribute("aria-busy", String(activeState === "loading"));
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
  }

  function formatDate(value) {
    return new Date(`${value}T00:00:00Z`).toLocaleDateString("en-US", {
      month: "short", year: "numeric", timeZone: "UTC",
    });
  }

  // Escaping attributes does not validate URL schemes.
  function safeLogoUrl(value) {
    if (!value) return "";
    try {
      const url = new URL(value, window.location.href);
      return ["http:", "https:"].includes(url.protocol) ? url.href : "";
    } catch {
      return "";
    }
  }

  function buildExperienceItemElement(item) {
    const experience = item;
    const id = escapeHtml(item.id);
    const title = escapeHtml(experience.title);
    const company = escapeHtml(experience.company_name);
    const logo = safeLogoUrl(experience.company_logo);
    const logoHtml = logo
      ? `<img src="${escapeHtml(logo)}" alt="${company} logo" width="72" height="72" loading="lazy">`
      : "";
    const endHtml = experience.ended_at
      ? `<time datetime="${escapeHtml(experience.ended_at)}">${escapeHtml(formatDate(experience.ended_at))}</time>`
      : "<time>Present</time>";
    const skillsHtml = experience.skills.map((name) => `<li>${escapeHtml(name)}</li>`).join("");
    const editHtml = config.isSuperuser === "true" || config.isEditor === "true"
      ? `<button type="button" data-action="edit" data-id="${id}" class="button button-secondary" aria-label="Edit ${title}">Edit</button>`
      : "";
    const deleteHtml = config.isSuperuser === "true"
      ? `<button type="button" popovertarget="delete-${id}" class="button button-danger">Delete</button><div id="delete-${id}" popover="auto" class="award-form-modal"><div class="award-form-modal__content"><h2>Delete experience?</h2><p>${title}</p><button type="button" popovertarget="delete-${id}" popovertargetaction="hide" class="button button-secondary">Cancel</button><button type="button" data-action="delete" data-id="${id}" class="button button-danger">Confirm delete</button></div></div>`
      : "";
    const starHtml = config.isAuthenticated === "true"
      ? `<button type="button" data-action="star" data-id="${id}" aria-pressed="${Boolean(experience.is_starred)}" class="button button-secondary">${experience.is_starred ? "Unstar" : "Star"} (${Number(experience.star_count)})</button>`
      : `<a href="/login/?next=/experience/" class="button button-secondary">Log in to star (${Number(experience.star_count)})</a>`;
    const element = document.createElement("li");
    element.className = "experience-item";
    element.innerHTML = `
      <span class="experience-number" aria-hidden="true"></span>
      <article class="experience-card" aria-labelledby="role-${id}">
        <div class="experience-card-header">
          <div class="experience-logo experience-logo-large">${logoHtml}</div>
          <div class="experience-details">
            <p class="experience-organization">${company}</p>
            <h3 id="role-${id}">${title}</h3>
          </div>
          <p class="experience-date">
            <time datetime="${escapeHtml(experience.started_at)}">${escapeHtml(formatDate(experience.started_at))}</time>
            &ndash; ${endHtml}
          </p>
        </div>
        <div class="experience-card-body">
          <p class="experience-description">${escapeHtml(experience.description).replace(/\r\n|\r|\n/g, "<br>")}</p>
          <ul class="experience-skills" aria-label="Skills and technologies">${skillsHtml}</ul>
        </div>
        <div class="record-actions">${starHtml}${editHtml}${deleteHtml}</div>
      </article>`;
    return element;
  }

  async function fetchExperiences(searchQuery = "") {
    abortController?.abort();
    const controller = new AbortController();
    abortController = controller;
    displayPageSection("loading");
    const url = new URL(config.endpoint, window.location.origin);
    url.searchParams.set("title", searchQuery);
    try {
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("Failed to load experiences");
      const experiences = await response.json();
      if (controller.signal.aborted) return;
      records.clear();
      experiences.forEach(item => records.set(item.id, item));
      list.replaceChildren(...experiences.map(buildExperienceItemElement));
      states.empty.textContent = searchQuery ? "No experiences found." : "No experience added yet.";
      displayPageSection(experiences.length ? "list" : "empty");
    } catch (error) {
      if (controller.signal.aborted) return;
      displayPageSection("error");
    }
  }

  function searchExperiences() {
    return fetchExperiences(searchInput.value.trim());
  }

  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    // Invalidate old results immediately, including during the debounce delay.
    abortController?.abort();
    searchTimer = setTimeout(searchExperiences, SEARCH_DEBOUNCE_DELAY);
  });
  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    clearTimeout(searchTimer);
    searchExperiences();
  });
  const experienceForm = document.getElementById("experience-form");
  const modal = document.getElementById("add-experience-modal");
  const fields = ["title", "company_name", "company_logo", "description", "started_at", "ended_at", "skills"];

  function getCookie(name) {
    return document.cookie.split(";").map(value => value.trim())
      .find(value => value.startsWith(`${name}=`))?.slice(name.length + 1) || "";
  }

  function errorMessage(data, status) {
    return Object.entries(data).map(([field, messages]) =>
      `${field}: ${Array.isArray(messages) ? messages.join(" ") : messages}`
    ).join(" ") || `Request failed (${status}).`;
  }

  async function write(url, method, data) {
    const response = await fetch(url, {
      method,
      headers: { Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": decodeURIComponent(getCookie("csrftoken")) },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    if (response.status === 204) return null;
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(errorMessage(result, response.status));
    return result;
  }

  document.getElementById("experience-page").addEventListener("click", event => {
    if (event.target.closest('[popovertarget="add-experience-modal"]')) {
      editingId = null;
      experienceForm.reset();
    }
  });

  list.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");
    if (!button || button.disabled) return;
    const { action, id } = button.dataset;
    if (action === "edit") {
      const record = records.get(id);
      editingId = id;
      for (const field of fields) {
        experienceForm.elements[field].value = field === "skills" ? record.skills.join(", ") : record[field] ?? "";
      }
      modal.showPopover();
      return;
    }
    button.disabled = true;
    try {
      const endpoint = (action === "star" ? config.starUrl : config.deleteUrl).replace(UUID_PLACEHOLDER, encodeURIComponent(id));
      await write(endpoint, action === "star" ? "POST" : "DELETE");
      button.closest("[popover]")?.hidePopover();
      showToast("Success", action === "star" ? "Star updated." : "Experience deleted.", "success");
      clearTimeout(searchTimer);
      await searchExperiences();
    } catch (error) {
      showToast("Request failed", error.message, "error");
    } finally {
      button.disabled = false;
    }
  });

  if (experienceForm) {
    experienceForm.addEventListener("submit", async event => {
      event.preventDefault();
      const submitButton = experienceForm.querySelector('button[type="submit"]');
      if (submitButton.disabled) return;
      submitButton.disabled = true;
      try {
        const data = Object.fromEntries(fields.map(field => [field, experienceForm.elements[field].value]));
        data.skills = data.skills.split(",").map(value => value.trim()).filter(Boolean);
        data.ended_at = data.ended_at || null;
        const endpoint = editingId ? config.editUrl.replace(UUID_PLACEHOLDER, encodeURIComponent(editingId)) : config.endpoint;
        await write(endpoint, editingId ? "PATCH" : "POST", data);
        experienceForm.reset();
        modal.hidePopover();
        showToast("Success", "Experience saved.", "success");
        clearTimeout(searchTimer);
        await searchExperiences();
      } catch (error) {
        showToast("Could not save experience", error.message, "error");
      } finally {
        submitButton.disabled = false;
      }
    });
  }
  searchExperiences();
})();
