# Website Change Monitoring — Approach Note

## 1. Objective

The solution monitors five corporate websites once per run and identifies new official publications and meaningful changes since the previous check.

The monitored companies are:

- Norsk Hydro
- Constellium
- Alcoa
- Ma'aden
- Rio Tinto

The solution focuses on useful corporate information such as news, press releases, investor updates, reports, presentations, financial information and other official publications.

## 2. Monitoring approach

The solution uses a configuration-driven Python scraper.

Each company is defined in one site configuration, including its company name, starting URL and monitoring rules. This makes it possible to add another company without redesigning the application.

The scraper retrieves the official website pages and follows relevant internal links to find publication and investor-related content. It does not depend only on RSS feeds or sitemaps because those sources may be missing, incomplete or stale.

The collected pages are cleaned and filtered so that normal website navigation is not treated as a business publication.

Examples of content intentionally ignored include:

- Navigation menus
- Generic section labels
- Cookie notices
- Search links
- "Learn more" links
- Generic investor/media navigation
- Routine website elements

The monitoring process keeps useful publication titles, source URLs, dates and available page text.

## 3. Change detection

The process stores monitoring results in a local SQLite database.

For each publication, the database records information including:

- Company
- Item type
- Title
- Source URL
- Website publication date
- First-found date and time
- Content hash
- Summary
- Status

A content hash is also stored for monitored content. During a later check, the new result is compared with the previously stored result.

The process can therefore distinguish between:

- A new publication
- An existing publication whose meaningful content changed
- An unchanged publication
- A failed check

The first time an item is found, its `first_found_at` value is recorded. If the website later changes the same publication, the item can be reported as updated without treating it as a completely new publication.

## 4. Duplicate handling

The same announcement can appear in more than one section of a corporate website.

The solution uses publication information and normalized source information to avoid treating the same business item as multiple independent updates.

This is important when an announcement appears in both a News section and an Investor Relations section, or when a publication moves to another URL.

## 5. Dates

Two dates are kept separately:

**Website date**

The date displayed by the company's website for the publication, when available.

**First found date**

The date and time when the monitoring process first detected the item.

This prevents the monitoring timestamp from being confused with the publication date supplied by the company.

## 6. Error handling

A failed website check is recorded separately from a successful check with no changes.

If a page cannot be retrieved or processed, the result is marked as an error and the dashboard displays that the check needs attention.

A failed check is therefore never reported as "No new updates."

The latest check status is also stored so that another user can see which companies were successfully checked.

## 7. Daily report

After each monitoring run, the solution produces a short report containing useful changes.

For each reported item, the report can include:

- Company
- Item type
- Title
- Source URL
- Website date
- First-found date and time
- Summary
- Change status
- Relevant uncertainty or error information

If no meaningful changes are detected, the report states that no changes were found and lists the companies that were successfully checked.

## 8. User interface

A local Flask dashboard provides a simple business-facing view of the results.

The dashboard displays:

- Number of companies monitored
- Number of successful checks
- Number of current updates
- Number of failed checks
- Individual company cards

Selecting a company displays its latest publications, update status, source links, website dates and first-found timestamps.

If a company has no new updates, the dashboard explicitly displays:

**"No new updates in the latest check."**

This allows a business user to review the monitoring results without needing to inspect the database or terminal output.

## 9. Why this approach was chosen

A Python-based local solution was chosen because it is simple to run, easy to maintain and does not require a paid monitoring service or company credentials.

SQLite provides lightweight persistent history without requiring a separate database server.

Flask provides a simple dashboard for reviewing results.

The main trade-off is that corporate websites differ significantly in structure. A generic scraper cannot guarantee that every dynamically generated or poorly exposed publication will always be found. Site-specific monitoring rules and filtering are therefore used where necessary.

The design favors a simple and explainable process over adding external monitoring services or unnecessary infrastructure.

## 10. Extending the solution

To monitor another company, the preferred approach is to add another site configuration containing its:

- Company name
- Starting URL
- Relevant monitoring sections or rules

The common scraper, database and dashboard logic can then process the new site using the same workflow.

This keeps daily operation simple and avoids redesigning the application whenever another website is added.