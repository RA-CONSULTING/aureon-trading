(function () {
  "use strict";

  const scriptElement = document.currentScript;
  const siteRoot = new URL(".", scriptElement.src);
  const projectMapLabels = {
    runtime: ["Task input", "Policy gate", "Human approval", "Bounded action"],
    research: ["Research question", "Evidence trail", "Reproduction audit", "Review boundary"],
    provenance: ["Source lineage", "Model output", "Agreement risk", "Validation gate"],
    operator: ["Input queue", "Evidence review", "Human gate", "Draft action"],
    feed: ["Source stream", "Freshness check", "Data boundary", "Review view"],
    market: ["Simulation input", "Integrity check", "Evidence ledger", "Review gate"],
    environment: ["Public source", "Baseline window", "Anomaly signal", "Validation"],
    shield: ["Assumption layer", "Boundary model", "Engineering review", "Claim gate"],
    governance: ["Invariant draft", "Test case", "Review gate", "Revision"],
    memory: ["Source node", "Tagged trace", "Retention rule", "Audit path"],
    energy: ["Hardware baseline", "Workload", "Measurement", "Reproduction"],
    archive: ["Record", "Context", "Preservation", "Reference"]
  };
  const publicGithubChannels = [
    { label: "RA Consulting GitHub", url: "https://github.com/RA-CONSULTING" },
    { label: "LuciferProSun GitHub", url: "https://github.com/luciferprosun" },
    { label: "Website source repository", url: "https://github.com/luciferprosun/RA-Consulting" }
  ];

  function siteUrl(path) {
    return new URL(String(path || "").replace(/^\/+/, ""), siteRoot).href;
  }

  async function loadJson(path) {
    const response = await fetch(siteUrl(path));
    if (!response.ok) {
      throw new Error("DATA_UNAVAILABLE");
    }
    return response.json();
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#039;"
    })[character]);
  }

  function statusClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized.includes("verified") || normalized.includes("public link") || normalized.includes("implementation") || normalized.includes("completed") || normalized.includes("deployed")) return "ok";
    if (normalized.includes("archive")) return "archive";
    if (normalized.includes("verify") || normalized.includes("draft") || normalized.includes("private")) return "warn";
    return "info";
  }

  function badge(value) {
    return `<span class="badge ${statusClass(value)}">${escapeHtml(value)}</span>`;
  }

  function changeState(update) {
    const isComplete = update.completed === true;
    const label = isComplete ? "Implemented" : "Pending verification";
    return `<span class="change-state ${isComplete ? "complete" : "pending"}"><span class="change-dot" aria-hidden="true"></span>${label}</span>`;
  }

  function externalLink(url, label, className = "btn compact") {
    if (!url) return "";
    return `<a class="${className}" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
  }

  function localLink(path, label, className = "btn compact") {
    return `<a class="${className}" href="${escapeHtml(siteUrl(path))}">${escapeHtml(label)}</a>`;
  }

  function sourceGroup(project) {
    const value = `${project.source_status} ${project.verification_status}`.toLowerCase();
    if (value.includes("verified") || value.includes("public code") || value.includes("public research")) return "verified";
    if (value.includes("archive")) return "archive";
    if (value.includes("draft") || value.includes("private")) return "draft";
    return "to-verify";
  }

  function projectRow(project) {
    const sources = [
      externalLink(project.github_url, "GitHub"),
      externalLink(project.zenodo_url, "Zenodo")
    ].filter(Boolean).join("");

    return `
      <tr>
        <td class="project-cell">
          <div class="project-cell-layout">
            <img class="project-thumb" src="${escapeHtml(siteUrl(project.thumbnail_asset))}" alt="" width="72" height="48" loading="lazy" decoding="async">
            <div>
              <span class="registry-id">${escapeHtml(project.registry_id)}</span>
              <strong>${escapeHtml(project.name)}</strong>
              <span class="mini">${escapeHtml(project.type)}</span>
            </div>
          </div>
        </td>
        <td>${escapeHtml(project.category)}</td>
        <td>${badge(project.status)}</td>
        <td class="source-cell">${badge(project.source_status)}<div class="mini">${escapeHtml(project.verification_status)}</div></td>
        <td class="project-summary">${escapeHtml(project.summary)}</td>
        <td>${escapeHtml(project.last_updated)}</td>
        <td><div class="row-actions">${localLink(project.page_url, "Open project", "btn compact primary")}${sources || '<span class="source-empty">No public source</span>'}</div></td>
      </tr>`;
  }

  function populateSelect(select, values, allLabel) {
    if (!select) return;
    const current = select.value;
    select.innerHTML = `<option value="all">${escapeHtml(allLabel)}</option>` + values
      .map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
      .join("");
    if (["all", ...values].includes(current)) select.value = current;
  }

  function setupProjectTable(projects, tableBody) {
    const scope = tableBody.closest("[data-registry]") || document;
    const searchInput = scope.querySelector("[data-search]");
    const categoryFilter = scope.querySelector("[data-category-filter]");
    const statusFilter = scope.querySelector("[data-status-filter]");
    const sourceFilter = scope.querySelector("[data-source-filter]");
    const sortSelect = scope.querySelector("[data-sort-select]");
    const clearButton = scope.querySelector("[data-clear-filters]");
    const resultCount = scope.querySelector("[data-result-count]");
    const limit = Number(tableBody.dataset.limit || 0);
    const state = { key: "name", direction: "asc" };

    populateSelect(categoryFilter, [...new Set(projects.map((project) => project.category))].sort(), "All categories");
    populateSelect(statusFilter, [...new Set(projects.map((project) => project.status))].sort(), "All statuses");

    function updateSortIndicators() {
      scope.querySelectorAll("th[data-sort]").forEach((header) => {
        const active = header.dataset.sort === state.key;
        header.setAttribute("aria-sort", active ? (state.direction === "asc" ? "ascending" : "descending") : "none");
      });
      if (sortSelect) sortSelect.value = `${state.key}:${state.direction}`;
    }

    function render() {
      const query = String(searchInput?.value || "").trim().toLowerCase();
      const category = categoryFilter?.value || "all";
      const status = statusFilter?.value || "all";
      const source = sourceFilter?.value || "all";
      const filtered = projects.filter((project) => {
        const haystack = [
          project.name,
          project.type,
          project.category,
          project.status,
          project.source_status,
          project.summary,
          project.technical_summary,
          project.caution,
          project.next_step
        ].join(" ").toLowerCase();
        return (!query || haystack.includes(query))
          && (category === "all" || project.category === category)
          && (status === "all" || project.status === status)
          && (source === "all" || sourceGroup(project) === source);
      }).sort((left, right) => {
        const result = String(left[state.key] || "").localeCompare(String(right[state.key] || ""), "en", { sensitivity: "base" });
        return state.direction === "asc" ? result : -result;
      });

      const visible = limit ? filtered.slice(0, limit) : filtered;
      tableBody.innerHTML = visible.length
        ? visible.map(projectRow).join("")
        : `<tr><td class="empty-row" colspan="7">No projects match the selected filters.</td></tr>`;
      if (resultCount) {
        resultCount.textContent = `${filtered.length} of ${projects.length} projects`;
      }
      updateSortIndicators();
    }

    [searchInput, categoryFilter, statusFilter, sourceFilter].forEach((control) => {
      if (control) control.addEventListener(control.tagName === "INPUT" ? "input" : "change", render);
    });

    scope.querySelectorAll("th[data-sort] button").forEach((button) => {
      button.addEventListener("click", () => {
        const key = button.closest("th").dataset.sort;
        if (state.key === key) {
          state.direction = state.direction === "asc" ? "desc" : "asc";
        } else {
          state.key = key;
          state.direction = "asc";
        }
        render();
      });
    });

    if (sortSelect) {
      sortSelect.addEventListener("change", () => {
        [state.key, state.direction] = sortSelect.value.split(":");
        render();
      });
    }

    if (clearButton) {
      clearButton.addEventListener("click", () => {
        if (searchInput) searchInput.value = "";
        [categoryFilter, statusFilter, sourceFilter].forEach((control) => {
          if (control) control.value = "all";
        });
        state.key = "name";
        state.direction = "asc";
        render();
      });
    }

    render();
  }

  function renderStats(projects) {
    document.querySelectorAll("[data-project-stats]").forEach((container) => {
      const verified = projects.filter((project) => sourceGroup(project) === "verified").length;
      const review = projects.filter((project) => ["to-verify", "draft"].includes(sourceGroup(project))).length;
      const categories = new Set(projects.map((project) => project.category)).size;
      const stats = [
        [projects.length, "Portfolio entries"],
        [verified, "Verified public-source entries"],
        [review, "Review-bound entries"],
        [categories, "Portfolio categories"]
      ];
      container.innerHTML = stats.map(([value, label]) => `<div class="stat"><strong>${value}</strong><span>${escapeHtml(label)}</span></div>`).join("");
    });
  }

  async function renderEcosystem(projects) {
    const container = document.querySelector("[data-project-graph]");
    if (!container) return;
    try {
      const graph = await loadJson("data/project-graph.json");
      const bySlug = new Map(projects.map((project) => [project.slug, project]));
      const groups = new Map();
      graph.nodes.forEach((node) => {
        if (!groups.has(node.group)) groups.set(node.group, []);
        const project = bySlug.get(node.slug);
        if (project) groups.get(node.group).push(project.name);
      });
      const nodes = [...groups.entries()].map(([group, names]) => `
        <div class="ecosystem-node"><strong>${escapeHtml(group)}</strong><span>${escapeHtml(names.join(" / "))}</span></div>`).join("");
      const relations = graph.edges.map((edge) => {
        const from = bySlug.get(edge.from)?.name || edge.from;
        const to = bySlug.get(edge.to)?.name || edge.to;
        return `<span>${escapeHtml(from)} -> ${escapeHtml(to)}: ${escapeHtml(edge.label)}</span>`;
      }).join("");
      container.innerHTML = `<div class="ecosystem-map">${nodes}</div><div class="relationship-ledger" aria-label="Project relationships">${relations}</div>`;
    } catch (_error) {
      showInlineError(container, "The project relationship map is temporarily unavailable.");
    }
  }

  function renderPublications(records) {
    document.querySelectorAll("[data-publications]").forEach((tableBody) => {
      tableBody.innerHTML = records.map((record) => `
        <tr>
          <td><strong>${escapeHtml(record.project)}</strong></td>
          <td>${escapeHtml(record.artifact)}</td>
          <td>${escapeHtml(record.type)}</td>
          <td>${externalLink(record.github, "GitHub") || '<span class="source-empty">Not listed</span>'}</td>
          <td>${externalLink(record.zenodo, "Zenodo") || '<span class="source-empty">Not listed</span>'}</td>
          <td>${externalLink(record.doi, "DOI") || '<span class="source-empty">Not listed</span>'}</td>
          <td>${badge(record.status)}</td>
          <td>${escapeHtml(record.notes)}</td>
        </tr>`).join("");
    });

    document.querySelectorAll("[data-publications-preview]").forEach((container) => {
      const limit = Number(container.dataset.limit || 3);
      container.innerHTML = records.slice(0, limit).map((record) => `
        <article class="record-item">
          <div>${badge(record.status)}</div>
          <div><h3>${escapeHtml(record.project)}</h3><p>${escapeHtml(record.artifact)}. ${escapeHtml(record.notes)}</p></div>
          <div class="actions">${externalLink(record.github, "GitHub")}${externalLink(record.zenodo, "Zenodo")}${externalLink(record.doi, "DOI")}</div>
        </article>`).join("");
    });
  }

  function renderResearch(data) {
    const profiles = data.profiles || [];
    const nameById = {};
    profiles.forEach((profile) => { nameById[profile.id] = profile.name; });

    document.querySelectorAll("[data-research-profiles]").forEach((container) => {
      container.innerHTML = profiles.map((profile) => `
        <article class="card">
          <div class="card-accent"></div>
          <div class="eyebrow">${escapeHtml(profile.role)}</div>
          <h3>${escapeHtml(profile.name)}</h3>
          <p>${escapeHtml(profile.summary)}</p>
          <div class="github-channel-actions">${(profile.links || []).map((link) => externalLink(link.url, link.label)).join("")}</div>
          ${(profile.collections || []).map((collection) => `<p class="mini">${externalLink(collection.url, collection.label)} &mdash; ${escapeHtml(collection.note)}</p>`).join("")}
        </article>`).join("");
    });

    document.querySelectorAll("[data-research]").forEach((tableBody) => {
      tableBody.innerHTML = (data.papers || []).map((paper) => `
        <tr>
          <td><strong>${escapeHtml(nameById[paper.author] || paper.author)}</strong></td>
          <td>${escapeHtml(paper.title)}</td>
          <td>${escapeHtml(paper.type)}</td>
          <td>${escapeHtml(paper.platform)}</td>
          <td>${externalLink(paper.url, "View")}${externalLink(paper.doi, "DOI")}${(!paper.url && !paper.doi) ? '<span class="source-empty">Not listed</span>' : ""}</td>
        </tr>`).join("");
    });
  }

  function renderUpdates(updates) {
    document.querySelectorAll("[data-updates]").forEach((container) => {
      const limit = Number(container.dataset.limit || updates.length);
      const visibleUpdates = updates.slice(0, limit);

      if (container.dataset.view === "table") {
        container.innerHTML = visibleUpdates.map((update) => `
          <tr data-update-id="${escapeHtml(update.id)}">
            <td><time datetime="${escapeHtml(update.date)}">${escapeHtml(update.date)}</time></td>
            <td>${changeState(update)}</td>
            <td><strong>${escapeHtml(update.title)}</strong><p class="mini">${escapeHtml(update.summary)}</p></td>
            <td>${badge(update.status)}</td>
          </tr>`).join("");
        return;
      }

      container.innerHTML = visibleUpdates.map((update) => `
        <article class="timeline-item">
          <time class="date" datetime="${escapeHtml(update.date)}">${escapeHtml(update.date)}</time>
          <div><div class="badges">${changeState(update)}${badge(update.status)}</div><h3>${escapeHtml(update.title)}</h3><p>${escapeHtml(update.summary)}</p></div>
          <span class="registry-id">PROJECT ENVISION</span>
        </article>`).join("");
    });
  }

  function listItems(items) {
    return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  function sourceButtons(project) {
    return [
      externalLink(project.github_url, "GitHub", "btn"),
      externalLink(project.zenodo_url, "Zenodo", "btn"),
      externalLink(project.secondary_zenodo_url, "Zenodo record 2", "btn"),
      externalLink(project.doi_url, "DOI", "btn")
    ].filter(Boolean).join("") || '<span class="source-empty">No verified public source link is listed.</span>';
  }

  function relatedCards(project, projects) {
    const bySlug = new Map(projects.map((item) => [item.slug, item]));
    return project.related_projects.map((slug) => bySlug.get(slug)).filter(Boolean).map((related) => `
      <article class="related-card">
        <img class="related-card-visual" src="${escapeHtml(siteUrl(related.thumbnail_asset))}" alt="" width="480" height="270" loading="lazy" decoding="async">
        <div><span class="registry-id">${escapeHtml(related.registry_id)} / ${escapeHtml(related.category)}</span><h3>${escapeHtml(related.name)}</h3><p>${escapeHtml(related.summary)}</p></div>
        ${localLink(related.page_url, "Open project", "btn compact")}
      </article>`).join("");
  }

  function supportingVisuals(project) {
    return project.supporting_visuals.map((visual) => `
      <figure class="project-visual">
        <img src="${escapeHtml(siteUrl(visual.src))}" alt="${escapeHtml(visual.alt)}" loading="lazy" decoding="async">
      </figure>`).join("");
  }

  function renderProjectDetail(project, projects) {
    const container = document.querySelector("[data-project-detail]");
    if (!container) return;
    const labels = projectMapLabels[project.visual_mode] || projectMapLabels.runtime;
    const publicBoundary = project.public_safe
      ? "Public profile with the stated evidence and claim boundaries."
      : "Partner or draft concept. Public claims remain restricted pending review.";

    document.title = `${project.name} | Project Envision`;
    const description = document.querySelector('meta[name="description"]');
    if (description) description.content = project.summary;

    container.innerHTML = `
      <section class="project-detail-hero">
        <div class="wrap">
          <a class="breadcrumbs" href="${escapeHtml(siteUrl("projects/"))}">Back to Projects</a>
          <div class="eyebrow">${escapeHtml(project.registry_id)} / ${escapeHtml(project.category)}</div>
          <h1>${escapeHtml(project.name)}</h1>
          <div class="badges">${badge(project.status)}${badge(project.source_status)}</div>
          <p class="lead">${escapeHtml(project.summary)}</p>
          <div class="actions">${sourceButtons(project)}</div>
        </div>
      </section>
      <section class="project-meta-strip" aria-label="Project metadata">
        <div class="project-meta"><span>Project type</span><strong>${escapeHtml(project.type)}</strong></div>
        <div class="project-meta"><span>Status</span><strong>${escapeHtml(project.status)}</strong></div>
        <div class="project-meta"><span>Source status</span><strong>${escapeHtml(project.source_status)}</strong></div>
        <div class="project-meta"><span>Last updated</span><strong>${escapeHtml(project.last_updated)}</strong></div>
      </section>
      <section class="band alt">
        <div class="wrap">
          <div class="project-story">
            <div><div class="eyebrow">Project profile</div><h2>${escapeHtml(project.visual_label)}</h2><p>${escapeHtml(project.technical_summary)}</p><p><strong>Verification status:</strong> ${escapeHtml(project.verification_status)}</p></div>
            <div class="project-system-map" aria-label="Conceptual project map">
              ${labels.map((label) => `<div class="map-node">${escapeHtml(label)}</div>`).join("")}
              <p class="map-caption">Concept map, not operational proof.</p>
            </div>
          </div>
          <div class="project-media-rail" aria-label="Supporting project visuals">${supportingVisuals(project)}</div>
        </div>
      </section>
      <section class="band">
        <div class="wrap evidence-columns">
          <article class="evidence-panel exists"><div class="eyebrow">Current state</div><h2>What exists now</h2><ul>${listItems(project.exists_now)}</ul></article>
          <article class="evidence-panel verify"><div class="eyebrow">Evidence boundary</div><h2>What is TO VERIFY</h2><ul>${listItems(project.to_verify)}</ul></article>
        </div>
      </section>
      <section class="band boundary-band">
        <div class="wrap grid cols-2">
          <div><div class="eyebrow">Public claim boundary</div><h2>${escapeHtml(publicBoundary)}</h2></div>
          <div class="panel"><h3>Required caution</h3><p>${escapeHtml(project.caution)}</p></div>
        </div>
      </section>
      <section class="band alt"><div class="wrap next-step"><strong>Next step</strong><p>${escapeHtml(project.next_step)}</p></div></section>
      <section class="band"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Portfolio links</div><h2>Related projects</h2></div><p>Relationships indicate shared questions or workflow context, not validation transfer between projects.</p></div><div class="related-grid">${relatedCards(project, projects)}</div></div></section>
      <section class="band warm"><div class="wrap"><div class="eyebrow">Sources</div><h2>Open project links</h2><p class="lead">Public links are listed only where the registry provides them. Missing links remain visibly unverified.</p><div class="actions">${sourceButtons(project)}${localLink("publications/", "Public records", "btn")}</div></div></section>`;

    const hero = container.querySelector(".project-detail-hero");
    hero.style.setProperty("--project-image", `url("${siteUrl(project.visual_asset)}")`);
  }

  function showInlineError(container, message) {
    if (!container) return;
    if (container.tagName === "TBODY") {
      container.innerHTML = `<tr><td class="empty-row" colspan="7" role="status">${escapeHtml(message)}</td></tr>`;
      return;
    }
    container.innerHTML = `<p class="notice error" role="status">${escapeHtml(message)}</p>`;
  }

  function setActiveNavigation() {
    const page = document.body.dataset.page;
    document.querySelectorAll("[data-nav]").forEach((link) => {
      if (link.dataset.nav === page) {
        link.classList.add("active");
        link.setAttribute("aria-current", "page");
      }
    });
  }

  function renderSharedGithubFooter() {
    const buttons = publicGithubChannels
      .map((channel) => externalLink(channel.url, channel.label, "btn compact"))
      .join("");
    document.querySelectorAll(".footer-grid").forEach((footer) => {
      if (footer.querySelector("[data-github-footer]")) return;
      footer.insertAdjacentHTML("beforeend", `
        <div class="footer-github" data-github-footer>
          <div class="footer-ant-lockup"><img src="${escapeHtml(siteUrl("assets/aureon-lux/ants/knowledge-ant-v2-transparent-style.webp"))}" alt="" width="64" height="64" loading="lazy" decoding="async"><strong>Public GitHub Channels</strong></div>
          <div class="github-channel-actions">${buttons}</div>
        </div>`);
    });
  }

  async function initialize() {
    setActiveNavigation();
    renderSharedGithubFooter();
    let projects;
    try {
      projects = await loadJson("data/projects.json");
      document.querySelectorAll("[data-project-table]").forEach((tableBody) => setupProjectTable(projects, tableBody));
      renderStats(projects);
      await renderEcosystem(projects);
      const slug = document.body.dataset.projectSlug;
      if (slug) {
        const project = projects.find((item) => item.slug === slug);
        if (project) renderProjectDetail(project, projects);
        else showInlineError(document.querySelector("[data-project-detail]"), "This project profile is not present in the public registry.");
      }
    } catch (_error) {
      document.querySelectorAll("[data-project-table], [data-project-detail], [data-project-stats], [data-project-graph]").forEach((container) => {
        showInlineError(container, "The project registry could not be loaded. Please retry from a local web server.");
      });
    }

    if (document.querySelector("[data-publications], [data-publications-preview]")) {
      try {
        renderPublications(await loadJson("data/publications.json"));
      } catch (_error) {
        document.querySelectorAll("[data-publications], [data-publications-preview]").forEach((container) => showInlineError(container, "Public records are temporarily unavailable."));
      }
    }

    if (document.querySelector("[data-research], [data-research-profiles]")) {
      try {
        renderResearch(await loadJson("data/research.json"));
      } catch (_error) {
        document.querySelectorAll("[data-research], [data-research-profiles]").forEach((container) => showInlineError(container, "The research index is temporarily unavailable."));
      }
    }

    if (document.querySelector("[data-updates]")) {
      try {
        renderUpdates(await loadJson("data/updates.json"));
      } catch (_error) {
        document.querySelectorAll("[data-updates]").forEach((container) => showInlineError(container, "Project updates are temporarily unavailable."));
      }
    }
  }

  initialize();
})();
