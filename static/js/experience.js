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
    const experience = item.fields;
    const id = escapeHtml(item.pk);
    const title = escapeHtml(experience.title);
    const company = escapeHtml(experience.company_name);
    const logo = safeLogoUrl(experience.company_logo);
    const logoHtml = logo
      ? `<img src="${escapeHtml(logo)}" alt="${company} logo" width="72" height="72" loading="lazy">`
      : "";
    const endHtml = experience.ended_at
      ? `<time datetime="${escapeHtml(experience.ended_at)}">${escapeHtml(formatDate(experience.ended_at))}</time>`
      : "<time>Present</time>";
    const skillsHtml = experience.skill_names.map((name) => `<li>${escapeHtml(name)}</li>`).join("");
    const editUrl = config.editUrl.replace(UUID_PLACEHOLDER, encodeURIComponent(item.pk));
    const deleteUrl = config.deleteUrl.replace(UUID_PLACEHOLDER, encodeURIComponent(item.pk));
    const editHtml = config.isSuperuser === "true" || config.isEditor === "true"
      ? `<a href="${escapeHtml(editUrl)}" class="button button-secondary" aria-label="Edit ${title}">Edit</a>`
      : "";
    const deleteHtml = config.isSuperuser === "true"
      ? `<a href="${escapeHtml(deleteUrl)}" class="button button-danger" aria-label="Delete ${title}">Delete</a>`
      : "";
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
        <div class="record-actions">${editHtml}${deleteHtml}</div>
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
  searchExperiences();
})();
