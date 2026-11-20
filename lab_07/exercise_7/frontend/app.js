/* =========================================================
   SENTINEL CTI PLATFORM
   Frontend Application
   ========================================================= */


/* =========================================================
   CONFIGURATION
   ========================================================= */

const API_BASE = "http://127.0.0.1:5000/api";


/* =========================================================
   INITIALIZE APPLICATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    loadDashboard();

    loadRecentThreats();

});


/* =========================================================
   NAVIGATION
   ========================================================= */

function showSection(sectionId) {

    const sections =
        document.querySelectorAll(".page-section");

    sections.forEach(section => {

        section.classList.remove(
            "active-section"
        );

    });


    const selected =
        document.getElementById(sectionId);

    if (selected) {

        selected.classList.add(
            "active-section"
        );

    }


    /* ---------------------------------------------
       Update sidebar active state
       --------------------------------------------- */

    const navItems =
        document.querySelectorAll(".nav-item");

    navItems.forEach(item => {

        item.classList.remove("active");

    });


    navItems.forEach(item => {

        const onclick =
            item.getAttribute("onclick");

        if (
            onclick &&
            onclick.includes(
                `'${sectionId}'`
            )
        ) {

            item.classList.add("active");

        }

    });


    /* ---------------------------------------------
       Change page title
       --------------------------------------------- */

    const titles = {

        dashboard:
            "Threat Intelligence Dashboard",

        threats:
            "Threat Intelligence",

        search:
            "Threat Search",

        classification:
            "Threat Classification"

    };


    const title =
        document.getElementById("pageTitle");


    if (title && titles[sectionId]) {

        title.textContent =
            titles[sectionId];

    }


    /* ---------------------------------------------
       Load section-specific information
       --------------------------------------------- */

    if (sectionId === "threats") {

        loadAllThreats();

    }


    if (sectionId === "classification") {

        loadDashboard();

    }

}


/* =========================================================
   DASHBOARD
   ========================================================= */

async function loadDashboard() {

    try {

        const response =
            await fetch(
                `${API_BASE}/analytics/dashboard`
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load dashboard"
            );

        }


        const data =
            await response.json();


        /* -----------------------------------------
           Statistics
           ----------------------------------------- */

        setText(
            "totalThreats",
            data.totalThreats
        );


        setText(
            "criticalThreats",
            data.criticalThreats
        );


        setText(
            "totalIndicators",
            data.totalIndicators
        );


        setText(
            "totalSources",
            data.totalSources
        );


        /* -----------------------------------------
           Classification counts
           ----------------------------------------- */

        setText(
            "ransomwareCount",
            data.categories?.ransomware ?? 0
        );


        setText(
            "malwareCount",
            data.categories?.malware ?? 0
        );


        setText(
            "phishingCount",
            data.categories?.phishing ?? 0
        );


    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

        setText(
            "totalThreats",
            "!"
        );

        setText(
            "criticalThreats",
            "!"
        );

        setText(
            "totalIndicators",
            "!"
        );

        setText(
            "totalSources",
            "!"
        );

    }

}


/* =========================================================
   RECENT THREATS
   ========================================================= */

async function loadRecentThreats() {

    const container =
        document.getElementById(
            "recentThreats"
        );


    if (!container) return;


    try {

        const response =
            await fetch(
                `${API_BASE}/threats/`
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load threats"
            );

        }


        const threats =
            await response.json();


        if (!Array.isArray(threats) ||
            threats.length === 0) {

            container.innerHTML = `
                <div class="empty-state">
                    No threat intelligence available.
                </div>
            `;

            return;

        }


        /* Show newest threats first */

        const recent =
            threats.slice(0, 6);


        container.innerHTML =
            recent.map(
                createThreatCard
            ).join("");


    } catch (error) {

        console.error(
            "Threat loading error:",
            error
        );


        container.innerHTML = `
            <div class="empty-state">
                Unable to load threat intelligence.
            </div>
        `;

    }

}


/* =========================================================
   ALL THREATS
   ========================================================= */

async function loadAllThreats() {

    const container =
        document.getElementById(
            "allThreats"
        );


    if (!container) return;


    container.innerHTML = `
        <div class="loading">
            Loading threat intelligence...
        </div>
    `;


    try {

        const response =
            await fetch(
                `${API_BASE}/threats/`
            );


        const threats =
            await response.json();


        if (!threats.length) {

            container.innerHTML = `
                <div class="empty-state">
                    No threats found.
                </div>
            `;

            return;

        }


        container.innerHTML =
            threats.map(
                createThreatCard
            ).join("");


    } catch (error) {

        console.error(error);


        container.innerHTML = `
            <div class="empty-state">
                Failed to load threats.
            </div>
        `;

    }

}


/* =========================================================
   CREATE THREAT CARD
   ========================================================= */

function createThreatCard(threat) {

    const severity =
        threat.severity ||
        "Unknown";


    const severityClass =
        severity.toLowerCase();


    const tags =
        Array.isArray(threat.tags)
            ? threat.tags
            : [];


    const tagHTML =
        tags.slice(0, 4).map(tag => {

            return `
                <span class="tag">
                    ${escapeHTML(tag)}
                </span>
            `;

        }).join("");


    const description =
        threat.description ||
        "No description available.";


    const source =
        threat.source?.name ||
        "Unknown source";


    const date =
        formatDate(
            threat.publishedDate
        );


    const id =
        threat._id ||
        threat.id ||
        "";


    return `

        <article
            class="threat-card"
            onclick="openThreat('${escapeAttribute(id)}')"
        >

            <div class="threat-top">

                <h3>
                    ${escapeHTML(
                        threat.title ||
                        "Unnamed Threat"
                    )}
                </h3>

                <span
                    class="severity ${severityClass}"
                >
                    ${escapeHTML(severity)}
                </span>

            </div>


            <p class="threat-description">

                ${escapeHTML(
                    truncate(
                        description,
                        130
                    )
                )}

            </p>


            <div class="tags">

                ${
                    tagHTML ||
                    `
                    <span class="tag">
                        ${escapeHTML(
                            threat.category ||
                            "Threat"
                        )}
                    </span>
                    `
                }

            </div>


            <div class="threat-footer">

                <span>
                    ${escapeHTML(source)}
                </span>

                <span>
                    ${escapeHTML(date)}
                </span>

            </div>

        </article>

    `;

}


/* =========================================================
   OPEN THREAT DETAILS
   ========================================================= */

async function openThreat(threatId) {

    if (!threatId) return;


    const modal =
        document.getElementById(
            "threatModal"
        );


    const content =
        document.getElementById(
            "modalContent"
        );


    modal.classList.add("show");


    content.innerHTML = `

        <div class="loading">
            Loading threat intelligence...
        </div>

    `;


    try {

        const response =
            await fetch(
                `${API_BASE}/threats/${encodeURIComponent(threatId)}`
            );


        if (!response.ok) {

            throw new Error(
                "Threat not found"
            );

        }


        const threat =
            await response.json();


        renderThreatDetails(
            threat
        );


    } catch (error) {

        console.error(error);


        content.innerHTML = `

            <div class="empty-state">

                Unable to load threat details.

            </div>

        `;

    }

}


/* =========================================================
   RENDER THREAT DETAILS
   ========================================================= */

function renderThreatDetails(threat) {

    const content =
        document.getElementById(
            "modalContent"
        );


    const severity =
        threat.severity ||
        "Unknown";


    const classification =
        threat.classification ||
        {};


    const confidence =
        Number(
            classification.confidence || 0
        );


    const indicatorIds =
        Array.isArray(
            threat.indicatorIds
        )
            ? threat.indicatorIds
            : [];


    const tags =
        Array.isArray(threat.tags)
            ? threat.tags
            : [];


    const tagHTML =
        tags.map(tag => {

            return `
                <span class="tag">
                    ${escapeHTML(tag)}
                </span>
            `;

        }).join("");


    const indicatorHTML =
        indicatorIds.length

            ? indicatorIds.map(id => {

                return `
                    <span class="tag">
                        ${escapeHTML(id)}
                    </span>
                `;

            }).join("")

            : `
                <span class="tag">
                    No indicators
                </span>
            `;


    content.innerHTML = `

        <span class="eyebrow">
            THREAT INVESTIGATION
        </span>


        <h2 class="modal-title">

            ${escapeHTML(
                threat.title ||
                "Unknown Threat"
            )}

        </h2>


        <span
            class="severity ${severity.toLowerCase()}"
        >
            ${escapeHTML(severity)}
        </span>


        <p class="modal-description">

            ${escapeHTML(
                threat.description ||
                "No description available."
            )}

        </p>


        <div class="detail-grid">


            <div class="detail-box">

                <label>
                    Category
                </label>

                <strong>
                    ${escapeHTML(
                        threat.category ||
                        "Unknown"
                    )}
                </strong>

            </div>


            <div class="detail-box">

                <label>
                    Classification
                </label>

                <strong>
                    ${escapeHTML(
                        classification.type ||
                        threat.category ||
                        "Unknown"
                    )}
                </strong>

            </div>


            <div class="detail-box">

                <label>
                    Source
                </label>

                <strong>
                    ${escapeHTML(
                        threat.source?.name ||
                        "Unknown"
                    )}
                </strong>

            </div>


            <div class="detail-box">

                <label>
                    Published
                </label>

                <strong>
                    ${escapeHTML(
                        formatDate(
                            threat.publishedDate
                        )
                    )}
                </strong>

            </div>


        </div>


        <div class="confidence">

            <label>
                Classification Confidence
            </label>

            <strong>
                ${Math.round(
                    confidence * 100
                )}%
            </strong>


            <div class="confidence-bar">

                <div
                    class="confidence-fill"
                    style="
                        width:${Math.min(
                            confidence * 100,
                            100
                        )}%
                    "
                ></div>

            </div>

        </div>


        <div class="tags">

            ${tagHTML}

        </div>


        <div class="detail-box"
             style="margin-top:20px">

            <label>
                Associated Indicators
            </label>

            <div class="tags">

                ${indicatorHTML}

            </div>

        </div>

    `;

}


/* =========================================================
   CLOSE MODAL
   ========================================================= */

function closeModal() {

    const modal =
        document.getElementById(
            "threatModal"
        );


    modal.classList.remove(
        "show"
    );

}


window.addEventListener(
    "click",
    event => {

        const modal =
            document.getElementById(
                "threatModal"
            );


        if (event.target === modal) {

            closeModal();

        }

    }
);


/* =========================================================
   SEARCH
   ========================================================= */

async function performSearch() {

    const input =
        document.getElementById(
            "globalSearch"
        );


    const query =
        input.value.trim();


    if (!query) {

        showSection("search");

        return;

    }


    /* Put the query into advanced search */

    const advanced =
        document.getElementById(
            "searchInput"
        );


    if (advanced) {

        advanced.value =
            query;

    }


    showSection("search");


    await performAdvancedSearch();

}


/* =========================================================
   ADVANCED SEARCH
   ========================================================= */

async function performAdvancedSearch() {

    const input =
        document.getElementById(
            "searchInput"
        );


    const container =
        document.getElementById(
            "searchResults"
        );


    const query =
        input.value.trim();


    if (!query) {

        container.innerHTML = `

            <div class="empty-state">

                Enter a search query to investigate
                threats.

            </div>

        `;

        return;

    }


    container.innerHTML = `

        <div class="loading">

            Searching threat intelligence...

        </div>

    `;


    try {

        const response =
            await fetch(
                `${API_BASE}/search/?q=${encodeURIComponent(query)}`
            );


        if (!response.ok) {

            throw new Error(
                "Search failed"
            );

        }


        const data =
            await response.json();


        if (
            !data.results ||
            data.results.length === 0
        ) {

            container.innerHTML = `

                <div class="empty-state">

                    No threats found for
                    "<strong>${escapeHTML(query)}</strong>".

                </div>

            `;

            return;

        }


        container.innerHTML = `

            <div class="result-count">

                ${data.count}
                threat(s) found for
                "<strong>${escapeHTML(query)}</strong>"

            </div>


            <div class="threat-grid">

                ${data.results
                    .map(createThreatCard)
                    .join("")
                }

            </div>

        `;


    } catch (error) {

        console.error(
            "Search error:",
            error
        );


        container.innerHTML = `

            <div class="empty-state">

                Search service unavailable.

            </div>

        `;

    }

}


/* =========================================================
   ENTER KEY — GLOBAL SEARCH
   ========================================================= */

function searchOnEnter(event) {

    if (event.key === "Enter") {

        performSearch();

    }

}


/* =========================================================
   ENTER KEY — SEARCH PAGE
   ========================================================= */

function searchPageEnter(event) {

    if (event.key === "Enter") {

        performAdvancedSearch();

    }

}


/* =========================================================
   UTILITY FUNCTIONS
   ========================================================= */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (element) {

        element.textContent =
            value;

    }

}


/* ---------------------------------------------------------
   Date formatting
   --------------------------------------------------------- */

function formatDate(value) {

    if (!value) {

        return "Unknown date";

    }


    try {

        const date =
            new Date(value);


        if (isNaN(date.getTime())) {

            return String(value);

        }


        return date.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );

    } catch {

        return String(value);

    }

}


/* ---------------------------------------------------------
   Truncate long text
   --------------------------------------------------------- */

function truncate(
    text,
    maxLength
) {

    if (!text) return "";

    if (text.length <= maxLength) {

        return text;

    }


    return (
        text.substring(
            0,
            maxLength
        ) + "..."
    );

}


/* ---------------------------------------------------------
   HTML escaping
   --------------------------------------------------------- */

function escapeHTML(value) {

    if (value === null ||
        value === undefined) {

        return "";

    }


    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


/* ---------------------------------------------------------
   Attribute escaping
   --------------------------------------------------------- */

function escapeAttribute(value) {

    return String(value)
        .replaceAll("\\", "\\\\")
        .replaceAll("'", "\\'");

}


/* =========================================================
   LOG
   ========================================================= */

console.log(
    "%c SENTINEL CTI PLATFORM ",
    "background:#36d6a1;color:#06110d;font-weight:bold;padding:5px"
);

console.log(
    "Cyber Threat Intelligence Platform initialized."
);